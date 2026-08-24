from __future__ import annotations

import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx

from app.core.config import Settings
from app.domain.schemas import SourceInput


class UnsafeSourceError(ValueError):
    pass


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str):
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str):
        if not self._skip_depth and data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return " ".join(self.parts)


def _validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeSourceError("only absolute HTTP(S) URLs are allowed")
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"}:
        raise UnsafeSourceError("local addresses are not allowed")
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeSourceError("URL hostname could not be resolved") from exc
    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        if not address.is_global:
            raise UnsafeSourceError("private, loopback, link-local, or reserved addresses are not allowed")


class SourceIngestor:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def materialize(self, sources: list[SourceInput]) -> list[SourceInput]:
        materialized: list[SourceInput] = []
        for source in sources:
            if source.kind == "text":
                content = (source.content or "")[: self.settings.max_source_chars]
                materialized.append(SourceInput(kind="text", title=source.title, content=content))
            else:
                materialized.append(await self._fetch_url(source))
        return materialized

    async def _fetch_url(self, source: SourceInput) -> SourceInput:
        assert source.url
        url = source.url
        headers = {"User-Agent": "AMRRA/2.0 research-agent"}
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=False, headers=headers) as client:
            for _ in range(4):
                _validate_public_url(url)
                response = await client.get(url)
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location:
                        raise UnsafeSourceError("redirect response did not include Location")
                    url = urljoin(url, location)
                    continue
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type and "text/plain" not in content_type:
                    raise UnsafeSourceError(f"unsupported URL content type: {content_type or 'unknown'}")
                if len(response.content) > self.settings.max_source_chars * 4:
                    raise UnsafeSourceError("remote source exceeds configured size limit")
                if "text/html" in content_type:
                    parser = _TextExtractor()
                    parser.feed(response.text)
                    text = parser.text()
                else:
                    text = response.text
                text = " ".join(text.split())[: self.settings.max_source_chars]
                if not text:
                    raise UnsafeSourceError("remote source did not contain readable text")
                return SourceInput(kind="text", title=source.title or url, content=text)
        raise UnsafeSourceError("too many redirects")
