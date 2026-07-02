"""Pytest bootstrap.

Ensures the repository root is on ``sys.path`` so tests can import the
``backend`` package with ``from backend.schemas import ...`` regardless of the
directory pytest is invoked from. Keeps the project to the folder layout in
``docs/system_architecture.md`` §8 without introducing a packaging file.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
