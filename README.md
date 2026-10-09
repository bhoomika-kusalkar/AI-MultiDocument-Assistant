\# 🤖 AI PDF MultiDocument Assistant



An AI-powered PDF question-answering chatbot built with \*\*FastAPI\*\*, \*\*Streamlit\*\*, and the \*\*OpenAI API\*\*.



The application allows users to upload a PDF and ask questions about its contents. It extracts the text, divides it into smaller chunks, creates embeddings, retrieves the most relevant sections for a question, and uses an OpenAI model to generate an answer.



\## ✨ Features



\- 📄 Upload PDF documents

\- 🔍 Extract text from PDFs

\- ✂️ Split PDF text into smaller chunks

\- 🧠 Generate text embeddings using OpenAI

\- 🔎 Find relevant PDF sections using similarity search

\- 💬 Ask questions about the uploaded PDF

\- 📚 Display source page numbers

\- ⚡ FastAPI backend

\- 🎨 Streamlit frontend

\- 🔐 Environment variables for API key configuration



\## 🧠 How It Works



The application follows a simple Retrieval-Augmented Generation (RAG) workflow:



```text

PDF Upload

&#x20;   ↓

Text Extraction

&#x20;   ↓

Text Chunking

&#x20;   ↓

OpenAI Embeddings

&#x20;   ↓

User Question

&#x20;   ↓

Question Embedding

&#x20;   ↓

Similarity Search

&#x20;   ↓

Top Relevant PDF Sections

&#x20;   ↓

OpenAI Response

&#x20;   ↓

Answer + Source Pages

