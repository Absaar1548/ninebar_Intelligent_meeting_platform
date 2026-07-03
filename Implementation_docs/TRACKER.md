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
| 3 | Human-in-the-Loop: Intent, Approve/Modify/Unsupported, Mock Execution | DONE | 100% |
| 4 | Platform Integration: FastAPI, Router, Watcher, Sessions | DONE | 100% |
| 5 | Gradio UI + End-to-End Validation + Docs | DONE | 100% |

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

- **Status:** DONE (reviewed and approved; committed as Phase 3)
- **Progress:** 100%
- **Deliverables:**
  - [x] `agents/hiring/nodes/`: intent_classification, approve, modify, unsupported, mock_execution
  - [x] Intent classifier LLM node + deterministic keyword fallback (`services/intent.py`); `modification_target` mapping (§12)
  - [x] Modification resume (conditional edge → earliest affected node; downstream-only regen)
  - [x] `core/execution/`: ats/email/teams adapters + engine (simulate + log + failure injection)
  - [x] Graph edges: WAIT→intent; Approve→Exec→END; Modify→resume target; Unsupported→WAIT; `resume()` via `Command(update=...)`
  - [x] Additive schemas: `execution.py`, `IntentClassification`, `execution_results` in state; `MOCK_EXECUTION_FAIL_ADAPTER` config
- **Checklist:**
  - [x] Exactly one intent returned; ambiguous / unresolved-target → Unsupported
  - [x] `modification_target` matches §12; unresolved → Unsupported
  - [x] Upstream artifacts unchanged after Modify; downstream regenerated
  - [x] Approve sets `approval_status="approved"` before execution
  - [x] Mock execution emits Started/Completed + writes log; failure path modelled (fail-injection test)
  - [x] Keyword classifier works with LLM off (offline suite)
  - [x] Approve + Modify + Unsupported cycles pass offline; modify→approve and unsupported→approve chains work
  - [x] `pytest` green (62 passed) + `ruff` clean
- **Blockers:** None
- **Notes:** Resume mechanic validated by a day-1 spike (`Command(update={human_feedback})`
  resumes past `interrupt_before` and routes correctly). Mock execution is
  **simulate + log only** (writes `data/runtime/logs/<meeting_id>.execution.json`;
  `data/hiring_tracker.json` untouched). Live cloud intent classification also
  verified (approve/modify-email/modify-recommendation/unsupported all routed
  correctly).

---

## Phase 4 — Platform Integration: FastAPI, Router, Watcher, Sessions

- **Status:** DONE (reviewed and approved; committed as Phase 4)
- **Progress:** 100%
- **Deliverables:**
  - [x] `api/`: main (`create_app` + lifespan), dependencies, middleware, models
  - [x] `api/routes/`: health, hiring (start/resume/get/list); stub engineering/sales/customer_success routers (501)
  - [x] `core/watcher/`: Watchdog handler + observer + `run` entrypoint; input→processing move
  - [x] Session mgmt: `HiringSessionService` (per-`meeting_id` session) + generic `SessionRegistry`; persist operations + approval packages; move to completed
  - [x] `MeetingPackageCreated` emitted at ingestion; §15.1 events flow through the run/execution engines
- **Checklist:**
  - [x] Hiring endpoints: start, resume(message), get, list
  - [x] Health endpoint ok
  - [x] Watcher detects file, moves + persists + completes (live Observer verified, not just handler)
  - [x] Session isolation verified with both fixtures (independent stages/artifacts)
  - [x] Stub routers prove pluggability (501; no platform change)
  - [x] Events logged in order (§15.1)
  - [x] `pytest` (TestClient) green (76 passed) + `ruff` clean
- **Blockers:** None
- **Notes:** A session is a checkpointer thread (`session_id_for(meeting_id)`);
  the compiled app singleton + InMemorySaver persist state across HTTP requests.
  Watcher triggers the session **in-process** (`create_app(enable_watcher=False)`
  keeps tests observer-free; guarded by `ENABLE_FILE_WATCHER`). Layering kept
  clean: generic session/persistence in `core/workflow/session.py`, hiring
  orchestration in `agents/hiring/session.py`, thin router in `api/`.

---

## Phase 5 — Gradio UI + End-to-End Validation + Docs

- **Status:** DONE (reviewed and approved; committed as Phase 5 — final phase)
- **Progress:** 100%
- **Deliverables:**
  - [x] `frontend/`: app, `pages/chat.py`, `components/renderers.py`, `api_client.py`, assets (root-level, sibling of `backend/`)
  - [x] UI renders all Approval Package fields + execution results; forwards messages over HTTP; no business logic
  - [x] `backend/core/renderer/` + `data/templates/` Jinja2 templates (approval_package, execution)
  - [x] `data/fixtures/expected_outputs/` golden packages (approval + operations, both fixtures)
  - [x] `README.md` + `data/fixtures/meeting_packages/README.md`
  - [x] `SessionView.messages` (additive) surfaces the chat transcript
- **Checklist:**
  - [x] UI renders all §8.2 fields; contains no business logic (pure HTTP client + injected for tests)
  - [x] Approve / Modify / Unsupported demonstrable from UI (handler tests + smokes)
  - [x] E2E documented (README); both fixtures pass (strong→move_forward, borderline→hold)
  - [x] Golden expected outputs captured + regression test (timestamps stripped)
  - [x] Demo-safe offline (fallback); real uvicorn HTTP path verified; live-LLM confirmed in earlier phases
  - [x] `pytest` green (87 passed) + `ruff` clean (backend + frontend)
- **Blockers:** None
- **Notes:** UI is a pure HTTP client of the FastAPI backend; rendering lives in
  `backend/core/renderer` (Jinja2). Gradio telemetry disabled (no external calls
  offline). Verified against the real app via `TestClient` and a live uvicorn TCP
  server. **Review-driven refinements** (also in this phase): recommendation moved
  into the chat with the right panel repurposed to an "Internal Processing &
  Memory" view; evidence citations now carry backfilled quotes (self-resolving);
  a **live per-node progress tracker** for slow cloud runs (UI polls
  `GET /sessions/{id}`, which reads live checkpointer state; `LLM_TIMEOUT_SECONDS`
  raised to 150 to avoid a needless timeout+retry); and **modifications now apply
  the human's instruction** (the reviewer's request is injected into the
  resume-target node's prompt). 92 tests pass, ruff clean; verified live in cloud.

---

## Final Readiness Checklist (product_requirements.md §13)

All six MVP success criteria are demonstrated end to end:

- [x] **End-to-end workflow execution** — Meeting Package → Operations + Approval Package → approval → mock execution → complete (offline and live).
- [x] **Explainable reasoning** — every node emits an inspectable artifact; the chat narrates each stage.
- [x] **Evidence-backed recommendations** — findings/decision carry `evidence_refs`; a grounding validator rejects ungrounded output (`test_evidence_enforcement`).
- [x] **Human approval before execution** — the graph interrupts at `WAIT_FOR_HUMAN`; no adapter runs without an Approve intent.
- [x] **Stateful workflow management** — per-`meeting_id` isolated LangGraph state with interrupt/resume; session isolation tested.
- [x] **Operational artifact generation** — Operations Package (internal) + Approval Package (source of truth), persisted under `data/runtime/`.
- [x] **Mock downstream execution** — ATS / email / Teams adapters simulate + log; failure path modelled.

**Test suite:** 87 passing, offline, no network. **Lint:** ruff clean.

---

## Change Log

| Date | Phase | Change |
|---|---|---|
| 2026-07-02 | 0 | Planning + bootstrap complete; tracker initialized; all implementation phases NOT STARTED. |
| 2026-07-03 | 1 | Foundations implemented: schemas (incl. `HiringTracker` for the mock ATS), config, common utils, LLM client + deterministic fallback; deps installed + locked; 16 tests pass, ruff clean; all 3 `data/` files validate. Status IN REVIEW pending user sign-off. |
| 2026-07-03 | 1 | Reviewed and approved; committed as Phase 1 (`56e11c2`). |
| 2026-07-03 | 2 | Reasoning pipeline implemented: 10 LangGraph nodes (deterministic + LLM-with-fallback), evidence-first grounding, Operations/Approval package builders, graph compiled with interrupt at WAIT_FOR_HUMAN. Offline strong≠borderline (move_forward vs hold) and live cloud pipeline both pass; 38 tests, ruff clean. Status IN REVIEW pending user sign-off. |
| 2026-07-03 | 2 | Reviewed and approved; committed as Phase 2. |
| 2026-07-03 | 3 | Human-in-the-loop implemented: intent classification (LLM + keyword fallback), Approve→mock execution→END, Modify→resume at earliest affected node, Unsupported→stay waiting; mock execution engine (ats/email/teams, simulate+log, failure injection); `resume()` via Command(update). 62 tests, ruff clean; offline approve/modify/unsupported + live intent verified. Status IN REVIEW pending user sign-off. |
| 2026-07-03 | 3 | Reviewed and approved; committed as Phase 3. |
| 2026-07-03 | 4 | Platform integration implemented: FastAPI gateway (create_app + lifespan), hiring router (start/resume/get/list) + health + pluggable agent stubs (501), Watchdog File Watcher (input→processing→completed), HiringSessionService + generic SessionRegistry/persistence. 76 tests (TestClient) pass, ruff clean; live Observer + API smokes verified. Status IN REVIEW pending user sign-off. |
| 2026-07-03 | 4 | Reviewed and approved; committed as Phase 4. |
| 2026-07-03 | 5 | Final phase implemented: Gradio Teams-chat UI (root `frontend/`, pure HTTP client), `backend/core/renderer` + Jinja2 templates, `SessionView.messages`, golden expected outputs + regression test, README + fixtures README. 87 tests pass, ruff clean; UI verified via TestClient and a live uvicorn server. Final Readiness Checklist ticked. Status IN REVIEW pending user sign-off. |
| 2026-07-03 | 5 | Review-driven UI/UX refinements: chat-first recommendation + "Internal Processing & Memory" panel; evidence citations carry backfilled quotes; live per-node progress tracker (UI polls checkpointer state) + LLM_TIMEOUT_SECONDS→150; modifications now apply the reviewer's instruction (revision injected into the resume-target prompt). 92 tests pass, ruff clean; fallback + live cloud verified end-to-end. |
| 2026-07-03 | 5 | Reviewed and approved; committed as Phase 5 — MVP complete. |
