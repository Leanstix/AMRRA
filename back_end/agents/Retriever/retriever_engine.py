# retriever_engine.py
import logging
import os
import tempfile
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


class RetrieverEngine:
    def __init__(self, index_path: str = "retriever.index"):
        self.index_path = index_path
        self.embeddings = HuggingFaceEmbeddings(model_name="intfloat/e5-small-v2")
        self.index: Optional[FAISS] = None

        if os.path.exists(index_path):
            try:
                logging.info("[ENGINE] Loading existing FAISS index...")
                self.index = FAISS.load_local(
                    index_path, self.embeddings, allow_dangerous_deserialization=True
                )
            except Exception as e:
                logging.error(f"[ENGINE] Failed to load index: {e}")
                self._build_empty_index()
        else:
            self._build_empty_index()

    def _build_empty_index(self):
        self.index = FAISS.from_texts(["init"], self.embeddings)
        self.index.delete([0])
        self.index.save_local(self.index_path)

    def ingest_pdfs(
        self,
        file_bytes: bytes = None,
        file_path: str = None,
        doc_id: str = None,
        chunk_size: int = 800,
        chunk_overlap: int = 50
    ) -> bool:
        try:
            if file_bytes:
                tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
                with os.fdopen(tmp_fd, "wb") as f:
                    f.write(file_bytes)
                loader = PyPDFLoader(tmp_path)
            else:
                loader = PyPDFLoader(file_path)

            docs = loader.load()
            if not docs:
                logging.warning(f"[PDF] No content found in {file_path or 'upload'}")
                return False

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            chunks = splitter.split_documents(docs)

            for idx, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "doc_id": doc_id,
                    "chunk_id": f"{doc_id}::{idx}",
                    "source_path": file_path or "upload",
                    "source_path_type": "pdf"   # tagging source type
                })

            self.index.add_documents(chunks)
            self.index.save_local(self.index_path)
            logging.info(f"[DEBUG] First 3 chunk IDs for {doc_id}: {[c.metadata['chunk_id'] for c in chunks[:3]]}")
            logging.info(f"[DEBUG] FAISS total doc count: {len(self.index.docstore._dict)}")

            logging.info(f"[PDF] Ingested {len(chunks)} chunks for doc_id {doc_id}")

            if file_bytes:
                os.remove(tmp_path)

            return True

        except Exception as e:
            logging.error(f"[ERROR] Failed to ingest PDF {file_path or 'upload'}: {e}")
            return False

    def ingest_urls(
        self,
        url: str,
        doc_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 100
    ) -> bool:
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()
            if not docs:
                logging.warning(f"[URL] No content found at {url}")
                return False

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            chunks = splitter.split_documents(docs)

            for idx, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "doc_id": doc_id,
                    "chunk_id": f"{doc_id}::{idx}",
                    "source_path": url,
                    "source_path_type": "url"  # tagging source type
                })

            self.index.add_documents(chunks)
            self.index.save_local(self.index_path)
            logging.info(f"[URL] Ingested {len(chunks)} chunks from {url}")
            return True

        except Exception as e:
            logging.error(f"[ERROR] Failed to ingest URL {url}: {e}")
            return False

    def retrieve(
        self,
        query: str,
        doc_ids: Optional[List[str]] = None,
        top_k: int = 5,
        source_type: Optional[str] = None
    ):
        if not self.index:
            raise RuntimeError("FAISS index not initialized")

        logging.info(f"[RETRIEVE] Query='{query}' | top_k={top_k} | "
                     f"doc_ids={doc_ids} | source_type={source_type}")

        # Step 1: Overfetch candidates
        overfetch_k = top_k * 10
        docs_with_scores = self.index.similarity_search_with_score(query, k=overfetch_k)
        logging.info(f"[RETRIEVE] Initial candidates retrieved={len(docs_with_scores)}")

        # Debug dump: first few docs
        for i, (doc, score) in enumerate(docs_with_scores[:3]):
            logging.debug(f"[CANDIDATE {i}] doc_id={doc.metadata.get('doc_id')} "
                          f"source_type={doc.metadata.get('source_path_type')} "
                          f"score={score:.4f} | content={doc.page_content[:100]}...")
        
        # Step 2: Filter by doc_ids
        if doc_ids:
            before = len(docs_with_scores)
            docs_with_scores = [
                (doc, score) for doc, score in docs_with_scores
                if doc.metadata.get("doc_id") in doc_ids
            ]
            logging.info(f"[FILTER] doc_ids reduced {before} → {len(docs_with_scores)}")

        # Step 3: Filter by source_type
        if source_type:
            before = len(docs_with_scores)
            docs_with_scores = [
                (doc, score) for doc, score in docs_with_scores
                if doc.metadata.get("source_path_type") == source_type
            ]
            logging.info(f"[FILTER] source_type reduced {before} → {len(docs_with_scores)}")

        # Step 4: Sort by score
        docs_with_scores.sort(key=lambda x: x[1], reverse=False)

        # Step 5: Pick top_k
        top_docs = [doc for doc, score in docs_with_scores[:top_k]]

        logging.info(f"[RESULT] Returning {len(top_docs)} docs after all filters")
        for i, doc in enumerate(top_docs):
            logging.debug(f"[RESULT {i}] doc_id={doc.metadata.get('doc_id')} "
                          f"source_type={doc.metadata.get('source_path_type')} "
                          f"content={doc.page_content[:120]}...")

        if not top_docs:
            logging.warning(f"[RETRIEVE] No results for query='{query}' after filtering")

        return top_docs
