import re
from typing import List, Dict, Any
from PyPDF2 import PdfReader
from collections import Counter
from bs4 import BeautifulSoup
import requests

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


# ------------------- Text Chunking -------------------
def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    doc_id: str = "",
    title: str = None,
    meta: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks with metadata and keywords."""
    text = clean_text(text)
    if not text:
        return []

    meta = meta or {}
    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunk_meta = meta.copy()
            chunk_meta.update({
                "keywords": extract_keywords(chunk),
                "chunk_index": chunk_id,
            })
            chunks.append({
                "chunk_id": f"{doc_id}_{chunk_id}" if doc_id else str(chunk_id),
                "doc_id": doc_id,
                "title": title,
                "text": chunk,
                "score_bm25": 0.0,
                "score_vec": 0.0,
                "score_hybrid": 0.0,
                "meta": chunk_meta
            })
        start += chunk_size - chunk_overlap
        chunk_id += 1

    return chunks


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
    """
    Download a webpage and return cleaned text.
    Removes scripts, styles, and common non-content elements.
    """
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
