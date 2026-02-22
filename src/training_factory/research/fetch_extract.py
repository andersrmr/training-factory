from __future__ import annotations

from html.parser import HTMLParser

_BOILERPLATE_PATTERNS = [
    "browser is no longer supported",
    "upgrade to microsoft edge",
    "access to this page requires authorization",
    "sign in",
    "cookies",
    "privacy",
    "feedback",
    "javascript",
    "try signing in",
    "changing directories",
]


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

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
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


def normalize_text(s: str) -> str:
    return " ".join(s.lower().split())


def is_boilerplate(text: str) -> bool:
    normalized = normalize_text(text)
    return any(pattern in normalized for pattern in _BOILERPLATE_PATTERNS)


def _distinct_keyword_hits(text: str, intent_keywords: list[str]) -> int:
    normalized_text = normalize_text(text)
    seen: set[str] = set()
    for keyword in intent_keywords:
        if keyword and keyword in normalized_text:
            seen.add(keyword)
    return len(seen)


def snippet_score(heading: str, text: str, intent_keywords: list[str]) -> float:
    score = 0.0
    normalized_heading = normalize_text(heading)
    normalized_text = normalize_text(text)
    normalized_keywords = []
    for keyword in intent_keywords:
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword:
            normalized_keywords.append(normalized_keyword)

    heading_has_keyword = any(keyword in normalized_heading for keyword in normalized_keywords)
    text_hits = _distinct_keyword_hits(text, normalized_keywords)
    text_has_keyword = text_hits > 0

    if heading_has_keyword:
        score += 2.0
    if text_has_keyword:
        score += 1.0
    score += min(1.5, text_hits * 0.3)
    if len(text) >= 120:
        score += 0.5
    if is_boilerplate(text):
        score -= 2.0
    if len(text) < 40 and not heading_has_keyword:
        score -= 1.0
    return score


def extract_snippets(
    html: str,
    *,
    intent_keywords: list[str] | None = None,
    max_snippets: int = 4,
    max_chars: int = 1200,
) -> list[dict[str, str]]:
    if not html.strip():
        return []

    parser = _SnippetHTMLParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return []

    keywords = list(intent_keywords or [])
    ranked: list[tuple[float, int, dict[str, str]]] = []
    for idx, snippet in enumerate(parser.snippets):
        text = snippet.get("text", "")
        heading = snippet.get("heading", "")
        score = snippet_score(heading, text, keywords)
        if is_boilerplate(text) or score <= -1.5:
            continue
        ranked.append((score, idx, snippet))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    limit = max(max_snippets, 0)
    output: list[dict[str, str]] = []
    for _score, _idx, snippet in ranked[:limit]:
        clipped = dict(snippet)
        text = clipped.get("text", "")
        if len(text) > max_chars:
            clipped["text"] = text[:max_chars].rstrip()
        output.append(clipped)
    return output
