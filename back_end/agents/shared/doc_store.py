# agents/shared/doc_store.py

"""
Global in-memory document registry.
Keeps track of ingested documents across agents.
This is NOT persistent — use a DB if you need persistence.
"""

# key: doc_id (str)
# value: dict { "type": "pdf"|"url", "title": str, ... }
doc_store: dict[str, dict] = {}
