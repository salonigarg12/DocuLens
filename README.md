# 🔍 DocuLens

DocuLens is an AI-powered PDF Question Answering application that allows users to upload PDF documents, generate summaries, and ask questions based on the document content. The application uses semantic search with FAISS and Sentence Transformers to retrieve relevant information and Gemini AI to generate accurate responses.

---

## ✨ Features

- 📄 Upload PDF documents
- 🤖 Ask questions about uploaded PDFs
- 📝 Generate concise PDF summaries
- 🔍 Semantic search using FAISS
- 🧠 Sentence Transformer embeddings
- ⚡ FastAPI backend
- 🎨 Streamlit frontend
- 🔐 Environment variable support for API keys

---

## 🛠️ Tech Stack

### Frontend
- Streamlit

### Backend
- FastAPI
- Uvicorn

### AI & NLP
- Google Gemini API
- Sentence Transformers
- FAISS

### PDF Processing
- pdfplumber

### Other Libraries
- NumPy
- python-dotenv
- python-multipart

---

## 📁 Project Structure

```
DocuLens/
│
├── requirements.txt
├── README.md
├── .gitignore
│
└── DocuLens/
    ├── app/
    │   ├── main.py
    │   ├── frontend.py
    │   ├── .env.example
    │   └── .env (Do NOT commit this file)
    │
    ├── data/
    └── storage/
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/DocuLens.git
cd DocuLens
```

---

### 2. Create a virtual environment

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Create a `.env` file inside:

```
DocuLens/app/
```

Add your Google Gemini API key:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

---

## ▶️ Running the Project

### Start the FastAPI Backend

```bash
uvicorn DocuLens.app.main:app --reload
```

The backend will run at:

```
http://127.0.0.1:8000
```

---

### Start the Streamlit Frontend

Open a **new terminal**, activate the virtual environment again, and run:

```bash
streamlit run DocuLens/app/frontend.py
```

The frontend will open automatically in your browser.

---

## 📖 How to Use

1. Launch both the backend and frontend.
2. Upload a PDF document.
3. Wait for the document to be indexed.
4. Click **Summarize PDF** to generate a summary.
5. Ask questions related to the uploaded document.
6. The application retrieves relevant content using FAISS and generates responses using Gemini AI.

---

## 🔧 Environment Variables

| Variable | Description |
|----------|-------------|
| GOOGLE_API_KEY | Google Gemini API Key |

---

## 📌 Future Improvements

- User Authentication
- Chat History Storage
- Multiple PDF Support
- Persistent Vector Database
- Docker Support
- Cloud Deployment
- Citation-based Answers

---

## 📄 License

This project is created for educational and learning purposes.
