dfrom fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import fitz
import numpy as np


# =========================
# Load environment variables
# =========================

load_dotenv("../.env")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# =========================
# FastAPI application
# =========================

app = FastAPI(title="AI Chatbot backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Temporary PDF storage
# =========================

pdf_text = ""
chunks = []
chunk_pages = []
chunk_embeddings = []


# =========================
# Question model
# =========================

class Question(BaseModel):
    question: str


# =========================
# Home
# =========================

@app.get("/")
def home():
    return {
        "message": "AI PDF Chatbot is running"
    }


# =========================
# Upload PDF
# =========================

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    global pdf_text
    global chunks
    global chunk_pages
    global chunk_embeddings

    # Read uploaded PDF
    contents = await file.read()

    # Open PDF
    pdf = fitz.open(
        stream=contents,
        filetype="pdf"
    )

    # Reset previous PDF data
    pdf_text = ""
    chunks = []
    chunk_pages = []
    chunk_embeddings = []

    # Size of each text chunk
    chunk_size = 1000

    # =========================
    # Extract text page by page
    # =========================

    for page_number, page in enumerate(pdf, start=1):

        page_text = page.get_text()

        pdf_text += page_text

        # Split page text into chunks
        page_chunks = [
            page_text[i:i + chunk_size]
            for i in range(0, len(page_text), chunk_size)
        ]

        # Store chunks and their page numbers
        for chunk in page_chunks:

            if chunk.strip():

                chunks.append(chunk)
                chunk_pages.append(page_number)

    # =========================
    # Create embeddings
    # =========================

    for chunk in chunks:

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=chunk
        )

        chunk_embeddings.append(
            response.data[0].embedding
        )

    return {
        "filename": file.filename,
        "pages": len(pdf),
        "chunks": len(chunks),
        "text": pdf_text[:1000]
    }


# =========================
# Get extracted text
# =========================

@app.get("/text")
def get_text():

    return {
        "text": pdf_text[:5000]
    }


# =========================
# Test AI connection
# =========================

@app.get("/test-ai")
def test_ai():

    response = client.responses.create(
        model="gpt-5.6",
        input="Say hello and tell me that the AI connection is working."
    )

    return {
        "answer": response.output_text
    }


# =========================
# Ask question
# =========================

@app.post("/ask")
def ask_question(data: Question):

    # Check whether a PDF has been uploaded
    if not chunks or not chunk_embeddings:

        return {
            "answer": "Please upload a PDF first."
        }

    # =========================
    # Create embedding for question
    # =========================

    question_response = client.embeddings.create(
        model="text-embedding-3-small",
        input=data.question
    )

    question_embedding = np.array(
        question_response.data[0].embedding
    )

    # =========================
    # Calculate similarity
    # =========================

    similarities = []

    for index, embedding in enumerate(chunk_embeddings):

        chunk_embedding = np.array(embedding)

        score = np.dot(
            question_embedding,
            chunk_embedding
        ) / (
            np.linalg.norm(question_embedding)
            * np.linalg.norm(chunk_embedding)
        )

        similarities.append({
            "index": index,
            "score": float(score)
        })

    # =========================
    # Sort by similarity
    # =========================

    similarities.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # Take the top 3 chunks
    top_chunks = similarities[:3]

    # =========================
    # Add page numbers
    # =========================

    relevant_text = "\n\n".join(
        f"[Page {chunk_pages[item['index']]}]\n"
        f"{chunks[item['index']]}"
        for item in top_chunks
    )

    # =========================
    # Ask AI
    # =========================

    prompt = f"""
You are an AI assistant that answers questions about a PDF.

Use ONLY the information provided in the PDF sections below.

If the answer is not contained in these sections, say:

"I couldn't find the answer in the uploaded PDF."

When possible, mention the page number where the information was found.

PDF SECTIONS:

{relevant_text}

QUESTION:

{data.question}
"""

    response = client.responses.create(
        model="gpt-5.6",
        input=prompt
    )

    # =========================
    # Return answer and sources
    # =========================

    return {
        "question": data.question,
        "answer": response.output_text,
        "sources": [
            {
                "page": chunk_pages[item["index"]],
                "similarity": round(item["score"], 4)
            }
            for item in top_chunks
        ]
    }