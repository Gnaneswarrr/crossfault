"""Command-line interface for CrossFault simulator."""

import argparse
import io
import json
import sys
from typing import List, Optional

from crossfault.engine import SimulationEngine
from crossfault.formatter import format_simulation_summary
from crossfault.scenario import create_initial_scenario


def _configure_utf8_stdout():
    """Ensure stdout handles UTF-8 formatting cleanly across Windows and POSIX terminals."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    elif hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def main(args: Optional[List[str]] = None) -> int:
    _configure_utf8_stdout()

    parser = argparse.ArgumentParser(
        description="CrossFault: Bounded simulator for reconstructing network-induced deployment failures."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=48291,
        help="Random seed for deterministic simulation (default: 48291)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured simulation result as JSON",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed event log trace along with summary",
    )

    parsed_args = parser.parse_args(args)

    scenario = create_initial_scenario()
    engine = SimulationEngine(scenario=scenario, seed=parsed_args.seed)
    result = engine.run()

    if parsed_args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_simulation_summary(result))
        if parsed_args.verbose:
            print("\nDetailed Event Log:")
            for event in result.events:
                print(
                    f" [{event.order:02d}] +{event.timestamp_offset_ms:6.2f}ms "
                    f"[{event.status:12s}] {event.service}: {event.message}"
                )

    return 0


if __name__ == "__main__":
    sys.exit(main())
