from __future__ import annotations

from training_factory.research.providers import SearchProvider, SearchResult


class SimpleFallbackSearchProvider(SearchProvider):
    _product_keywords = ("power bi", "power apps", "power platform", "alm")

    def search(self, query: str, *, num_results: int = 10) -> list[SearchResult]:
        lower_query = query.lower()
        if any(keyword in lower_query for keyword in self._product_keywords):
            results = [
                SearchResult(
                    title="Power Platform documentation overview",
                    url="https://learn.microsoft.com/power-platform/",
                    snippet="Official Microsoft Learn entry point for Power Platform guidance.",
                    source="learn.microsoft.com",
                    rank=1,
                ),
                SearchResult(
                    title="Application lifecycle management (ALM) with Power Platform",
                    url="https://learn.microsoft.com/power-platform/alm/overview-alm",
                    snippet="Microsoft guidance for ALM processes, environments, and release practices.",
                    source="learn.microsoft.com",
                    rank=2,
                ),
                SearchResult(
                    title="Power BI documentation",
                    url="https://learn.microsoft.com/power-bi/",
                    snippet="Official Power BI product docs for modeling, governance, and deployment.",
                    source="learn.microsoft.com",
                    rank=3,
                ),
            ]
        else:
            results = [
                SearchResult(
                    title="NIST Cybersecurity Framework",
                    url="https://www.nist.gov/cyberframework",
                    snippet="Security best-practices framework useful for governance-focused training.",
                    source="nist.gov",
                    rank=1,
                ),
                SearchResult(
                    title="OWASP Top 10",
                    url="https://owasp.org/www-project-top-ten/",
                    snippet="Well-known reference for common application security risks and mitigations.",
                    source="owasp.org",
                    rank=2,
                ),
                SearchResult(
                    title="Google Developer Documentation Style Guide",
                    url="https://developers.google.com/style",
                    snippet="Clear writing and documentation standards for technical content creation.",
                    source="developers.google.com",
                    rank=3,
                ),
            ]
        return results[: max(num_results, 0)]
