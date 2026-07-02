# SYSTEM_ARCHITECTURE.md

# Hiring Operations Agent MVP

**Version:** 1.0  
**Status:** Final Draft

---

# 1. Purpose

This document defines the technical architecture for the Hiring Operations Agent MVP.

It serves as the engineering source of truth for implementation.

The architecture intentionally separates **business logic**, **workflow orchestration**, **platform infrastructure**, and **presentation** so the MVP can evolve into a production AI Operations Platform without architectural redesign.

---

# 2. Architecture Philosophy

The Hiring Operations Agent is **not a chatbot**.

It is an AI-native **workflow engine** built using LangGraph.

The Gradio chat interface simply provides one method for humans to interact with the workflow.

The MVP implements only one domain agent (Hiring Operations Agent), but the platform is designed to support multiple independent Operations Agents in the future.

Examples include:

- Hiring Operations
- Engineering Operations
- Sales Operations
- Customer Success Operations
- Executive Operations

The architecture follows the following principles:

- Modular
- Event Driven
- Human-in-the-Loop
- Schema First
- Explainable AI
- Production Oriented

Infrastructure may be mocked.

Architecture must not be.

---

# 3. High Level Architecture

```
                   AI OPERATIONS PLATFORM

┌─────────────────────────────────────────────────────┐
│                 Layer 1 (Mocked)                    │
│         Meeting Intelligence Platform               │
│                                                     │
│  • Meeting Capture                                 │
│  • Transcript Generation                           │
│  • Context Assembly                                │
│  • Meeting Package Generation                      │
└─────────────────────────────────────────────────────┘

                       │

                       ▼

              Meeting Package (JSON)

                       │

──────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────┐
│               Layer 2 (Implemented)                 │
│            Hiring Operations Agent                  │
└─────────────────────────────────────────────────────┘

                       │

                 LangGraph Workflow

                       │

                       ▼

              Operations Package (JSON)

                       │

                       ▼

              Approval Package (JSON)

                       │

                       ▼

             Teams Chat Simulation (Gradio)

                       │

                       ▼

                 Human Approval

                       │

                       ▼

             Mock Enterprise Integrations
```

---

# 4. Architectural Boundaries

## Layer 1 — Meeting Intelligence Platform

Status

Mocked.

Responsibilities

- Meeting ingestion
- Transcript generation
- Speaker identification
- Context assembly
- Meeting Package generation

Output

Meeting Package JSON.

---

## Layer 2 — AI Operations Platform

Responsible for:

- Workflow orchestration
- Operational reasoning
- Evidence-backed decisions
- Action generation
- Human approval
- Execution orchestration

This MVP implements only the Hiring Operations Agent.

---

# 5. Core Components

## 5.1 File Watcher

Responsibilities

- Monitor runtime input directory
- Detect new Meeting Packages
- Trigger workflow execution

Production Equivalent

- Kafka
- Azure Service Bus
- RabbitMQ
- Event Grid

---

## 5.2 FastAPI Gateway

Acts as the backend entry point.

Responsibilities

- Route requests
- Create workflow sessions
- Expose agent endpoints
- Manage API lifecycle

Future agents register new routers without changing platform architecture.

Example

```
/api/v1/agents/hiring

/api/v1/agents/engineering

/api/v1/agents/sales
```

---

## 5.3 Hiring Agent Router

Responsibilities

- Receive Meeting Package
- Create workflow instance
- Start Hiring Agent
- Resume workflow
- Return workflow state

---

## 5.4 LangGraph Workflow Engine

Core orchestration engine.

Responsibilities

- Workflow execution
- Stateful execution
- Interrupt / Resume
- Human Approval
- Memory
- Session Management

Every interview becomes an independent workflow.

---

## 5.5 Workflow State

Each Meeting Package owns its own state.

State includes

- Meeting Package
- Operations Package
- Approval Package
- Current Workflow Stage
- Pending Approval
- Human Feedback
- Execution Status

Workflow state persists until completion.

---

## 5.6 Intent Classifier

Every incoming user message first passes through an intent classifier.

Supported intents

- Approval
- Modification
- Unsupported

The classifier determines which workflow node executes next.

---

## 5.7 Operations Package Generator

Produces the internal reasoning artifact.

Contains

- Context Analysis
- Evidence Graph
- Findings
- Assessment
- Decisions
- Action Plan
- Draft Communications

Not user editable.

---

## 5.8 Approval Package Generator

Creates the human-facing workflow artifact.

Stored as JSON.

Rendered by the UI.

Acts as the approval source of truth.

Contains

- Executive Summary
- Recommendation
- Confidence
- Evidence
- Decisions
- Action Items
- Draft Email
- Tracker Updates
- Approval Status
- Human Comments
- Execution Status

---

## 5.9 Gradio UI

Acts as a Teams Chat simulation.

Responsibilities

- Display workflow analysis
- Display evidence
- Display recommendations
- Display approval requests
- Accept user interaction

Business logic remains entirely in the backend.

---

## 5.10 Mock Execution Engine

Simulates downstream enterprise systems.

Includes

- ATS Update
- Candidate Email
- Teams Notification
- Execution Logs

Production replaces these adapters with real integrations.

---

# 6. Workflow Pipeline

The Hiring Operations Agent executes the following pipeline.

```
Meeting Package

↓

Context Validation

↓

Context Analysis

↓

Evidence Graph Construction

↓

Issue Identification

↓

Operational Assessment

↓

Decision Synthesis

↓

Action Planning

↓

Draft Generation

↓

Operations Package

↓

Approval Package
```

Each stage produces a structured artifact.

Artifacts become inputs for downstream stages.

---

# 7. Data Contracts

The system defines three primary contracts.

## Meeting Package

Input Contract.

Produced by Layer 1.

Contains

- Metadata
- Transcript
- Participants
- Candidate Profile
- Job Description
- Tracker Context
- Interview Context

Immutable.

---

## Operations Package

Internal Contract.

Contains

- Context Analysis
- Evidence Graph
- Findings
- Assessment
- Decisions
- Action Plan
- Draft Communications

Generated only by the agent.

---

## Approval Package

Human Interaction Contract.

Contains

- Recommendation
- Confidence
- Decisions
- Action Items
- Draft Email
- Tracker Updates
- Human Feedback
- Approval Status
- Execution Status

Stored as JSON.

Rendered in UI.

Source of truth for workflow approval.

---

# 8. Project Structure

```
project/

├── backend/
│
│   ├── api/
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   ├── middleware.py
│   │   └── routes/
│   │       ├── hiring.py
│   │       ├── engineering.py
│   │       ├── sales.py
│   │       ├── customer_success.py
│   │       └── health.py
│   │
│   ├── core/
│   │   ├── workflow/
│   │   ├── llm/
│   │   ├── execution/
│   │   ├── watcher/
│   │   ├── renderer/
│   │   └── common/
│   │
│   ├── agents/
│   │   ├── hiring/
│   │   │   ├── workflow.py
│   │   │   ├── nodes/
│   │   │   ├── prompts/
│   │   │   ├── services/
│   │   │   └── models.py
│   │   │
│   │   ├── engineering/
│   │   ├── sales/
│   │   └── customer_success/
│   │
│   ├── schemas/
│   │   ├── meeting_package.py
│   │   ├── operations_package.py
│   │   ├── approval_package.py
│   │   ├── workflow_state.py
│   │   └── events.py
│   │
│   └── tests/
│
├── frontend/
│   ├── app.py
│   ├── pages/
│   ├── components/
│   └── assets/
│
├── data/
│   ├── fixtures/
│   │   ├── meeting_packages/
│   │   │   ├── meeting_package_strong.json
│   │   │   ├── meeting_package_borderline.json
│   │   │   └── README.md
│   │   └── expected_outputs/
│   │
│   ├── runtime/
│   │   ├── input/
│   │   ├── processing/
│   │   ├── operations/
│   │   ├── approvals/
│   │   ├── completed/
│   │   └── logs/
│   │
│   └── templates/
│
├── docs/
│
├── requirements.txt
│
├── README.md
│
└── .env
```

---

# 9. Technology Stack

Backend

- Python

API Framework

- FastAPI

Workflow Engine

- LangGraph

Frontend

- Gradio

LLM

- Ollama Cloud API

Validation

- Pydantic

Templates

- Jinja2

File Monitoring

- Watchdog

Logging

- Rich

---

# 10. Session Management

Each Meeting Package creates an independent workflow session.

Workflow State

```
meeting_id

↓

workflow_state

↓

operations_package

↓

approval_package

↓

execution_status
```

LangGraph manages workflow persistence.

Workflow memory is scoped per interview.

No conversational memory exists in the MVP.

---

# 11. Intent Routing

Every user interaction follows the same pipeline.

```
User Message

↓

Intent Classifier

↓

Approve

↓

Modify

↓

Unsupported
```

Approve

Workflow resumes.

Modify

Approval Package updates.

Unsupported

Reject request.

---

# 12. Production Equivalence

| MVP | Production |
|------|------------|
| File Watcher | Event Bus |
| Local JSON | Database / Object Storage |
| Gradio Chat | Microsoft Teams |
| Mock Integrations | Enterprise APIs |
| Local Workflow | Distributed LangGraph Services |
| Single Agent | Multiple Domain Agents |

---

# 13. Architectural Decisions

The following architectural decisions are mandatory.

- The agent is a workflow engine.
- The UI is only a presentation layer.
- Business logic exists only in backend services.
- Every recommendation requires evidence.
- Every external action requires human approval.
- Every workflow owns independent state.
- Data contracts are schema-first.
- Components remain pluggable.
- Future domain agents require no platform redesign.

---

# 14. MVP Simplifications

The following simplifications intentionally reduce infrastructure while preserving architecture.

- Layer 1 mocked.
- Pre-generated Meeting Packages.
- Local file watcher.
- Local JSON storage.
- Single user.
- Single implemented domain agent.
- Mock Teams UI.
- Mock enterprise integrations.
- Local workflow execution.
- No authentication.
- No authorization.

These simplifications replace infrastructure only.

The production architecture remains unchanged.

---

# 15. Future Expansion

Future enhancements include:

Layer 1

- Live Meeting Intelligence Platform
- Meeting Bots
- Live Speech Processing
- Context Assembly

Layer 2

- Engineering Operations Agent
- Sales Operations Agent
- Customer Success Operations Agent
- Executive Operations Agent

Execution Layer

- ATS
- Microsoft Teams
- Calendar
- Email
- Slack

Platform

- Multi-user support
- Authentication
- Authorization
- Distributed workflow execution
- Persistent storage
- Observability
- Metrics
- Monitoring