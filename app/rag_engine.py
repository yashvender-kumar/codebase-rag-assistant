import os
import re
import hashlib
import requests
from typing import List, Dict
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import app.config  # .env load karne ke liye


def get_active_groq_model() -> str:
    """Groq API se automatically best active text-chat model pick karta hai."""
    api_key = os.getenv("GROQ_API_KEY")
    resp = requests.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10
    )
    resp.raise_for_status()
    models = [m["id"] for m in resp.json().get("data", [])]

    # Audio, TTS, guard, embedding aur special-terms models ko exclude karein
    excluded = ("whisper", "guard", "tts", "playai", "embed", "orpheus", "vision", "compound")
    chat_models = [m for m in models if not any(x in m.lower() for x in excluded)]

    # Best Llama / chat models ko priority dein
    preferred = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "openai/gpt-oss-120b",
        "qwen/qwen3-32b"
    ]
    for p in preferred:
        if p in chat_models:
            print(f"[Groq] Selected active model: {p}")
            return p

    if not chat_models:
        raise ValueError(f"Koi active chat model nahi mila. Available: {models}")

    selected = chat_models[0]
    print(f"[Groq] Selected active model: {selected}")
    return selected


# Local Embedding model
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

# Groq LLM initialization (auto-picks valid active chat model)
llm = ChatGroq(
    model=get_active_groq_model(),
    temperature=0.2
)

CHROMA_DIR = "./chroma_db"
MAX_CHUNKS = 150  # Fast indexing ke liye optimal chunk limit

EXTENSION_TO_LANGUAGE = {
    ".py": Language.PYTHON,
    ".js": Language.JS,
    ".ts": Language.TS,
    ".tsx": Language.TS,
    ".jsx": Language.JS,
    ".java": Language.JAVA,
    ".cpp": Language.CPP,
    ".c": Language.C,
    ".go": Language.GO,
    ".rs": Language.RUST,
    ".html": Language.HTML,
    ".md": Language.MARKDOWN,
}


def get_collection_name(repo_url: str) -> str:
    """ChromaDB ke rules ke hisaab se valid collection name banata hai (starts & ends with alphanumeric)."""
    clean_url = repo_url.strip().rstrip("/").lower()
    url_hash = hashlib.md5(clean_url.encode()).hexdigest()[:12]
    slug = re.sub(r"[^a-zA-Z0-9]", "", clean_url.split("github.com/")[-1])[:30]
    return f"repo_{slug}_{url_hash}"


def split_code_documents(files: List[Dict[str, str]]) -> List[Document]:
    """Programming language ke syntax ke hisaab se fast code chunks banata hai."""
    all_chunks = []

    for file in files[:80]:  # Top 80 files tak hi process karein
        if len(all_chunks) >= MAX_CHUNKS:
            break

        path = file["path"]
        content = file["content"]

        ext = "." + path.split(".")[-1] if "." in path else ""
        lang = EXTENSION_TO_LANGUAGE.get(ext)

        if lang:
            splitter = RecursiveCharacterTextSplitter.from_language(
                language=lang,
                chunk_size=1800,
                chunk_overlap=150
            )
        else:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1800,
                chunk_overlap=150
            )

        chunk = splitter.create_documents(
            texts=[content],
            metadatas=[{"source": path}]
        )
        all_chunks.extend(chunk)

    return all_chunks[:MAX_CHUNKS]


def index_repository(repo_url: str, files: List[Dict[str, str]]) -> int:
    """Code chunks ko ChromaDB mein store karta hai aur total chunks return karta hai."""
    print(f"[1/3] Splitting {len(files)} files into code chunks...")
    collection_name = get_collection_name(repo_url)
    chunks = split_code_documents(files)

    if not chunks:
        raise ValueError("Repository mein koi readable code file nahi mili.")

    print(f"[2/3] Created {len(chunks)} chunks. Saving to ChromaDB ({collection_name})...")

    try:
        existing_store = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=CHROMA_DIR
        )
        existing_store.delete_collection()
    except Exception:
        pass

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=CHROMA_DIR
    )
    print("[3/3] Indexing completed successfully!")
    return len(chunks)


def ask_repository(repo_url: str, question: str) -> Dict:
    """Vector Database se relevant code dhoondh kar Groq LLM se answer banwata hai."""
    collection_name = get_collection_name(repo_url)

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    retriever_docs = retriever.invoke(question)

    if not retriever_docs:
        return {
            "answer": "Is repository ke liye koi indexed code nahi mila. Pehle /ingest run karein.",
            "sources": []
        }

    context_parts = []
    sources = set()
    for doc in retriever_docs:
        file_path = doc.metadata.get("source", "unknown")
        sources.add(file_path)
        context_parts.append(f"--- File: {file_path} ---\n{doc.page_content}")

    formatted_context = "\n\n".join(context_parts)

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a senior software engineer helping a developer understand a GitHub repository. "
            "Answer the question strictly based on the provided code context. "
            "Always mention the exact file paths where functions, classes, or logic are defined. "
            "If the answer is not in the context, clearly say you cannot find it in the indexed codebase."
        )),
        ("human", "Codebase Context:\n{context}\n\nDeveloper Question: {question}")
    ])

    chain = prompt | llm
    response = chain.invoke({
        "context": formatted_context,
        "question": question
    })

    return {
        "answer": response.content,
        "sources": list(sources)
    }