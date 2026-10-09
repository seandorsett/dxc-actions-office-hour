#!/usr/bin/env python3
"""Assert cache restore behavior in the reusable demo workflow.

Usage: python scripts/cache_probe.py MODE
Prerequisites: a preceding cache restore into .demo-cache/seed.
No credentials or third-party dependencies. Cache verifier handles save results.
"""

import os
from pathlib import Path
import sys

from demo_api import MODES


def main(mode: str) -> None:
    expected = MODES[mode][0]
    marker = Path(".demo-cache/seed/marker.txt")
    observed = marker.exists()
    if observed and marker.read_text(encoding="utf-8").strip() != "trusted-demo-seed":
        raise RuntimeError("Restored cache marker content was not the seeded value.")
    if observed != expected:
        raise RuntimeError(f"{mode}: expected restore={expected}, observed restore={observed}")
    target = Path(".demo-cache/probe")
    target.mkdir(parents=True, exist_ok=True)
    (target / "marker.txt").write_text(f"probe-{mode}\n", encoding="utf-8")
    message = f"## Caller mode: {mode}\n\nExpected restore: **{expected}**. Observed: **{observed}**.\n"
    print(message)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write(message)


if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except (IndexError, KeyError, OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

