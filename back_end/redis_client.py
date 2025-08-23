# redis_doc_cache.py
import asyncio
import json
import hashlib
from redis.asyncio import Redis
from concurrent.futures import ThreadPoolExecutor

redis = Redis(host="localhost", port=6379, db=0, decode_responses=True)
executor = ThreadPoolExecutor()

def _hash_key(doc_id: str, chunk_text: str) -> str:
    """Generate a Redis-safe key for a chunk under a doc_id."""
    text_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
    return f"{doc_id}:{text_hash}"

async def set_cached_chunk(key: str, value: str, expire: int = 86400):
    await redis.set(key, value, ex=expire)

async def get_cached_chunk(key: str):
    return await redis.get(key)

async def _embed_text(text: str, embed_fn):
    """Run embedding in executor if embed_fn is sync."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, lambda: embed_fn([text])[0])

async def batch_embed_chunks(doc_id: str, chunks: list, embed_fn, expire: int = 86400):
    """Embed chunks (PDF, URL, text) and cache them in Redis under the same doc_id."""
    
    async def process_chunk(chunk_text: str):
        key = _hash_key(doc_id, chunk_text)
        cached = await get_cached_chunk(key)
        if cached:
            return json.loads(cached)
        vec = await _embed_text(chunk_text, embed_fn)
        await set_cached_chunk(key, json.dumps(vec), expire=expire)
        return vec

    return await asyncio.gather(*(process_chunk(c) for c in chunks))
