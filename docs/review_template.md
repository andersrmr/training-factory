# Architecture Review — Step {{STEP_NUMBER}}

## Context
- Step: `{{STEP_NUMBER}}`
- Date: `{{YYYY-MM-DD}}`
- Reviewer: `{{NAME}}`
- Scope: `{{FEATURE_SCOPE}}`

## A) Current architecture summary

### Modules and responsibilities
- `{{path/to/module_a.py}}`: {{responsibility}}
- `{{path/to/module_b.py}}`: {{responsibility}}
- `{{path/to/module_c.py}}`: {{responsibility}}

### State/data flow
1. `{{NODE_A}} -> {{NODE_B}}`: {{what flows / key outputs}}
2. `{{NODE_B}} -> {{NODE_C}}`: {{what flows / key outputs}}
3. `{{NODE_C}} -> {{END_OR_BRANCH}}`: {{routing behavior}}

### Validation and boundaries
- JSON extraction occurs in: `{{path}}`
- Slice/schema validation occurs in: `{{path}}`
- Final/bundle validation occurs in: `{{path}}`

## B) Cleanliness checks

- Separation of concerns (`graph` vs `agents` vs `utils`): **{{PASS|FAIL}}**
  - {{explanation}}
- DRY-ness (shared helpers, no repeated logic): **{{PASS|FAIL}}**
  - {{explanation}}
- Schema boundaries (slice vs aggregate schema): **{{PASS|FAIL}}**
  - {{explanation}}
- Test determinism (no unintended network/runtime coupling): **{{PASS|FAIL}}**
  - {{explanation}}
- Control-loop boundedness (routing, counters, retries): **{{PASS|FAIL}}**
  - {{explanation}}

## C) Risks / smells (ranked)

1. **{{risk_title_1}}**
   - Why it matters: {{impact}}
   - Trigger/signals: {{what to watch}}
2. **{{risk_title_2}}**
   - Why it matters: {{impact}}
   - Trigger/signals: {{what to watch}}
3. **{{risk_title_3}}**
   - Why it matters: {{impact}}
   - Trigger/signals: {{what to watch}}
4. **{{risk_title_4}}**
   - Why it matters: {{impact}}
   - Trigger/signals: {{what to watch}}
5. **{{risk_title_5}}**
   - Why it matters: {{impact}}
   - Trigger/signals: {{what to watch}}

## D) Recommendations before next step

1. **{{recommendation_1}}**
   - Impact: `{{high|medium|low}}`
   - Effort: `{{high|medium|low}}`
   - Why: {{reason}}
2. **{{recommendation_2}}**
   - Impact: `{{high|medium|low}}`
   - Effort: `{{high|medium|low}}`
   - Why: {{reason}}
3. **{{recommendation_3}}**
   - Impact: `{{high|medium|low}}`
   - Effort: `{{high|medium|low}}`
   - Why: {{reason}}
4. **{{recommendation_4}}**
   - Impact: `{{high|medium|low}}`
   - Effort: `{{high|medium|low}}`
   - Why: {{reason}}
5. **{{recommendation_5}}**
   - Impact: `{{high|medium|low}}`
   - Effort: `{{high|medium|low}}`
   - Why: {{reason}}

## E) Expansion readiness

**Is this clean enough for next step (`{{NEXT_STEP_NAME}}`)?**
- Verdict: **{{YES|YES_WITH_CAVEATS|NO}}**
- Rationale: {{short rationale}}

### Watch-outs for next step
- {{watch_out_1}}
- {{watch_out_2}}
- {{watch_out_3}}

## Test status
- Command run: `{{pytest or other}}`
- Result: **{{passed|failed}}**
- Notes: {{failures/flakiness/environment caveats}}

## Appendix (optional)
- Key files reviewed:
  - `{{path_1}}`
  - `{{path_2}}`
  - `{{path_3}}`
- Open questions:
  - {{question_1}}
  - {{question_2}}
