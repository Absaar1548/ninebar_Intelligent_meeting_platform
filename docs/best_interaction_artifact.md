# Best agent–user interaction (steering artifact)

One end-to-end example of steering an AI coding agent (Claude Code) to a real
feature: **switching the LLM provider/mode at runtime from the UI, with Azure
OpenAI support, and Mock as the default.** It shows *how I directed the work* —
demanding a plan, making the product/safety calls, and refining the result —
rather than just accepting generated code.

> Condensed and redacted from the actual session. `…` marks trimmed content; no
> secrets are shown. The point is the **steering**, not the raw output.

---

### 1. I set the goal — and blocked implementation until there was a plan

> **Me:** Move all docker files into a proper `docker/` folder. Then edit the UI
> to add the LLM key and switch LLM mode to cloud with this key — but I need
> compatibility with **AzureOpenAI** keys as well. For this I need a **detailed
> plan before any changes or execution.**

Steering choice: *plan-first*. I didn't want code yet — I wanted to see the
approach and catch bad decisions cheaply. The agent entered plan mode and
researched the existing LLM layer instead of guessing.

**Agent (summarized):** Found that the provider seam already existed
(`LLMProvider` protocol; `LLMClient` hardcodes Ollama) and that nodes fetch the
client at call-time — so a provider could be added without redesign, and a
running client could be swapped. It also flagged the architecture rule that the
**UI must hold no business logic**, so the switch had to be a backend endpoint.

### 2. I made the product/safety decisions the agent surfaced

The agent didn't decide these for me — it asked, and I chose:

| Decision | My call | Why |
|---|---|---|
| Docker file location | `docker/` folder | Least disruptive; folder already existed |
| How the entered key is held | **In memory only** | No secret written to disk or logged; `.env` stays the persistent path |

Judgment I applied and told it to honour: **reuse the existing provider
abstraction — do not redesign**; add Azure with **no new dependency**; keep all
validation server-side; never log or echo the key.

### 3. I reviewed the plan, then let it implement

After I approved the plan, the agent implemented against it:
- `AzureOpenAIProvider` (hand-rolled `httpx`, `api-key` header, deployment-in-URL)
  next to the Ollama provider, selected by a `build_provider()` factory.
- A backend `LLMRuntime` service + `GET/PUT /api/v1/llm/config` that rebuilds and
  swaps the shared client; keys returned **masked** (booleans only).
- A UI settings panel that only forwards fields to that endpoint.
- Tests for the provider and the config API; full suite green.

### 4. I refined the result into better UX

Reviewing the running UI, I steered a simplification:

> **Me:** In the provider setting have **Mock** as an option as well, **with
> default**. Can use Ollama or Azure if you want.

**Agent (summarized):** Recognized that "Mock" is exactly the existing
deterministic offline path, unified the two controls into a **single Provider
dropdown** (Mock = default, Ollama, Azure), dropped the now-redundant Mode
dropdown, made the app default to Mock so it runs keyless, and updated the
backend/tests/docs to match. Verified by rebuilding the container and confirming
`GET /api/v1/llm/config` reported `provider: mock`.

---

### Outcome

A real, shipped capability: **pick Mock / Ollama Cloud / Azure OpenAI at runtime
from the UI**, keyless by default, keys held in memory only — added *without*
changing the approved architecture, and covered by tests.

### What this shows about my use of AI

- I used the agent for speed and breadth, but **kept the decisions**: plan-first,
  the safety model for secrets, the "reuse the seam, don't redesign" constraint,
  and the final UX simplification.
- The agent's value was strongest when pointed at a **well-scoped change against a
  known architecture**; my value was in **scoping, deciding, and reviewing**.
