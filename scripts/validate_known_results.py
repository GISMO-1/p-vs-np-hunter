from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.lower_bound_hunter.agent import LowerBoundHunterAgent


def main() -> int:
    hunter = LowerBoundHunterAgent()
    report = hunter.validate_known_results()
    print("Known-result validation checks:", report.checks)
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
