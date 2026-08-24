import pytest

from app.core.config import Settings
from app.domain.schemas import SourceInput
from app.services.ingestion import SourceIngestor, UnsafeSourceError, _TextExtractor, _validate_public_url


def test_ssrf_guard_rejects_localhost_without_network_lookup():
    with pytest.raises(UnsafeSourceError):
        _validate_public_url("http://localhost:8080/internal")


def test_ssrf_guard_rejects_non_http_scheme():
    with pytest.raises(UnsafeSourceError):
        _validate_public_url("file:///etc/passwd")


def test_html_extractor_ignores_script_content():
    parser = _TextExtractor()
    parser.feed("<html><body><h1>Result</h1><script>secret()</script><p>Useful evidence</p></body></html>")
    assert "Result" in parser.text()
    assert "Useful evidence" in parser.text()
    assert "secret" not in parser.text()


@pytest.mark.asyncio
async def test_materialize_text_truncates_to_configured_limit():
    settings = Settings(environment="test", COHERE_API_KEY="test", max_source_chars=10)
    result = await SourceIngestor(settings).materialize(
        [SourceInput(kind="text", content="abcdefghijklmnopqrstuvwxyz")]
    )
    assert result[0].content == "abcdefghij"
