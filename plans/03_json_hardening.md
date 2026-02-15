# Step 3 — JSON Hardening and Output Validation

## Goal
Improve reliability of agent outputs by enforcing strict JSON-only responses and adding a robust JSON extraction and validation process.

This step ensures that:
- LLM responses are reliably parsed as JSON
- Schema validation is consistently applied
- The system is more stable and testable

---

## Definition of Done
- All agents enforce “return JSON only” in their prompts.
- A JSON extraction helper exists and is used by all agents.
- Extraction handles cases where extra text surrounds the JSON.
- Agent outputs are validated against their schemas.
- Unit tests pass with the hardened JSON flow.

---

## Summary of Changes
- Added a JSON extraction helper to:
  - Attempt direct `json.loads`
  - Fallback to extracting the first `{ ... }` block
- Updated agent prompts to explicitly require JSON-only outputs.
- Updated agents to:
  - Use the JSON extractor
  - Validate outputs against schemas
- Added or updated tests for JSON extraction logic.
- Ensured all tests pass after changes.

---

## Commit
Step 3: hardened JSON outputs and validation
