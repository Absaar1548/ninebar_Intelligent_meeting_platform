"""Checkpointer factory.

The MVP uses LangGraph's in-memory saver, which is enough for local, single-
process interrupt/resume. Production swaps this for a persistent saver
(e.g. Postgres) with no change to the graph or nodes.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver


def get_checkpointer() -> InMemorySaver:
    return InMemorySaver()
