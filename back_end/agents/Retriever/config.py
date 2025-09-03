import os
from dotenv import load_dotenv

load_dotenv()

# Optional API keys (not required if using HuggingFace embeddings)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
GROQ_API_KEY=os.getenv("GROQ_API_KEY","")

# Embedding model (default to local HuggingFace E5 model)
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/e5-small-v2")

PERSIST_DIR = os.path.join(os.getcwd(), "retriever_data")
EPS = 1e-12

import logging
logging.basicConfig(level=logging.INFO)
