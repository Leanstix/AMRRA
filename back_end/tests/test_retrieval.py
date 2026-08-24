import pytest

from app.domain.schemas import SourceInput
from app.providers.base import FakeProvider
from app.services.retrieval import Retriever


def long_source() -> SourceInput:
    return SourceInput(
        kind="text",
        title="paper",
        content=("background unrelated material " * 230)
        + ("treatment recovery outcome evidence " * 230),
    )


@pytest.mark.asyncio
async def test_llm_reranker_can_reorder_only_known_candidates():
    provider = FakeProvider(
        [
            {
                "rankings": [
                    {"chunk_id": "made-up", "relevance": 1.0, "reason": "invalid"},
                    {
                        "chunk_id": "source-1-chunk-2",
                        "relevance": 0.99,
                        "reason": "directly discusses the outcome",
                    },
                ]
            }
        ],
        rerank_enabled=True,
    )
    evidence = await Retriever(provider).retrieve(
        "Does treatment improve recovery outcome?",
        [long_source()],
        3,
    )
    assert len(evidence) == 3
    ranked = next(item for item in evidence if item.chunk_id == "source-1-chunk-2")
    assert ranked.metadata["agent_relevance"] == 0.99
    assert all(item.chunk_id != "made-up" for item in evidence)


@pytest.mark.asyncio
async def test_reranker_failure_degrades_to_lexical_ranking():
    provider = FakeProvider([], rerank_enabled=True)
    evidence = await Retriever(provider).retrieve(
        "Does treatment improve recovery outcome?",
        [long_source()],
        3,
    )
    assert len(evidence) == 3
    assert all("rerank_fallback" in item.metadata for item in evidence)
