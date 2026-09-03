#!/usr/bin/env python3
"""Which skills a Cook round walks, in which order, and whether they resolve.

Cook owns the ordering and nothing else. Each step is a name, a pointer and one
line saying why it is there; the rules live in the skill being pointed at. A
step that carried the routed skill's doctrine would put the same rules in two
places, which is the duplication this router exists to remove.

Resolution is a real check against a real skills directory. `zoom-out` in
particular is in no install manifest today (R-43), so a clean host resolves two
of these three and a route that assumed otherwise would be fiction.
"""
from __future__ import annotations

from pathlib import Path

SKILLS = Path.home() / ".claude" / "skills"

# name -> why this step is in the route. One line each, on purpose.
ROUTE = (
    ("zoom-out", "map the area before touching it, so a fix lands in the right place"),
    ("diagnosing-bugs", "reproduce and localise before proposing a cause"),
    ("ponytail-review", "cut what the fix did not need, before the release boundary"),
)

TERMINAL = ("reviewed commit and push, only after the user confirms; "
            "cook reports the boundary and never crosses it")


def resolve(skills_root: Path) -> dict:
    """The route, with each step's installed path if it has one.

    A directory without a `SKILL.md` has not resolved: an empty folder with the
    right name is not an installed skill, and treating it as one is how a route
    goes green against something nobody can run.
    """
    steps = []
    for name, purpose in ROUTE:
        found = skills_root / name / "SKILL.md"
        steps.append({"name": name, "purpose": purpose,
                      "path": str(found.parent) if found.is_file() else "",
                      "resolved": found.is_file()})
    unresolved = [step["name"] for step in steps if not step["resolved"]]
    return {"route": steps, "terminal": TERMINAL, "unresolved": unresolved,
            "skillsRoot": str(skills_root),
            "errors": [f"{name} does not resolve under {skills_root}"
                       for name in unresolved],
            "passed": not unresolved}
