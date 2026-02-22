from __future__ import annotations

from html.parser import HTMLParser


def fetch_url(url: str, *, timeout: int = 10) -> str:
    try:
        import requests
    except ImportError:
        return ""

    headers = {
        "User-Agent": "training-factory/0.1 (+https://example.local)",
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException:
        return ""
    return response.text


class _SnippetHTMLParser(HTMLParser):
    _target_tags = {"h1", "h2", "h3", "p", "li"}

    def __init__(self, *, max_chars: int = 1200) -> None:
        super().__init__(convert_charrefs=True)
        self._max_chars = max_chars
        self._current_tag: str | None = None
        self._current_chunks: list[str] = []
        self._current_heading = ""
        self._tag_counts: dict[str, int] = {}
        self.snippets: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        lowered = tag.lower()
        if lowered in self._target_tags and self._current_tag is None:
            self._current_tag = lowered
            self._current_chunks = []

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._current_tag is not None:
            self._current_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        lowered = tag.lower()
        if self._current_tag != lowered:
            return

        raw_text = " ".join(self._current_chunks).strip()
        cleaned = " ".join(raw_text.split())
        if cleaned:
            if len(cleaned) > self._max_chars:
                cleaned = cleaned[: self._max_chars].rstrip()

            self._tag_counts[lowered] = self._tag_counts.get(lowered, 0) + 1
            loc = f"{lowered}[{self._tag_counts[lowered]}]"

            heading = self._current_heading
            if lowered in {"h1", "h2", "h3"}:
                self._current_heading = cleaned
                heading = cleaned

            self.snippets.append(
                {
                    "heading": heading or lowered,
                    "text": cleaned,
                    "loc": loc,
                }
            )

        self._current_tag = None
        self._current_chunks = []


def extract_snippets(html: str, *, max_snippets: int = 4, max_chars: int = 1200) -> list[dict[str, str]]:
    if not html.strip():
        return []

    parser = _SnippetHTMLParser(max_chars=max_chars)
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return []

    return parser.snippets[: max(max_snippets, 0)]
