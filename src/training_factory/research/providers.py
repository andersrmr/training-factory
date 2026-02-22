from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    source: str = ""
    rank: int = 0


class SearchProvider(Protocol):
    def search(self, query: str, *, num_results: int = 10) -> list[SearchResult]:
        ...
