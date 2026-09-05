"""Network change evaluator for CrossFault simulator."""

from typing import List, Optional, Tuple
from crossfault.models import NetworkCandidate


class NetworkEvaluator:
    """Evaluates candidate network changes against service communication hops."""

    def __init__(self, candidates: List[NetworkCandidate]):
        self._candidates = list(candidates)

    def evaluate_hop(self, source: str, destination: str) -> Optional[NetworkCandidate]:
        """
        Evaluates active candidate network changes against a communication hop.
        Returns the NetworkCandidate that interrupts the hop, or None if the hop succeeds.
        """
        for candidate in self._candidates:
            if not candidate.is_enabled:
                continue

            if not candidate.interrupts_path:
                continue

            # Direct link match
            if candidate.affected_source == source and candidate.affected_destination == destination:
                return candidate

            # Node match (if candidate interrupts all traffic to/from affected_destination or affected_source)
            if candidate.affected_destination == destination and candidate.affected_source is None:
                return candidate

            if candidate.affected_source == source and candidate.affected_destination is None:
                return candidate

        return None
