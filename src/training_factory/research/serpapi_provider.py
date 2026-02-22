from __future__ import annotations

import logging
import os
from typing import Any

from training_factory.research.providers import SearchProvider, SearchResult
from training_factory.settings import get_settings

logger = logging.getLogger(__name__)


class SerpApiSearchProvider(SearchProvider):
    _endpoint = "https://serpapi.com/search.json"

    def __init__(self, api_key: str | None = None, *, timeout_seconds: float = 10.0) -> None:
        resolved_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not resolved_key:
            resolved_key = get_settings().serpapi_api_key
        self._api_key = resolved_key
        self._timeout_seconds = timeout_seconds

    def search(self, query: str, *, num_results: int = 10) -> list[SearchResult]:
        if not self._api_key:
            logger.warning("SERPAPI_API_KEY not set; SerpAPI search disabled")
            return []

        try:
            import requests
        except ImportError:
            logger.warning("requests is not installed; SerpAPI search disabled")
            return []

        params = {
            "engine": "google",
            "q": query,
            "num": num_results,
            "api_key": self._api_key,
        }

        try:
            response = requests.get(self._endpoint, params=params, timeout=self._timeout_seconds)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("SerpAPI request failed: %s", exc)
            return []

        try:
            payload: dict[str, Any] = response.json()
        except ValueError as exc:
            logger.warning("SerpAPI returned invalid JSON: %s", exc)
            return []

        organic = payload.get("organic_results", [])
        if not isinstance(organic, list):
            return []

        results: list[SearchResult] = []
        for idx, item in enumerate(organic[:num_results], start=1):
            if not isinstance(item, dict):
                continue
            url = str(item.get("link", "")).strip()
            title = str(item.get("title", "")).strip()
            if not url or not title:
                continue
            snippet = str(item.get("snippet", "")).strip()
            source = str(item.get("source", "")).strip()
            results.append(
                SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source=source,
                    rank=idx,
                )
            )
        return results
