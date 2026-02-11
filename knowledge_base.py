import os
import re
from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class MedicalKnowledgeBase:
    """RAG knowledge base with medical sources"""
    
    def __init__(self, persist_dir: str = "./medical_kb"):
        self.persist_dir = persist_dir
        self.embeddings = None
        self.vectorstore = None
        self.documents = []
        self._fallback_mode = False

        # Prefer local-only HF model to avoid network dependency during demo.
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"local_files_only": True},
            )
        except Exception:
            self._fallback_mode = True
        self.vectorstore = None
        
    def load_medical_sources(self, sources: List[str]):
        """Load and index medical documents"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
        docs = [Document(page_content=src, metadata={"source": f"medical_ref_{i}"}) 
                for i, src in enumerate(sources)]
        chunks = splitter.split_documents(docs)
        self.documents = chunks

        if self.embeddings:
            self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
        
    def retrieve(self, query: str, k: int = 3) -> List[tuple]:
        """Retrieve relevant medical context with scores"""
        if not self.vectorstore:
            return self._fallback_retrieve(query, k)
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return [(doc.page_content, score, doc.metadata.get("source", "unknown")) 
                for doc, score in results]

    def _fallback_retrieve(self, query: str, k: int) -> List[tuple]:
        """Simple keyword-overlap retrieval when embeddings aren't available."""
        if not self.documents:
            return []

        q_terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        q_len = max(1, len(q_terms))

        scored = []
        for doc in self.documents:
            d_terms = set(re.findall(r"[a-z0-9]+", doc.page_content.lower()))
            overlap = len(q_terms & d_terms)
            score = 1.0 - (overlap / q_len)
            scored.append((doc.page_content, score, doc.metadata.get("source", "unknown")))

        scored.sort(key=lambda x: x[1])
        return scored[:k]
    
    def save(self):
        """Persist vector store"""
        if self.vectorstore:
            self.vectorstore.save_local(self.persist_dir)
    
    def load(self):
        """Load persisted vector store"""
        if os.path.exists(self.persist_dir):
            self.vectorstore = FAISS.load_local(
                self.persist_dir, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
