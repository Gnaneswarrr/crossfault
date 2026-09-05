"""Counterfactual Replay Engine for CrossFault."""

import copy
from typing import List

from crossfault.engine import SimulationEngine
from crossfault.models import (
    CounterfactualResult,
    InvestigationReplayResult,
    NetworkCandidate,
    ReplayConfiguration,
    Scenario,
)


class ReplayEngine:
    """
    Orchestrates baseline and counterfactual simulation runs to observe outcomes when
    specific network candidates are disabled.
    """

    @staticmethod
    def _create_isolated_scenario(
        original_scenario: Scenario, disabled_candidate_id: str = None
    ) -> Scenario:
        """Creates a deep copy of the scenario, optionally disabling one candidate."""
        # Deepcopy ensures topology, application_input, and candidate lists are completely isolated
        isolated = copy.deepcopy(original_scenario)

        if disabled_candidate_id:
            # Rebuild candidates list to respect immutability of the frozen dataclass
            new_candidates = []
            for candidate in isolated.candidates:
                if candidate.candidate_id == disabled_candidate_id:
                    # Create new NetworkCandidate instance with is_enabled=False
                    new_candidates.append(
                        NetworkCandidate(
                            candidate_id=candidate.candidate_id,
                            candidate_type=candidate.candidate_type,
                            description=candidate.description,
                            affected_source=candidate.affected_source,
                            affected_destination=candidate.affected_destination,
                            interrupts_path=candidate.interrupts_path,
                            is_enabled=False,
                        )
                    )
                else:
                    new_candidates.append(candidate)
            
            # Since Scenario is frozen, we must use __new__ or object.__setattr__ if we can't instantiate easily.
            # But we can just instantiate a new Scenario cleanly.
            return Scenario(
                scenario_id=isolated.scenario_id,
                name=isolated.name,
                description=isolated.description,
                topology_path=isolated.topology_path,
                candidates=new_candidates,
                application_input=isolated.application_input,
            )

        return isolated

    def run(self, scenario: Scenario, seed: int) -> InvestigationReplayResult:
        """
        Executes the complete investigation:
        1. Baseline run (all candidates enabled as declared).
        2. Counterfactual runs (each candidate disabled exactly once).
        """
        # 1. Baseline run
        baseline_scenario = self._create_isolated_scenario(scenario)
        baseline_engine = SimulationEngine(scenario=baseline_scenario, seed=seed)
        baseline_result = baseline_engine.run()

        counterfactual_results: List[CounterfactualResult] = []

        # 2. Iterate through declared candidates in deterministic order
        for candidate in scenario.candidates:
            # Create completely isolated scenario with only this candidate disabled
            isolated_scenario = self._create_isolated_scenario(
                scenario, disabled_candidate_id=candidate.candidate_id
            )
            
            # Run simulation
            engine = SimulationEngine(scenario=isolated_scenario, seed=seed)
            sim_result = engine.run()

            # Record result
            config = ReplayConfiguration(
                scenario_id=isolated_scenario.scenario_id,
                seed=seed,
                disabled_candidate_id=candidate.candidate_id,
                application_input=isolated_scenario.application_input,
                topology_path=isolated_scenario.topology_path,
                candidates=isolated_scenario.candidates,
            )
            counterfactual_results.append(
                CounterfactualResult(configuration=config, result=sim_result)
            )

        return InvestigationReplayResult(
            scenario_id=scenario.scenario_id,
            seed=seed,
            baseline_result=baseline_result,
            counterfactual_results=counterfactual_results,
        )
