# Phase 2 – Search Provider Abstraction

## Motivation
The pipeline needs a stable abstraction for web search before adding a research slice. A `SearchProvider` interface isolates search acquisition from graph logic so provider behavior can evolve without changing agent contracts.

Pluggability matters because runtime environments differ:
- `SerpAPI` enables live web retrieval when credentials are available.
- A deterministic fallback provider enables reliable operation without external services.

Offline determinism is preserved for tests by default:
- Tests do not perform network I/O.
- Fallback behavior is deterministic and local.
- SerpAPI is only used when explicitly selected and configured.

Graph wiring and the research slice were intentionally deferred to keep this step narrow: establish provider boundaries first, then integrate them into state flow in a later step.

## Implemented in This Step
- `src/training_factory/research/providers.py`
  - `SearchResult` model
  - `SearchProvider` protocol
- `src/training_factory/research/serpapi_provider.py`
  - SerpAPI-backed provider with env-based key usage, timeout/error handling, normalized results
- `src/training_factory/research/fallback_provider.py`
  - Deterministic offline provider with curated authoritative references
- `src/training_factory/research/registry.py`
  - Provider selection and fallback logic (`serpapi` / `fallback`, graceful degradation)
- CLI updates
  - Added `--web` and `--search-provider`
  - Stores research config in request payload
- Dependency update
  - Added `requests` to project dependencies
- Test coverage
  - Registry default behavior
  - SerpAPI-without-key fallback behavior
  - Fallback provider returns authoritative Power Platform references

## Not Implemented Yet
- No research slice agent
- No `context_pack`
- No deterministic authority scoring
- No graph rewiring
- No schema changes

## Design Decisions
- SerpAPI is optional and environment-driven via `SERPAPI_API_KEY`.
- Fallback provider is deterministic and offline-safe.
- Registry handles graceful degradation to fallback when SerpAPI is unavailable.
- CLI stores research configuration in `request` but execution logic does not consume it yet.

## Next Step
Implement a research slice that performs deterministic source scoring and generates `context_pack` for downstream agents.
