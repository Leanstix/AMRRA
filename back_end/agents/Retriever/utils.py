import re
import uuid
from typing import List, Dict, Any
from collections import Counter
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
import requests
import numpy as np


# ------------------- Text Cleaning -------------------
def clean_text(text: str) -> str:
    """Normalize whitespace and remove artifacts like form feeds."""
    if not text:
        return ""
    text = text.replace("\u000c", " ")  # form feed
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ------------------- Keywords -------------------
def extract_keywords(text: str, top_n=5) -> List[str]:
    """Extract most frequent words as basic keywords."""
    if not text:
        return []
    words = re.findall(r'\b\w+\b', text.lower())
    freq = Counter(words)
    return [w for w, _ in freq.most_common(top_n)]


# ------------------- PDF Extraction -------------------
def extract_pdf_text(file_path: str) -> List[Dict[str, Any]]:
    """Extract clean text from each page of a PDF."""
    texts = []
    try:
        reader = PdfReader(file_path)
        if reader.is_encrypted:
            reader.decrypt("")  # try empty password
        for i, page in enumerate(reader.pages):
            page_text = clean_text(page.extract_text() or "")
            if page_text:
                texts.append({"page": i + 1, "text": page_text})
    except Exception as e:
        raise RuntimeError(f"Failed to read PDF {file_path}: {e}")
    return texts


# ------------------- URL Fetching -------------------
def fetch_and_clean_url(url: str) -> str:
    """Download a webpage and return cleaned text."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch URL {url}: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove scripts, style, and non-content tags
    for tag in soup(["script", "style", "noscript", "header", "footer", "form", "meta", "link"]):
        tag.extract()

    text = soup.get_text(separator=" ")
    return clean_text(text)


# ------------------- Numbers Extraction -------------------
def extract_numbers(text: str) -> List[float]:
    """Extract numeric values from text."""
    matches = re.findall(r'-?\d+(?:\.\d+)?', text)
    return [float(m) for m in matches]


# ------------------- Text Chunking -------------------
def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    doc_id: str = None,
    title: str = None,
    meta: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks with metadata."""
    meta = meta or {}
    tokens = text.split()
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_str = " ".join(chunk_tokens)
        chunk_meta = meta.copy()
        chunk_meta["raw_numbers"] = extract_numbers(chunk_text_str)
        chunk = {
            "chunk_id": str(uuid.uuid4()),
            "doc_id": doc_id or "unknown",
            "title": title,
            "text": chunk_text_str,
            "meta": chunk_meta
        }
        chunks.append(chunk)
        start += chunk_size - chunk_overlap
    return chunks


# ------------------- Retriever Utils -------------------
class RetrieverUtils:
    EPS = 1e-10

    @staticmethod
    def tokenize(text: str) -> List[str]:
        return text.lower().split()

    @staticmethod
    def normalize_vector(v: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(v)
        return v / (norm + RetrieverUtils.EPS)

    @staticmethod
    def filter_irrelevant_numbers(text: str) -> str:
        """Drop noisy number-like patterns (ISBNs, SKUs, dimensions, etc.)."""
        # Drop ISBNs
        text = re.sub(r"\b97[89][0-9]{10}\b", "", text)
        # Drop product dimensions
        text = re.sub(r"\b\d+(\.\d+)?\s?(cm|mm|inch|inches|kg|lbs)\b", "", text, flags=re.I)
        # Drop ASINs / SKU-like codes
        text = re.sub(r"\b[A-Z0-9]{8,}\b", "", text)
        # Drop page numbers
        text = re.sub(r"\bPage\s?\d+\b", "", text, flags=re.I)
        return text.strip()
