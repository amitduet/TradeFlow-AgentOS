"""Run deterministic guardrail approval evals for the Kaggle judge quickstart.

This compatibility entry point delegates to the Sprint 012 approval workflow
eval runner, which covers policy enforcement, approval requests, and audit
events.
"""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.run_approval_workflow_evals import main


if __name__ == "__main__":
    raise SystemExit(main())
