# Hiring Operations Agent — MVP

An AI-native **Hiring Operations Agent**: one pluggable domain agent within a
larger AI Operations Platform. Unlike assistants that stop at transcripts or
summaries, it performs **operational reasoning** over a standardized interview
record, prepares evidence-backed work products, and collaborates with a human
through an **approval-first** workflow.

Given a **Meeting Package** (the output of a — here mocked — Meeting Intelligence
Platform), the agent runs a LangGraph workflow that analyzes the interview,
builds an evidence graph, identifies findings, assesses suitability, synthesizes
a recommendation, plans actions, drafts communications, and then **pauses for
human approval** before simulating any downstream action.

> This MVP is one complete vertical slice of a multi-agent platform. It is
> production-*oriented* in architecture; infrastructure is mocked, architecture
> is not.

---

## Architecture at a glance

```
Layer 1 (mocked)                Layer 2 (implemented)
Meeting Intelligence   ──▶  Hiring Operations Agent (LangGraph)  ──▶  Mock
Platform → Meeting          Operations Package → Approval Package        Enterprise
Package (JSON)              → Human Approval → Mock Execution             Integrations

Ingestion            Backend (FastAPI + LangGraph)             Presentation
File Watcher   ─▶   API Gateway → Hiring Router → Workflow  ─▶  Gradio (Teams sim)
```

**Workflow pipeline** (each node produces one inspectable artifact):

```
Context Validation → Context Analysis → Evidence Graph → Issue Identification →
Operational Assessment → Decision Synthesis → Action Planning → Draft Generation →
Operations Package → Approval Package → [WAIT_FOR_HUMAN] → Intent Classification →
{ Approve → Mock Execution → END | Modify → resume at earliest affected node | Unsupported }
```

Design principles: **workflow engine, not a chatbot**; **evidence-first** (no
recommendation without evidence references); **human-in-the-loop** (no external
action without explicit approval); **schema-first** data contracts; **pluggable**
domain agents. The full specs live in [`docs/`](docs/) — product requirements,
system architecture, and the node-by-node system flow — and the engineering plan
in [`Implementation_docs/`](Implementation_docs/).

## Project structure

```
backend/
  api/         FastAPI gateway, routers (hiring + health + agent stubs), DTOs
  agents/hiring/  workflow, nodes, prompts, services (reasoner/evidence/builders), session
  core/        common (config/logging/io), llm (client + fallback), workflow,
               execution (mock adapters), watcher (file watcher), renderer (Jinja2)
  schemas/     Pydantic data contracts (meeting/operations/approval, state, events)
  tests/       pytest suite (offline)
frontend/      Gradio Teams-chat simulation (HTTP client of the backend)
data/          fixtures (meeting packages, expected outputs), runtime dirs, templates
docs/          immutable product/architecture/flow specs
```

## Setup

Requires **Python 3.12**.

```bash
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# bash/Git Bash:       source .venv/Scripts/activate
pip install -r requirements.txt          # or requirements.lock for exact pins
cp .env.example .env                      # PowerShell: Copy-Item .env.example .env
```

Edit `.env` and set `OLLAMA_API_KEY` for live reasoning (the only real secret).
`.env` is gitignored.

### LLM modes

| `LLM_MODE` | Behaviour |
|---|---|
| `cloud` (default) | Reasoning nodes call the Ollama Cloud API; each output is schema-validated with bounded retry. On failure they **degrade to the deterministic fallback** (`LLM_FALLBACK_ENABLED=true`). |
| `fallback` | No network: a deterministic, rule-based reasoner runs the whole pipeline. Used for offline dev, CI, and demos. |

Every node has a deterministic fallback, so the system runs end-to-end with **no
key and no network**.

## Running

Open two terminals (backend + UI):

```bash
# 1) Backend API (starts the File Watcher too)
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000

# 2) Gradio UI  → http://127.0.0.1:7860
python -m frontend.app
```

Optional — run the File Watcher standalone: `python -m backend.core.watcher.run`,
then drop a fixture into `data/runtime/input/`.

**Use it:** in the UI, pick a Meeting Package and **Start session**. Review the
Approval Package, then reply in chat:
- `approve` → the agent runs mock execution (ATS update, candidate email, Teams
  notification) and completes;
- `rewrite the email` / `change the recommendation` / `remove the tracker update`
  → the workflow resumes at the earliest affected node, regenerates downstream,
  and returns for approval;
- anything off-topic → politely declined (workflow stays paused).

### API (without the UI)

```bash
curl -X POST localhost:8000/api/v1/agents/hiring/sessions \
  -H 'content-type: application/json' \
  -d "{\"meeting_package\": $(cat data/fixtures/meeting_packages/meeting_package_strong.json)}"
# → { session_id, workflow_stage: "waiting_approval", approval_package, ... }

curl -X POST localhost:8000/api/v1/agents/hiring/sessions/<id>/messages \
  -H 'content-type: application/json' -d '{"message":"approve"}'
```

Runtime artifacts are written under `data/runtime/` (`operations/`, `approvals/`,
`logs/`); processed input files move `input → processing → completed`.

## Testing

```bash
python -m pytest backend/tests -q      # full suite, offline (no network)
python -m ruff check backend frontend  # lint
```

The suite covers schemas, the LLM client + fallback, every workflow node, the
full pipeline (strong ≠ borderline), human-in-the-loop (approve/modify/
unsupported), mock execution, the API, the File Watcher, the renderer, the UI
handlers, and a **golden** regression on the deterministic output.

## MVP → production mapping

| MVP | Production |
|---|---|
| File Watcher | Event bus (Kafka / Service Bus / Event Grid) |
| Local JSON storage + InMemorySaver | Database / object storage + persistent checkpointer |
| Gradio Teams simulation | Microsoft Teams |
| Mock execution adapters | Enterprise APIs (ATS, email, calendar, Slack, Teams) |
| Single implemented agent | Multiple domain agents (register a router — see the 501 stubs) |

Simplifications replace **infrastructure only**; the architecture is unchanged.
