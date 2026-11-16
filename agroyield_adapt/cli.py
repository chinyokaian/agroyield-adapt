"""Command line entry point: ``python -m agroyield_adapt.cli splits ...``"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help"}:
        print(
            "agroyield-adapt - deployment-readiness auditor\n\n"
            "usage:\n"
            "  python -m agroyield_adapt.cli splits --data <panel.csv> [--trees 250]\n"
            "\ncommands:\n"
            "  splits   module 1: split-integrity audit (random vs cluster vs country)\n"
        )
        return 0 if argv else 1

    command, rest = argv[0], argv[1:]
    if command == "splits":
        from .checks.splits import main as splits_main

        return splits_main(rest)
    print(f"unknown command {command!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
