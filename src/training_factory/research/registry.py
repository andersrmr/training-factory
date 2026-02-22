from __future__ import annotations

import logging
import os

from training_factory.research.fallback_provider import SimpleFallbackSearchProvider
from training_factory.research.providers import SearchProvider
from training_factory.research.serpapi_provider import SerpApiSearchProvider

logger = logging.getLogger(__name__)


def get_search_provider(name: str | None, *, web: bool = False) -> SearchProvider:
    requested_name = (name or "").strip().lower()
    normalized_name = requested_name or "fallback"
    if normalized_name not in {"fallback", "serpapi"}:
        logger.warning("Unknown search provider '%s'; using fallback", normalized_name)
        normalized_name = "fallback"

    # Honor explicit provider selection. Only auto-prefer SerpAPI in web mode
    # when no provider was explicitly requested.
    wants_serpapi = normalized_name == "serpapi" or (web and not requested_name)
    if wants_serpapi:
        if os.getenv("SERPAPI_API_KEY"):
            return SerpApiSearchProvider()
        logger.warning("SERPAPI_API_KEY not set; using fallback search provider")

    return SimpleFallbackSearchProvider()
