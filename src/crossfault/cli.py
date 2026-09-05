"""Command-line interface for CrossFault simulator."""

import argparse
import io
import json
import sys
from typing import List, Optional

from crossfault.analyzer import CausalAnalyzer
from crossfault.assembler import EvidenceAssembler
from crossfault.formatter import (
    format_causal_analysis,
    format_investigation_summary,
    format_simulation_summary,
    format_verified_evidence,
)
from crossfault.replay import ReplayEngine
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
    
    # Phase 2: Counterfactual Replay Investigation
    replay_engine = ReplayEngine()
    investigation_result = replay_engine.run(scenario=scenario, seed=parsed_args.seed)

    # Phase 3: Causal Analysis
    causal_analyzer = CausalAnalyzer()
    analysis_result = causal_analyzer.analyze(investigation_result)

    # Phase 4: Verified Evidence Assembly
    assembler = EvidenceAssembler()
    verified_evidence = assembler.assemble(investigation_result, analysis_result)

    if parsed_args.json:
        # Output the complete structure
        output = investigation_result.to_dict()
        output["analysis"] = analysis_result.to_dict()
        output["verified_evidence"] = verified_evidence.to_dict()
        print(json.dumps(output, indent=2))
    else:
        # Print Phase 2 summary
        print(format_investigation_summary(investigation_result))
        print("")
        
        # Print Phase 3 causal analysis
        print(format_causal_analysis(analysis_result))
        print("")

        # Print Phase 4 verified evidence path
        print(format_verified_evidence(verified_evidence))
        
        if parsed_args.verbose:
            print("\nDetailed Baseline Event Log:")
            for event in investigation_result.baseline_result.events:
                print(
                    f" [{event.order:02d}] +{event.timestamp_offset_ms:6.2f}ms "
                    f"[{event.status:12s}] {event.service}: {event.message}"
                )

    return 0


if __name__ == "__main__":
    sys.exit(main())
