import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "embed-english-v3.0")
PERSIST_DIR = os.getenv("RETRIEVER_PERSIST_DIR", "./persist")
EPS = 1e-12

import logging
logging.basicConfig(level=logging.INFO)
