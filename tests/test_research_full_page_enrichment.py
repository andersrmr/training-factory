from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.agents.research import generate_research


def test_research_enriches_snippets_from_html_when_web_enabled(monkeypatch) -> None:
    import training_factory.research.fetch_extract as fetch_extract_module

    html_fixture = """
    <html>
      <body>
        <p>This browser is no longer supported.</p>
        <p>Access to this page requires authorization. Try signing in.</p>
        <h1>Title</h1>
        <h2>Governance</h2>
        <p>Governance best practices include environment separation.</p>
        <li>Use managed solutions</li>
      </body>
    </html>
    """

    monkeypatch.setattr(fetch_extract_module, "fetch_url", lambda _url, timeout=10: html_fixture)

    payload = generate_research(
        {
            "topic": "Power BI basics",
            "audience": "novice",
            "research": {"web": True, "search_provider": "fallback"},
        }
    )

    sources = payload["sources"]
    assert sources

    assert any(
        "governance" in snippet.get("heading", "").lower()
        for source in sources
        for snippet in source.get("snippets", [])
    )
    assert any(
        "environment separation" in snippet.get("text", "").lower()
        or "managed solutions" in snippet.get("text", "").lower()
        for source in sources
        for snippet in source.get("snippets", [])
    )
    assert all(
        "browser is no longer supported" not in snippet.get("text", "").lower()
        and "authorization" not in snippet.get("text", "").lower()
        for source in sources
        for snippet in source.get("snippets", [])
    )
    assert all(len(source.get("snippets", [])) <= 4 for source in sources)
