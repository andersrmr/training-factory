from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.research.fetch_extract import extract_snippets


def test_extract_snippets_filters_boilerplate_and_keeps_relevant_content() -> None:
    html = """
    <html>
      <body>
        <p>This browser is no longer supported.</p>
        <p>Upgrade to Microsoft Edge to take advantage of the latest features.</p>
        <p>Access to this page requires authorization. You can try signing in.</p>
        <h2>Governance</h2>
        <p>Application lifecycle management (ALM) is critical for governance and deployment.</p>
        <li>Use managed solutions for production deployments.</li>
      </body>
    </html>
    """

    snippets = extract_snippets(
        html,
        intent_keywords=["governance", "alm", "lifecycle", "deployment"],
        max_snippets=4,
    )

    texts = [snippet.get("text", "").lower() for snippet in snippets]

    assert all("browser is no longer supported" not in text for text in texts)
    assert all("authorization" not in text for text in texts)
    assert any(
        "application lifecycle management" in text or "managed solutions" in text for text in texts
    )
    assert len(snippets) <= 4
