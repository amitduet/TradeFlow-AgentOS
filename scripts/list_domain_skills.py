"""List Sprint 006 domain skills and related runbooks."""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agents.domain_skills import list_available_skills


def main() -> int:
    catalog = list_available_skills()
    for skill in catalog.skills:
        runbooks = ", ".join(skill.related_runbooks)
        print(f"{skill.name} ({skill.version})")
        print(f"  {skill.description}")
        print(f"  Runbooks: {runbooks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
