# AGENTS.md

# Hiring Operations Agent MVP

This file contains the permanent implementation guidelines for this repository.

---

# Project Overview

This repository implements the **Hiring Operations Agent MVP**, which is one domain-specific agent within a larger AI Operations Platform.

The platform architecture consists of:

* **Layer 1:** Meeting Intelligence Platform (Mocked)
* **Layer 2:** AI Operations Agents

Only the **Hiring Operations Agent** is implemented in this MVP.

The architecture must remain generic so additional domain agents can be added without redesigning the platform.

---

# Source of Truth

Before implementing anything, always read and follow these documents:

1. `docs/product_requirements.md`
2. `docs/system_architecture.md`
3. `docs/system_flow.md`

These documents are immutable specifications.

Do not redesign or reinterpret them.

If implementation reveals ambiguity, ask for clarification.

---

# Core Principles

* The Hiring Operations Agent is a **workflow engine**, not a chatbot.
* LangGraph owns workflow orchestration and state.
* FastAPI owns backend APIs.
* Gradio is only a presentation layer simulating Microsoft Teams.
* Business logic belongs only in the backend.
* UI must never contain business logic.
* Components must remain modular and reusable.
* Future domain agents should plug into the same platform without architectural changes.

---

# Workflow Principles

The workflow follows the architecture defined in `system_flow.md`.

Every Meeting Package creates an independent workflow session.

Every workflow produces:

* Operations Package (internal)
* Approval Package (human-facing)

The Approval Package is the source of truth for user approvals.

The workflow pauses for human approval before any external action.

---

# Human-in-the-Loop

No external action may occur automatically.

Examples include:

* Sending emails
* Updating trackers
* Scheduling interviews
* Sending Teams notifications

All such actions require explicit approval.

The MVP performs mock execution only.

---

# Supported User Intents

Only the following workflow interactions are supported:

* Approve
* Modify
* Unsupported

Unsupported requests should be rejected with an explanation instead of attempting open-ended conversation.

---

# Development Principles

* Follow schema-first development.
* Use structured outputs for all LLM interactions.
* Validate all structured outputs.
* Keep modules focused on a single responsibility.
* Prefer composition over tightly coupled implementations.
* Maintain clean separation between platform infrastructure and domain logic.
* Do not introduce unnecessary abstractions.
* Stop and ask before making architectural changes.

---

# Implementation Guidelines

* Implement milestone by milestone.
* Keep commits small and reviewable.
* Preserve folder structure defined in `system_architecture.md`.
* Keep runtime behavior aligned with `system_flow.md`.
* Do not implement functionality outside the approved scope.

The objective is to implement the agreed architecture—not redesign it.
