import logging
from typing import List, Dict, Union, Optional
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, Tool
from langchain.schema import Document

from model.extractor_model import RetrievalOutput, Evidence
from .retriever_engine import RetrieverEngine
from agents.shared.doc_store import doc_store  # ✅ use shared doc_store

load_dotenv()
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


class RetrieverAgent:
    def __init__(self, llm=None):
        self.engine = RetrieverEngine()
        self.llm = llm or ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

        self.refine_prompt = PromptTemplate(
            input_variables=["query"],
            template=(
                "You are an expert retrieval assistant. "
                "Refine this query into a sharper, more specific version:\n\n"
                "Original: {query}\n\nRefined:"
            ),
        )

    # -------------------- Ingest --------------------
    def ingest(self, sources: List[Dict[str, Union[str, bytes]]], force: bool = False) -> List[str]:
        ingested_docs = []
        for src in sources:
            doc_id = src.get("doc_id")
            logging.debug(f"[INGEST] Processing source: {src}")
            if not doc_id:
                logging.warning("[INGEST] Skipping source with no doc_id")
                continue
            if doc_id in doc_store and not force:
                logging.info(f"[INGEST] Skipping already ingested doc {doc_id}")
                continue

            success = False
            try:
                if "file_bytes" in src or "file_path" in src:
                    logging.info(f"[INGEST] Ingesting PDF for doc_id={doc_id}")
                    success = self.engine.ingest_pdfs(
                        file_bytes=src.get("file_bytes"),
                        file_path=src.get("file_path"),
                        doc_id=doc_id
                    )
                elif "url" in src:
                    logging.info(f"[INGEST] Ingesting URL {src['url']} for doc_id={doc_id}")
                    success = self.engine.ingest_urls(
                        src["url"], doc_id, chunk_size=1000, chunk_overlap=100
                    )

                if success:
                    # ✅ register in shared doc_store
                    doc_store[doc_id] = {
                        "type": "pdf" if "file_bytes" in src or "file_path" in src else "url",
                        "path": src.get("file_path") or src.get("url", "upload"),
                        "title": src.get("title")
                    }
                    ingested_docs.append(doc_id)
                    logging.info(f"[INGEST] Added {doc_id} ({doc_store[doc_id]['type']})")
                else:
                    logging.error(f"[INGEST] FAILED to ingest {doc_id}")
            except Exception as e:
                logging.exception(f"[INGEST] Exception while ingesting {doc_id}: {e}")

        return ingested_docs

    # -------------------- Build Tools --------------------
    def build_tools(self, allowed_doc_ids: List[str], top_k: int = 5) -> List[Tool]:
        tools = []
        logging.debug(f"[TOOLS] Building tools for doc_ids={allowed_doc_ids}")

        for doc_id in allowed_doc_ids:
            if doc_id not in doc_store:
                logging.warning(f"[TOOLS] Skipping {doc_id}, not in doc_store")
                continue
            doc_type = doc_store[doc_id]["type"]

            def make_retriever_fn(doc_id=doc_id, doc_type=doc_type):
                def retriever_fn(query: str) -> str:
                    logging.debug(f"[TOOLS] Running retriever_fn for doc_id={doc_id}, query='{query}'")
                    try:
                        docs: List[Document] = self.engine.retrieve(
                            query, doc_ids=[doc_id], source_type=doc_type, top_k=top_k
                        )
                        if not docs:
                            logging.warning(f"[NO RESULTS] For query='{query}' in doc_id={doc_id}")
                            return f"[NO RESULTS] No evidence found in {doc_id}"
                        return "\n\n".join(d.page_content for d in docs)
                    except Exception as e:
                        logging.exception(f"[TOOLS] Error in retriever_fn for {doc_id}: {e}")
                        return f"[ERROR] Retrieval failed for {doc_id}: {e}"
                return retriever_fn

            tools.append(
                Tool(
                    name=f"search_{doc_type}_{doc_id}",
                    func=make_retriever_fn(),
                    description=f"Search only inside {doc_type} document {doc_id}"
                )
            )
            logging.debug(f"[TOOLS] Added tool for {doc_id}")

        return tools

    # -------------------- Retrieve --------------------
    def retrieve(
        self,
        query: str,
        doc_ids: Optional[List[str]] = None,
        top_k: int = 5,
        debug: bool = False
    ) -> RetrievalOutput:
        if not doc_ids:
            raise ValueError("You must provide doc_ids. Agent cannot search outside given docs.")

        # Step 1: Refine query
        logging.info(f"[RETRIEVE] Refining query='{query}'")
        try:
            llm_resp = self.llm.invoke(self.refine_prompt.format(query=query))
            refined_query = getattr(llm_resp, "content", str(llm_resp)).strip()
        except Exception as e:
            logging.exception(f"[REFINE] Error refining query: {e}")
            refined_query = query  # fallback
        logging.info(f"[REFINE] Original: '{query}' | Refined: '{refined_query}'")

        # Step 2: Build tools
        tools = self.build_tools(doc_ids, top_k=top_k)
        logging.debug(f"[RETRIEVE] Built {len(tools)} tools")
        if not tools:
            raise RuntimeError("No valid tools could be built (maybe ingestion failed).")

        # Step 3: Run agent
        logging.info(f"[RETRIEVE] Running agent with refined query='{refined_query}'")
        try:
            agent = initialize_agent(
                tools=tools,
                llm=self.llm,
                agent="zero-shot-react-description",
                verbose=debug
            )
            agent_response = agent.run(refined_query)
            logging.info(f"[AGENT] Response: {agent_response[:200]}...")
        except Exception as e:
            logging.exception(f"[AGENT] Error running agent: {e}")
            agent_response = f"[ERROR] Agent failed: {e}"

        # Step 4: Collect provenance directly
        all_docs = []
        for doc_id in doc_ids:
            if doc_id not in doc_store:
                logging.warning(f"[RETRIEVE] Skipping doc_id={doc_id}, not in doc_store")
                continue
            doc_type = doc_store[doc_id]["type"]
            logging.debug(f"[RETRIEVE] Direct retrieval for doc_id={doc_id}, query='{refined_query}'")
            try:
                retrieved = self.engine.retrieve(
                    refined_query, doc_ids=[doc_id], source_type=doc_type, top_k=top_k
                )
                logging.debug(f"[RETRIEVE] Retrieved {len(retrieved)} chunks from {doc_id}")
                all_docs.extend(retrieved)
            except Exception as e:
                logging.exception(f"[RETRIEVE] Error retrieving from {doc_id}: {e}")

        # Dedup & format evidence
        seen_chunk_ids = set()
        evidence_chunks = []
        for idx, doc in enumerate(all_docs[:top_k]):
            cid = doc.metadata.get("chunk_id", f"{idx}")
            if cid in seen_chunk_ids:
                continue
            seen_chunk_ids.add(cid)
            evidence_chunks.append(Evidence(
                chunk_id=cid,
                doc_id=doc.metadata.get("doc_id", f"unknown::{idx}"),
                text=doc.page_content,
                meta=doc.metadata,
                title=doc.metadata.get("title") or doc.metadata.get("source_path")
            ))

        provenance = {"retrieved_from": list({
            doc.metadata.get("source_path", doc.metadata.get("title", "unknown"))
            for doc in all_docs
        })}
        logging.info(f"[RETRIEVE] Returning {len(evidence_chunks)} evidence chunks")

        return RetrievalOutput(query=query, evidence_chunks=evidence_chunks, provenance=provenance)
