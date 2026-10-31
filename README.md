AI PDF Multi-Document Assistant

An AI-powered application that lets users upload multiple PDF documents and ask questions across their contents. It uses FastAPI, Streamlit, PyMuPDF, OpenAI embeddings, and cosine similarity to retrieve relevant passages and generate answers with source references.

Features
- Upload one or more PDF files at the same time.
- Extract text page by page and retain document names and page numbers.
- Split extracted text into chunks of up to 1,000 characters.
- Generate embeddings with OpenAI text-embedding-3-small.
- Rank chunks using NumPy cosine similarity.
- Retrieve the five highest-scoring chunks across uploaded documents.
- Generate answers using the OpenAI Responses API.
- Display source document names and page numbers.
- View uploaded documents and clear the current session's documents.
  
Tech Stack
Component	Technology
Language	Python
Backend	FastAPI
Frontend	Streamlit
PDF extraction	PyMuPDF (fitz)
Embeddings	OpenAI text-embedding-3-small
Similarity search	NumPy cosine similarity
Answer generation	OpenAI Responses API
HTTP requests	Requests


How It Works
1. Select one or more PDFs in the Streamlit interface.
2. The frontend sends them to the FastAPI /upload endpoint.
3. The backend extracts text page by page and splits it into chunks.
4. An embedding is generated for each chunk.
5. When a question is submitted, the backend generates a question embedding.
6. Cosine similarity ranks the stored chunks against the question.
7. The five highest-scoring chunks are sent as context to the OpenAI model.
8. The answer is returned with source document names and page numbers.
   
Project Structure
AI-PDF-MultiDocument-Assistant/
├── backend/
│   ├── main.py
│   └── pdf_utils.py
├── frontend/
│   └── app.py
├── .gitignore
├── requirements.txt
└── README.md
The application entry points are backend/main.py and frontend/app.py.
Prerequisites
- Python 3.10 or later
- An OpenAI API key
- Internet access for OpenAI API requests
  
Installation
1. Clone the repository
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_REPOSITORY_FOLDER>
Replace the placeholders with your repository URL and folder name.
2. Create and activate a virtual environment
Windows:
python -m venv venv
venv\\Scripts\\activate
macOS / Linux:
python3 -m venv venv
source venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
4. Configure your OpenAI API key
Create a .env file in the project root (the same directory as requirements.txt):
OPENAI_API_KEY=your_openai_api_key
Keep .env private and ensure it is listed in .gitignore. Never commit your API key.
Run the Application
Open two terminals in the project root and activate the virtual environment in both.

Terminal 1 — FastAPI backend:
uvicorn backend.main:app --reload
Backend address: http://127.0.0.1:8000

Interactive API documentation: http://127.0.0.1:8000/docs

Terminal 2 — Streamlit frontend:
streamlit run frontend/app.py
Open the local address printed by Streamlit in your browser.
API Endpoints
Method	Endpoint	Description
GET	/	Backend status and current document/chunk counts.
GET	/test-ai	Tests the OpenAI model connection.
POST	/upload	Uploads and processes multiple PDF files.
GET	/documents	Lists uploaded documents and counts.
DELETE	/documents	Clears in-memory documents and chunks.
POST	/ask	Answers a question using retrieved document sections.


Example question request
Send a POST request to /ask with:
{
  "question": "What are the main points in the uploaded documents?"
}
The response includes the question, generated answer, and source entries containing document names, page numbers, and similarity scores.
Notes and Limitations
- Temporary storage: Documents, chunks, and embeddings are held in backend memory and are cleared when the backend process restarts.
- Scanned PDFs: The current implementation extracts selectable text. Image-only or scanned PDFs may not contain readable text and may fail processing.
- Local configuration: The Streamlit frontend currently calls http://127.0.0.1:8000; this setup is intended for local use.
- API costs: Uploading documents and asking questions make requests to the OpenAI API and may incur usage costs.
- Retrieval: The application selects the five chunks with the highest cosine-similarity scores. Results depend on the document content and question.
  
Security
- Store the API key in .env.
- Never commit API keys, passwords, or other secrets.
- If a key is exposed, revoke it and create a replacement.
  
Future Improvements
- Persist documents and embeddings between backend restarts.
- Add OCR support for scanned PDFs.
- Improve chunking and retrieval strategies.
- Add document filtering and richer source previews.
- Make the backend URL configurable for deployment.
- Add automated tests and deployment instructions.
- 
Author
Bhoomika Kusalkar

GitHub: bhoomika-kusalkar
