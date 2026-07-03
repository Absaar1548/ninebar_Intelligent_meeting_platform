# Meeting Package Fixtures

Pre-generated **Meeting Packages** — the input contract produced by the (mocked)
Layer 1 Meeting Intelligence Platform and consumed by the Hiring Operations
Agent. Each is a standardized interview record: metadata, participants,
transcript, and a `payload` (candidate profile, role/JD, tracker context,
interview context). Schema: [`backend/schemas/meeting_package.py`](../../../backend/schemas/meeting_package.py).

| File | Candidate | Scenario | Expected recommendation (offline) |
|---|---|---|---|
| `meeting_package_strong.json` | Absaar Ali | Round-2 technical + system design; deep, evidence-backed answers across all four must-haves (multi-agent orchestration, production GenAI at scale, evaluation, leadership). | **move_forward** |
| `meeting_package_borderline.json` | Meera Krishnan | Same round; strong on RAG/evaluation but *disclaims* depth on multi-agent orchestration and production governance; up-levelling Senior→Lead. | **hold** |

The two fixtures are deliberately contrasting so the agent's reasoning produces
**different** operational outcomes. The deterministic (offline) outcomes are
locked by the goldens in [`../expected_outputs/`](../expected_outputs/) and the
`test_golden.py` regression test.

> Drop either file into `data/runtime/input/` (with the backend running) to
> trigger a session via the File Watcher, or start one from the Gradio UI.
