"""RAG Service — treatment knowledge base for the autism clinic chatbot.

Ports the PersonalRAG pipeline into Sentiri with one key change:
  - Embedding model: paraphrase-multilingual-MiniLM-L12-v2 (handles Malay)
  - Reranker: cross-encoder/ms-marco-MiniLM-L-6-v2 (same as PersonalRAG)
  - LLM: Groq llama-3.3-70b-versatile (same as PersonalRAG)
  - Vector store: ChromaDB PersistentClient (same as PersonalRAG)

Two main entry points:
  1. ingest_document(file_path, doc_title)  — called by Celery task on upload
  2. query(question)                        — called by chatbot view
"""

import os
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import chromadb
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer, CrossEncoder
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

# ── CONFIG ──
BASE_DIR = Path(__file__).resolve().parent.parent.parent
VECTOR_STORE_DIR = str(BASE_DIR / "data" / "vector_store")
COLLECTION_NAME = "treatment_documents"

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
LLM_MODEL = "openai/gpt-oss-120b"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 5
RETRIEVE_K = 20
SCORE_THRESHOLD = 0.2

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


# ╔════════════════════════════════════════════╗
# ║          SINGLETONS (load once)             ║
# ╚════════════════════════════════════════════╝

_embedding_model: Optional[SentenceTransformer] = None
_reranker: Optional[CrossEncoder] = None
_chroma_client: Optional[chromadb.PersistentClient] = None
_collection: Optional[chromadb.Collection] = None


def get_embedding_model() -> SentenceTransformer:
    """Lazy-load the multilingual embedding model (singleton)."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"Embedding model loaded. Dim: {_embedding_model.get_sentence_embedding_dimension()}")
    return _embedding_model


def get_reranker() -> CrossEncoder:
    """Lazy-load the cross-encoder reranker (singleton)."""
    global _reranker
    if _reranker is None:
        logger.info(f"Loading reranker: {RERANKER_MODEL}")
        _reranker = CrossEncoder(RERANKER_MODEL)
        logger.info("Reranker loaded")
    return _reranker


def get_collection() -> chromadb.Collection:
    """Get or create the ChromaDB collection (singleton)."""
    global _chroma_client, _collection
    if _collection is None:
        os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB collection ready: {COLLECTION_NAME} at {VECTOR_STORE_DIR}")
    return _collection


# ╔════════════════════════════════════════════╗
# ║         DOCUMENT INGESTION                  ║
# ╚════════════════════════════════════════════╝

def load_and_chunk(file_path: str) -> List[Dict[str, Any]]:
    """Load a PDF or text file and split into chunks.

    Returns list of {content, metadata} dicts.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    # Choose loader based on file type
    if path.suffix.lower() == ".pdf":
        loader = PyMuPDFLoader(str(path))
    elif path.suffix.lower() in (".txt", ".md"):
        loader = TextLoader(str(path))
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    documents = loader.load()
    logger.info(f"Loaded {len(documents)} pages from {path.name}")

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"Split into {len(chunks)} chunks")

    # Convert to our format
    result = []
    for i, chunk in enumerate(chunks):
        result.append({
            "content": chunk.page_content,
            "metadata": {
                "source": path.name,
                "page": chunk.metadata.get("page", 0),
                "chunk_index": i,
            },
        })
    return result


def embed_and_store(chunks: List[Dict[str, Any]], doc_title: str) -> int:
    """Embed chunks and store in ChromaDB.

    Returns number of chunks stored.
    """
    if not chunks:
        return 0

    model = get_embedding_model()
    collection = get_collection()

    # Generate embeddings
    texts = [c["content"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=False)

    # Generate unique IDs
    doc_hash = hashlib.md5(doc_title.encode()).hexdigest()[:8]
    ids = [f"{doc_hash}_{i}" for i in range(len(chunks))]

    # Add to ChromaDB
    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=[
            {**c["metadata"], "doc_title": doc_title}
            for c in chunks
        ],
    )
    logger.info(f"Stored {len(chunks)} chunks in ChromaDB for '{doc_title}'")
    return len(chunks)


def ingest_document(file_path: str, doc_title: str) -> Dict[str, Any]:
    """Full ingestion pipeline: load → chunk → embed → store.

    Called by the Celery task when a doctor uploads a document.
    """
    try:
        chunks = load_and_chunk(file_path)
        count = embed_and_store(chunks, doc_title)
        return {
            "status": "ready",
            "chunks_created": count,
            "error": None,
        }
    except Exception as e:
        logger.error(f"Ingestion failed for '{doc_title}': {e}")
        return {
            "status": "failed",
            "chunks_created": 0,
            "error": str(e),
        }


# ╔════════════════════════════════════════════╗
# ║          RETRIEVAL + GENERATION             ║
# ╚════════════════════════════════════════════╝

def retrieve(query: str, top_k: int = RETRIEVE_K) -> List[Dict[str, Any]]:
    """Embed the query and search ChromaDB for relevant chunks."""
    model = get_embedding_model()
    collection = get_collection()

    # Embed the question
    query_embedding = model.encode([query], show_progress_bar=False)[0]

    # Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k,
    )

    if not results.get("documents") or not results["documents"][0]:
        return []

    retrieved_docs = []
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    ids = results["ids"][0]

    for doc_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        # Cosine distance → similarity (0 = identical, 2 = opposite)
        similarity = (2 - distance) / 2

        if similarity < SCORE_THRESHOLD:
            continue

        retrieved_docs.append({
            "id": doc_id,
            "content": document,
            "metadata": metadata,
            "similarity_score": similarity,
            "distance": distance,
        })

    logger.info(f"Retrieved {len(retrieved_docs)} chunks (threshold={SCORE_THRESHOLD})")
    return retrieved_docs


def rerank(query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rerank retrieved documents using cross-encoder for precision."""
    if not documents:
        return []

    reranker = get_reranker()

    # Create query-document pairs
    pairs = [(query, doc["content"]) for doc in documents]
    scores = reranker.predict(pairs)

    # Attach rerank scores
    for doc, score in zip(documents, scores):
        doc["rerank_score"] = float(score)

    # Sort by rerank score, keep top K
    reranked = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
    result = reranked[:TOP_K]

    logger.info(f"Reranked to top {len(result)} chunks")
    return result


def build_context(results: List[Dict[str, Any]]) -> str:
    """Build the context string for the LLM from retrieved chunks."""
    parts = []
    for i, doc in enumerate(results, 1):
        title = doc["metadata"].get("doc_title", "unknown")
        page = doc["metadata"].get("page", "N/A")
        score = doc.get("rerank_score", doc.get("similarity_score", 0))

        header = f"[Document {i} - {title}"
        if page != "N/A":
            header += f", page {page}"
        header += f" (relevance: {score:.2%})]"
        parts.append(f"{header}\n{doc['content']}\n")

    return "\n".join(parts)


def build_sources(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build sources list for the frontend (title, page, score, preview)."""
    sources = []
    for doc in results:
        score = doc.get("rerank_score", doc.get("similarity_score", 0))
        sources.append({
            "title": doc["metadata"].get("doc_title", "unknown"),
            "page": doc["metadata"].get("page", "N/A"),
            "score": round(float(score), 3),
            "preview": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
        })
    return sources


def calculate_confidence(results: List[Dict[str, Any]]) -> float:
    """Calculate overall confidence from retrieval/rerank scores."""
    if not results:
        return 0.0
    scores = [doc.get("rerank_score", doc.get("similarity_score", 0)) for doc in results]
    import math
    # Sigmoid normalize the max rerank score
    max_score = max(scores)
    normalized = 1 / (1 + math.exp(-max_score))
    return min(normalized, 1.0)


# ╔════════════════════════════════════════════╗
# ║                LLM GENERATION               ║
# ╚════════════════════════════════════════════╝

def get_llm() -> ChatGroq:
    """Create a Groq LLM instance."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in environment")
    return ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name=LLM_MODEL,
        temperature=0.1,
        max_tokens=1024,
    )


SYSTEM_PROMPT = """Anda adalah pembantu AI untuk pusat terapi autism.
Jawab soalan berdasarkan MAKLUMAT yang diberikan dalam konteks sahaja.
Jika konteks tidak mengandungi jawapan, katakan "Saya tidak mempunyai maklumat yang cukup untuk menjawab soalan ini."
Jawab dalam Bahasa Malaysia jika soalan dalam Bahasa Malaysia, dan dalam Bahasa Inggeris jika soalan dalam Bahasa Inggeris.
Sentiasa rujuk sumber dokumen dalam jawapan anda."""


def generate_answer(query: str, context: str) -> str:
    """Generate an answer using the LLM with retrieved context."""
    llm = get_llm()

    prompt = f"""{SYSTEM_PROMPT}

Konteks:
{context}

Soalan: {query}

Jawapan:"""

    response = llm.invoke(prompt)
    return response.content


# ╔════════════════════════════════════════════╗
# ║             FULL RAG PIPELINE               ║
# ╚════════════════════════════════════════════╝

@dataclass
class RAGResponse:
    """Structured response from the RAG pipeline."""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    context: Optional[str] = None


def query(question: str, return_context: bool = False) -> RAGResponse:
    """Full RAG pipeline: retrieve → rerank → build context → generate.

    This is the entry point called by the chatbot view.
    """
    logger.info(f"RAG query: {question}")

    # Step 1: Retrieve
    results = retrieve(question, top_k=RETRIEVE_K)

    if not results:
        logger.warning("No relevant documents found")
        return RAGResponse(
            answer="Saya tidak mempunyai maklumat yang cukup untuk menjawab soalan ini. Sila pastikan dokumen rawatan telah dimuat naik.",
            sources=[],
            confidence=0.0,
            context="" if return_context else None,
        )

    # Step 2: Rerank
    results = rerank(question, results)

    # Step 3: Build context + sources
    context = build_context(results)
    sources = build_sources(results)
    confidence = calculate_confidence(results)

    # Step 4: Generate
    answer = generate_answer(question, context)

    logger.info(f"Answer generated (confidence: {confidence:.2%})")

    return RAGResponse(
        answer=answer,
        sources=sources,
        confidence=confidence,
        context=context if return_context else None,
    )


# ╔════════════════════════════════════════════╗
# ║            UTILITY FUNCTIONS                ║
# ╚════════════════════════════════════════════╝

def get_collection_stats() -> Dict[str, Any]:
    """Get stats about the vector store for the dashboard."""
    try:
        collection = get_collection()
        count = collection.count()
        return {"total_chunks": count, "status": "ready" if count > 0 else "empty"}
    except Exception as e:
        return {"total_chunks": 0, "status": "error", "error": str(e)}


def delete_document_chunks(doc_title: str) -> int:
    """Delete all chunks belonging to a document from ChromaDB."""
    collection = get_collection()
    results = collection.get(where={"doc_title": doc_title})
    ids = results.get("ids", [])
    if ids:
        collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} chunks for '{doc_title}'")
    return len(ids)
