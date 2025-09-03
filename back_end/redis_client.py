import os
import json
import redis.asyncio as redis
import logging

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

CHUNK_PREFIX = "chunk:"       # stores individual chunks
DOC_PREFIX = "doc_chunks:"    # stores list of chunk_ids per doc


async def cache_chunk(chunk: dict, expire_seconds: int = 24*3600):
    """
    Store a chunk in Redis and register its ID under the doc.
    chunk must contain: chunk_id, doc_id, text, title, meta
    """
    chunk_id = chunk["chunk_id"]
    doc_id = chunk["doc_id"]

    try:
        # Store the chunk
        await redis_client.set(f"{CHUNK_PREFIX}{chunk_id}", json.dumps(chunk), ex=expire_seconds)
        # Register chunk ID under the document
        await redis_client.rpush(f"{DOC_PREFIX}{doc_id}", chunk_id)
        logging.info(f"[REDIS] Cached chunk {chunk_id} for doc {doc_id}")
    except Exception as e:
        logging.error(f"[REDIS] Failed to cache chunk {chunk_id}: {e}")


async def get_cached_chunks(doc_ids: list) -> list:
    """
    Fetch all cached chunks for a list of doc_ids.
    """
    chunks = []
    for doc_id in doc_ids:
        try:
            chunk_ids = await redis_client.lrange(f"{DOC_PREFIX}{doc_id}", 0, -1)
            for chunk_id in chunk_ids:
                raw = await redis_client.get(f"{CHUNK_PREFIX}{chunk_id}")
                if raw:
                    chunks.append(json.loads(raw))
        except Exception as e:
            logging.error(f"[REDIS] Failed to fetch chunks for doc {doc_id}: {e}")
    return chunks
