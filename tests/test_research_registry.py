from __future__ import annotations

from types import SimpleNamespace

from training_factory.research.fallback_provider import SimpleFallbackSearchProvider
import training_factory.research.registry as registry_module
from training_factory.research.registry import get_search_provider


def test_registry_default_returns_fallback() -> None:
    provider = get_search_provider(None)
    assert isinstance(provider, SimpleFallbackSearchProvider)


def test_registry_serpapi_without_key_falls_back(monkeypatch) -> None:
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    monkeypatch.setattr(
        registry_module,
        "get_settings",
        lambda: SimpleNamespace(serpapi_api_key=None),
    )
    provider = get_search_provider("serpapi")
    assert isinstance(provider, SimpleFallbackSearchProvider)


def test_fallback_returns_authoritative_power_platform_result() -> None:
    provider = SimpleFallbackSearchProvider()
    results = provider.search("Power Platform ALM best practices")
    assert len(results) >= 1
    assert any("learn.microsoft.com" in result.url for result in results)
