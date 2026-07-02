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
| 1 | Foundations: Contracts, Config, LLM + Deterministic Fallback | NOT STARTED | 0% |
| 2 | LangGraph Reasoning Pipeline (→ WAIT_FOR_HUMAN) | NOT STARTED | 0% |
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

- **Status:** NOT STARTED
- **Progress:** 0%
- **Deliverables:**
  - [ ] Backend package skeleton per `system_architecture.md` §8
  - [ ] `data/runtime/*` + `data/fixtures/expected_outputs/` + `data/templates/` (with `.gitkeep`)
  - [ ] `schemas/`: meeting_package, operations_package, approval_package, workflow_state, events
  - [ ] `core/common/`: config, logging, ids, json_io, paths
  - [ ] `core/llm/`: base, ollama_provider, fallback_provider, client (retry + validation)
  - [ ] Fixture validation (both packages parse)
  - [ ] `pytest` unit tests (schemas, config, fallback, retry)
- **Checklist:**
  - [ ] Schemas cover §8.1, §8.2, and full WorkflowState (§14.1)
  - [ ] Both fixtures validate; malformed rejected
  - [ ] Config maps all `.env.example` keys; `LLM_MODE` ∈ {cloud, fallback}
  - [ ] Fallback provider produces valid structured output offline
  - [ ] Validator rejects bad output → retry
  - [ ] Folder structure matches §8
  - [ ] `pytest` green
- **Blockers:** None
- **Notes:**

---

## Phase 2 — LangGraph Reasoning Pipeline (→ WAIT_FOR_HUMAN)

- **Status:** NOT STARTED
- **Progress:** 0%
- **Deliverables:**
  - [ ] `agents/hiring/models.py` (InterviewContext, EvidenceGraph, Findings, Assessment, Decision, ActionPlan, Drafts)
  - [ ] `agents/hiring/nodes/` — 10 linear nodes (Context Validation → Approval Package Generation)
  - [ ] `agents/hiring/prompts/` — one prompt per LLM node
  - [ ] `agents/hiring/services/` — operations + approval package generators, evidence enforcement
  - [ ] `agents/hiring/workflow.py` — StateGraph to interrupt at WAIT_FOR_HUMAN
  - [ ] `core/workflow/` — checkpointer, stage transitions, retry integration
  - [ ] Dev runner to execute a fixture to interrupt
- **Checklist:**
  - [ ] Node order/names match Diagram 3 / §7 (no renames)
  - [ ] Each node sets `workflow_stage` per Appendix B
  - [ ] Evidence-first enforced (ungrounded → regenerated)
  - [ ] Interrupt fires at WAIT_FOR_HUMAN; state persists
  - [ ] Full pipeline runs offline (`LLM_MODE=fallback`)
  - [ ] Strong ≠ borderline outcome
  - [ ] Malformed / empty-transcript package → Rejected
  - [ ] `pytest` green
- **Blockers:** None
- **Notes:**

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
