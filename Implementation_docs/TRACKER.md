# TRACKER.md

# Hiring Operations Agent MVP — Implementation Tracker

**Living document.** Update this after every work session and at each phase
boundary. It mirrors the phases in `MASTER_IMPLEMENTATION.md`. Do not start a
new phase until the previous one is approved by the user.

**Status legend:** `NOT STARTED` · `IN PROGRESS` · `BLOCKED` · `IN REVIEW` · `DONE`

---

## Snapshot

| Phase | Title | Status | Progress |
|---|---|---|---|
| 0 | Repository Bootstrap & Planning | DONE | 100% |
| 1 | Foundations: Contracts, Config, LLM + Deterministic Fallback | DONE | 100% |
| 2 | LangGraph Reasoning Pipeline (→ WAIT_FOR_HUMAN) | DONE | 100% |
| 3 | Human-in-the-Loop: Intent, Approve/Modify/Unsupported, Mock Execution | NOT STARTED | 0% |
| 4 | Platform Integration: FastAPI, Router, Watcher, Sessions | NOT STARTED | 0% |
| 5 | Gradio UI + End-to-End Validation + Docs | NOT STARTED | 0% |

> Phase 0 is the bootstrap/planning task (this deliverable). Phases 1–5 are the
> implementation phases and begin only after user approval, one at a time.

---

## Phase 0 — Repository Bootstrap & Planning

- **Status:** DONE
- **Progress:** 100%
- **Deliverables:**
  - [x] `.venv` created (Python 3.12.10, **no packages installed**)
  - [x] `requirements.txt`
  - [x] `.env.example`
  - [x] `.gitignore` (Python / FastAPI / Gradio / LangGraph / VS Code / PyCharm)
  - [x] `Implementation_docs/MASTER_IMPLEMENTATION.md`
  - [x] `Implementation_docs/TRACKER.md`
  - [x] `AGENTS.md` — appended Implementation Workflow section
- **Checklist:**
  - [x] Source docs + AGENTS.md read and treated as immutable
  - [x] Fixtures, hiring tracker, candidate profiles analyzed
  - [x] Phases defined (fewer, larger, reviewable)
  - [x] No application code written
- **Blockers:** None
- **Notes:** Environment questions surfaced to user (only real secret is `OLLAMA_API_KEY`; deterministic fallback mandated for LLM-unavailable case).

---

## Phase 1 — Foundations: Data Contracts, Config, LLM + Deterministic Fallback

- **Status:** DONE (reviewed and approved; committed as Phase 1)
- **Progress:** 100%
- **Deliverables:**
  - [x] Backend package skeleton per `system_architecture.md` §8 (17 packages + root `conftest.py`)
  - [x] `data/runtime/*` + `data/fixtures/expected_outputs/` + `data/templates/` (with `.gitkeep`)
  - [x] `schemas/`: enums, meeting_package, **hiring_tracker**, artifacts, operations_package, approval_package, workflow_state, events, `_time`
  - [x] `core/common/`: config, logging, ids, json_io, paths
  - [x] `core/llm/`: base, ollama_provider, fallback_provider, client (retry + validation)
  - [x] Data-contract validation — **all three `data/` files** parse (2 Meeting Packages + `hiring_tracker.json`)
  - [x] `pytest` unit tests (schemas, config, fallback, retry) — **16 passed**
  - [x] Dependencies installed into `.venv`; `requirements.lock` frozen (81 pins)
- **Checklist:**
  - [x] Schemas cover §8.1, §8.2, and full WorkflowState (§14.1, 17 keys)
  - [x] Both fixtures validate; malformed rejected
  - [x] `hiring_tracker.json` validates against `HiringTracker`
  - [x] Config maps all `.env.example` keys; `LLM_MODE` ∈ {cloud, fallback}
  - [x] Fallback provider produces valid structured output offline (no network)
  - [x] Validator rejects bad output → retry with error fed back (§15)
  - [x] Folder structure matches §8
  - [x] `pytest` green; `ruff check` clean
- **Blockers:** None
- **Notes:** Schema-first: hiring artifact models defined in `schemas/artifacts.py`
  now (Phase 2 `agents/hiring/models.py` re-exports + adds node logic).
  `candidate_profile/` PDFs are reference-only (no PDF dependency; "Resume"
  evidence sources from `payload.candidate` in Phase 2). Optional live-Ollama
  smoke (`LLM_MODE=cloud`) also run live and **passed** (raw call + structured
  path; the §15 retry loop self-corrected a real malformed field), confirming
  the `/v1` path end to end.

---

## Phase 2 — LangGraph Reasoning Pipeline (→ WAIT_FOR_HUMAN)

- **Status:** DONE (reviewed and approved; committed as Phase 2)
- **Progress:** 100%
- **Deliverables:**
  - [x] `agents/hiring/models.py` (re-exports Phase 1 artifact contracts + `TrackerContext`)
  - [x] `agents/hiring/nodes/` — 10 linear nodes + `base` (Context Validation → Approval Package Generation)
  - [x] `agents/hiring/prompts/` — `base` (schema/enum embedder) + `reasoning` (7 per-node builders)
  - [x] `agents/hiring/services/` — `fallbacks` (rule-based reasoner), `evidence` (graph + grounding), operations + approval package builders
  - [x] `agents/hiring/workflow.py` — StateGraph compiled with `interrupt_before=["wait_for_human"]`; `run_to_interrupt`
  - [x] `core/workflow/` — `checkpointer` (InMemorySaver) + `engine` (run-to-interrupt + §15.1 events)
  - [x] `agents/hiring/dev_runner.py` — offline fixture runner
- **Checklist:**
  - [x] Node order/names match Diagram 3 / §7 (no renames)
  - [x] Each node sets `workflow_stage` per Appendix B
  - [x] Evidence-first enforced (grounding validator + `validate=` retry hook → regenerated)
  - [x] Interrupt fires at WAIT_FOR_HUMAN; state persists (`next == ('wait_for_human',)`)
  - [x] Full pipeline runs offline (`LLM_MODE=fallback`) — no network
  - [x] Strong ≠ borderline (move_forward@0.81 vs hold@0.54)
  - [x] Malformed / empty-transcript package → Rejected (terminal, no reasoning)
  - [x] `pytest` green (38 passed) + `ruff` clean
- **Blockers:** None
- **Notes:** Checkpoint serialization of Pydantic artifacts verified up front (spike) —
  stored directly in state, no dict workaround. Live `LLM_MODE=cloud` full-pipeline
  run also passed (7/7 reasoning nodes validated first try; grounded reasoning citing
  real evidence ids). Prompt builders consolidated into `prompts/reasoning.py`
  (7 functions) rather than 7 files. `wait_for_human` is a Phase-3 placeholder;
  the edge to END is provisional.

---

## Phase 3 — Human-in-the-Loop: Intent, Approve/Modify/Unsupported, Mock Execution

- **Status:** NOT STARTED
- **Progress:** 0%
- **Deliverables:**
  - [ ] `agents/hiring/nodes/`: intent_classification, approve, modify, unsupported, mock_execution
  - [ ] Intent classifier + deterministic keyword fallback; `modification_target` mapping (§12)
  - [ ] Modification resume (earliest affected node; downstream-only regen)
  - [ ] `core/execution/`: ats, email, teams adapters + execution logger + failure modelling
  - [ ] Graph edges: Approve→Exec→END; Modify→resume; Unsupported→WAIT
- **Checklist:**
  - [ ] Exactly one intent returned; ambiguous → Unsupported
  - [ ] `modification_target` matches §12; unresolved → Unsupported
  - [ ] Upstream artifacts unchanged after Modify; downstream regenerated
  - [ ] Approve sets `approval_status="approved"` before execution
  - [ ] Mock execution emits Started/Completed + logs; failure path modelled
  - [ ] Keyword classifier works with LLM off
  - [ ] Approve + Modify + Unsupported cycles pass offline
  - [ ] `pytest` green
- **Blockers:** None
- **Notes:**

---

## Phase 4 — Platform Integration: FastAPI, Router, Watcher, Sessions

- **Status:** NOT STARTED
- **Progress:** 0%
- **Deliverables:**
  - [ ] `api/`: main, dependencies, middleware
  - [ ] `api/routes/`: health, hiring (start/resume/get-state); stub engineering/sales/customer_success routers
  - [ ] `core/watcher/`: Watchdog handler → session trigger; input→processing move
  - [ ] Session manager: per-`meeting_id` isolated state; persist operations + approval packages; move to completed; logs
  - [ ] Event emission in specified order
- **Checklist:**
  - [ ] Hiring endpoints: start, resume(message), get-state
  - [ ] Health endpoint ok
  - [ ] Watcher detects file, moves + persists + completes
  - [ ] Session isolation verified with both fixtures
  - [ ] Stub routers prove pluggability (no platform change)
  - [ ] Events logged in order (§15.1)
  - [ ] `pytest` + scripted API E2E pass (fallback mode)
- **Blockers:** None
- **Notes:**

---

## Phase 5 — Gradio UI + End-to-End Validation + Docs

- **Status:** NOT STARTED
- **Progress:** 0%
- **Deliverables:**
  - [ ] `frontend/`: app, pages, components (chat, approval panel, evidence, execution results), assets
  - [ ] UI renders all Approval Package fields; forwards messages; no business logic
  - [ ] `core/renderer/` + `data/templates/` Jinja2 templates
  - [ ] `data/fixtures/expected_outputs/` golden packages (both fixtures)
  - [ ] `README.md` + `data/fixtures/meeting_packages/README.md`
- **Checklist:**
  - [ ] UI renders all §8.2 fields; contains no business logic
  - [ ] Approve / Modify / Unsupported demonstrable from UI
  - [ ] E2E documented; both fixtures pass
  - [ ] Golden expected outputs captured
  - [ ] Demo-safe offline (fallback); live-LLM run confirmed separately
  - [ ] `pytest` green
- **Blockers:** None
- **Notes:**

---

## Change Log

| Date | Phase | Change |
|---|---|---|
| 2026-07-02 | 0 | Planning + bootstrap complete; tracker initialized; all implementation phases NOT STARTED. |
| 2026-07-03 | 1 | Foundations implemented: schemas (incl. `HiringTracker` for the mock ATS), config, common utils, LLM client + deterministic fallback; deps installed + locked; 16 tests pass, ruff clean; all 3 `data/` files validate. Status IN REVIEW pending user sign-off. |
| 2026-07-03 | 1 | Reviewed and approved; committed as Phase 1 (`56e11c2`). |
| 2026-07-03 | 2 | Reasoning pipeline implemented: 10 LangGraph nodes (deterministic + LLM-with-fallback), evidence-first grounding, Operations/Approval package builders, graph compiled with interrupt at WAIT_FOR_HUMAN. Offline strong≠borderline (move_forward vs hold) and live cloud pipeline both pass; 38 tests, ruff clean. Status IN REVIEW pending user sign-off. |
| 2026-07-03 | 2 | Reviewed and approved; committed as Phase 2. |
