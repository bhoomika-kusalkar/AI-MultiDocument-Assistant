from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

import os
import fitz
import numpy as np


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError(
        "OPENAI_API_KEY was not found in the .env file."
    )

client = OpenAI(api_key=api_key)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Multi-Document AI Chatbot"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# MULTI-DOCUMENT STORAGE
# =========================================================

documents = []

chunks = []


# =========================================================
# QUESTION MODEL
# =========================================================

class Question(BaseModel):
    question: str


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "Multi-Document AI PDF Chatbot is running",
        "documents": len(documents),
        "chunks": len(chunks)
    }


# =========================================================
# TEST AI
# =========================================================

@app.get("/test-ai")
def test_ai():

    try:

        response = client.responses.create(
            model="gpt-5.6",
            input=(
                "Say hello and confirm that "
                "the AI connection is working."
            )
        )

        return {
            "answer": response.output_text
        }

    except Exception as e:

        print("AI ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# UPLOAD MULTIPLE DOCUMENTS
# =========================================================

@app.post("/upload")
async def upload_documents(
    files: list[UploadFile] = File(...)
):

    if not files:

        raise HTTPException(
            status_code=400,
            detail="No files were uploaded."
        )

    uploaded_documents = []

    for file in files:

        try:

            # -------------------------------------------------
            # Read PDF
            # -------------------------------------------------

            contents = await file.read()

            pdf = fitz.open(
                stream=contents,
                filetype="pdf"
            )

            document_chunks = []

            # -------------------------------------------------
            # Extract text page by page
            # -------------------------------------------------

            for page_number, page in enumerate(
                pdf,
                start=1
            ):

                page_text = page.get_text()

                if not page_text.strip():
                    continue

                chunk_size = 1000

                page_chunks = [
                    page_text[i:i + chunk_size]
                    for i in range(
                        0,
                        len(page_text),
                        chunk_size
                    )
                ]

                for chunk_text in page_chunks:

                    if not chunk_text.strip():
                        continue

                    document_chunks.append({
                        "document": file.filename,
                        "page": page_number,
                        "text": chunk_text
                    })

            # -------------------------------------------------
            # Check text
            # -------------------------------------------------

            if not document_chunks:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"No readable text found "
                        f"in {file.filename}. "
                        "The PDF may be scanned/image-based."
                    )
                )

            # -------------------------------------------------
            # Create embeddings
            # -------------------------------------------------

            for item in document_chunks:

                response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=item["text"]
                )

                item["embedding"] = (
                    response.data[0].embedding
                )

            # -------------------------------------------------
            # Add document to global storage
            # -------------------------------------------------

            chunks.extend(document_chunks)

            documents.append({
                "filename": file.filename,
                "pages": len(pdf),
                "chunks": len(document_chunks)
            })

            uploaded_documents.append({
                "filename": file.filename,
                "pages": len(pdf),
                "chunks": len(document_chunks)
            })

        except HTTPException:
            raise

        except Exception as e:

            print(
                f"UPLOAD ERROR ({file.filename}):",
                repr(e)
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Error processing "
                    f"{file.filename}: {str(e)}"
                )
            )

    return {
        "message": "Documents uploaded successfully.",
        "uploaded": uploaded_documents,
        "total_documents": len(documents),
        "total_chunks": len(chunks)
    }


# =========================================================
# LIST DOCUMENTS
# =========================================================

@app.get("/documents")
def get_documents():

    return {
        "documents": documents,
        "total_documents": len(documents),
        "total_chunks": len(chunks)
    }


# =========================================================
# CLEAR ALL DOCUMENTS
# =========================================================

@app.delete("/documents")
def clear_documents():

    documents.clear()
    chunks.clear()

    return {
        "message": "All documents have been cleared."
    }


# =========================================================
# ASK QUESTION
# =========================================================

@app.post("/ask")
def ask_question(data: Question):

    try:

        # -------------------------------------------------
        # Check documents
        # -------------------------------------------------

        if not chunks:

            return {
                "answer": (
                    "Please upload at least one "
                    "PDF document first."
                ),
                "sources": []
            }

        # -------------------------------------------------
        # Create question embedding
        # -------------------------------------------------

        question_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=data.question
        )

        question_embedding = np.array(
            question_response.data[0].embedding
        )

        # -------------------------------------------------
        # Calculate similarities
        # -------------------------------------------------

        similarities = []

        for index, item in enumerate(chunks):

            chunk_embedding = np.array(
                item["embedding"]
            )

            denominator = (
                np.linalg.norm(question_embedding)
                * np.linalg.norm(chunk_embedding)
            )

            if denominator == 0:
                continue

            score = np.dot(
                question_embedding,
                chunk_embedding
            ) / denominator

            similarities.append({
                "index": index,
                "score": float(score)
            })

        # -------------------------------------------------
        # Sort
        # -------------------------------------------------

        similarities.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        # -------------------------------------------------
        # Top 5 chunks across ALL documents
        # -------------------------------------------------

        top_chunks = similarities[:5]

        # -------------------------------------------------
        # Build context
        # -------------------------------------------------

        relevant_text = "\n\n".join(
            (
                f"[Document: "
                f"{chunks[item['index']]['document']}]\n"
                f"[Page: "
                f"{chunks[item['index']]['page']}]\n"
                f"{chunks[item['index']]['text']}"
            )
            for item in top_chunks
        )

        # -------------------------------------------------
        # AI prompt
        # -------------------------------------------------

        prompt = f"""
You are an AI assistant that answers questions
using the uploaded PDF documents.

You have access to multiple documents.

Use ONLY the information contained in the
provided document sections.

If the answer cannot be found in the provided
sections, say:

"I couldn't find the answer in the uploaded documents."

When answering:

1. Use information from one or multiple documents
   when relevant.

2. Clearly distinguish information from different
   documents when necessary.

3. Mention the document name and page number
   whenever possible.

DOCUMENT SECTIONS:

{relevant_text}

QUESTION:

{data.question}
"""

        # -------------------------------------------------
        # Generate answer
        # -------------------------------------------------

        response = client.responses.create(
            model="gpt-5.6",
            input=prompt
        )

        # -------------------------------------------------
        # Sources
        # -------------------------------------------------

        sources = [
            {
                "document": chunks[item["index"]]["document"],
                "page": chunks[item["index"]]["page"],
                "similarity": round(
                    item["score"],
                    4
                )
            }
            for item in top_chunks
        ]

        return {
            "question": data.question,
            "answer": response.output_text,
            "sources": sources
        }

    except Exception as e:

        print("ASK ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )