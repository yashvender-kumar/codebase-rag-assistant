# 🤖 AI GitHub Repository Assistant (`RepoChat AI`)

A full-stack **Retrieval-Augmented Generation (RAG)** developer assistant that ingests any public GitHub repository, indexes its source code using syntax-aware chunking, and lets you chat with the codebase through a sleek dark-mode web interface.

---

## ✨ Key Features

- **Universal Public Repo Ingestion:** Paste any public GitHub repository URL (`https://github.com/owner/repo`) to automatically fetch, parse, and index its source files.
- **Syntax-Aware Code Splitting:** Uses LangChain's language-specific splitters (`RecursiveCharacterTextSplitter.from_language`) so functions, classes, and code blocks remain intact.
- **Fast & Safe Indexing:** Built-in chunk capping (`MAX_CHUNKS = 300`) prevents timeouts on large multi-hundred-file repositories while maintaining high retrieval accuracy.
- **Dynamic Groq LLM Selection:** Automatically discovers and selects an active Groq model at runtime—eliminating hardcoded model deprecation errors.
- **Source-Cited Developer Chat:** Every answer includes exact file path citations, syntax-highlighted code blocks with one-click **Copy** buttons, and interactive file exploration in the sidebar.

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python, FastAPI, Uvicorn, Pydantic |
| **AI & RAG Pipeline** | LangChain, ChromaDB (Vector Store), HuggingFace (`BAAI/bge-small-en-v1.5`), Groq API |
| **Frontend** | HTML5, CSS3 (Custom Dark UI), Vanilla JavaScript, Marked.js, Highlight.js |

---

## 📂 Project Structure

```text
github-repo-assistant/
├── app/
│   ├── __init__.py
│   ├── config.py          # Environment variables & model settings
│   ├── github_loader.py   # GitHub repo URL parser & archive file extractor
│   ├── main.py            # FastAPI endpoints (/ingest, /ask) & static frontend mount
│   └── rag_engine.py      # Syntax-aware chunking, ChromaDB indexing & Groq QA chain
├── frontend/
│   ├── index.html         # Main dark-mode developer chat UI
│   ├── style.css          # Responsive layout, cards & syntax theme styling
│   └── script.js          # API integration, dynamic file sidebar & markdown rendering
├── .env                   # API keys (excluded from Git)
├── .gitignore             # Ignores venv, .env, chroma_db, and cache files
├── requirements.txt       # Python dependencies
└── README.md

🚀 Getting Started (Local Setup)
1. Clone the Repository

git clone (https://github.com/yashvender-kumar/repochat-ai.git)
cd repochat-ai

2. Create & Activate Virtual Environment

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

3. Install Dependencies

pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file in the root directory and add your Groq API key:

GROQ_API_KEY=your_groq_api_key_here

5. Run the Application
Start the FastAPI server (which serves both the API and the frontend UI):

uvicorn app.main:app

Open your browser and visit:
(http://127.0.0.1:8000)


💡 How to Use
 1. Index a Repository: Paste any public GitHub repository URL into the left sidebar input and click Index Repo.

2. Explore Indexed Files: View total files processed, chunks indexed, and click any file in the sidebar to auto-fill a targeted code explanation prompt.

3. Ask Technical Questions: Use the Suggested Questions or type your own queries (e.g., "How does the authentication flow work?", "Explain the main entry point") to get context-grounded answers with file references.

-------⏱️ Performance Note: Small to medium repositories index within 2–5 seconds. If you index a very large repository with hundreds of files, downloading and generating local embeddings may take a little longer—please wait until the indexing loader finishes.-------------

👨‍💻 Author
Yashvender Kumar

GitHub: @yashvender-kumar