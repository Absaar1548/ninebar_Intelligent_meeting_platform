"""Mock execution engine — simulated downstream enterprise integrations."""

from backend.core.execution.engine import ADAPTERS, execute

__all__ = ["execute", "ADAPTERS"]
