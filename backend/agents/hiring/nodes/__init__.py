"""The 10 linear pipeline nodes (Context Validation → Approval Package
Generation). Node identifiers registered in the graph are authoritative and
must match ``system_flow.md`` §7 / Diagram 3."""

from backend.agents.hiring.nodes.action_planning import action_planning_node
from backend.agents.hiring.nodes.approval_package_generation import (
    approval_package_generation_node,
)
from backend.agents.hiring.nodes.approve import approve_node
from backend.agents.hiring.nodes.base import get_llm_client, set_llm_client
from backend.agents.hiring.nodes.context_analysis import context_analysis_node
from backend.agents.hiring.nodes.context_validation import context_validation_node
from backend.agents.hiring.nodes.decision_synthesis import decision_synthesis_node
from backend.agents.hiring.nodes.draft_generation import draft_generation_node
from backend.agents.hiring.nodes.evidence_graph_construction import (
    evidence_graph_construction_node,
)
from backend.agents.hiring.nodes.intent_classification import (
    intent_classification_node,
)
from backend.agents.hiring.nodes.issue_identification import issue_identification_node
from backend.agents.hiring.nodes.mock_execution import mock_execution_node
from backend.agents.hiring.nodes.modify import modify_node
from backend.agents.hiring.nodes.operational_assessment import (
    operational_assessment_node,
)
from backend.agents.hiring.nodes.operations_package_generation import (
    operations_package_generation_node,
)
from backend.agents.hiring.nodes.unsupported import unsupported_node

__all__ = [
    # linear pipeline (Phase 2)
    "context_validation_node",
    "context_analysis_node",
    "evidence_graph_construction_node",
    "issue_identification_node",
    "operational_assessment_node",
    "decision_synthesis_node",
    "action_planning_node",
    "draft_generation_node",
    "operations_package_generation_node",
    "approval_package_generation_node",
    # resume half (Phase 3)
    "intent_classification_node",
    "approve_node",
    "modify_node",
    "unsupported_node",
    "mock_execution_node",
    # helpers
    "get_llm_client",
    "set_llm_client",
]
