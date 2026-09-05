"""Deterministic Simulation Engine for CrossFault."""

import random
from typing import List, Optional

from crossfault.models import (
    DeploymentStatus,
    EventType,
    NetworkCandidate,
    Scenario,
    SimulationEvent,
    SimulationResult,
)
from crossfault.network import NetworkEvaluator
from crossfault.topology import ServiceTopology


class SimulationEngine:
    """
    Bounded simulation engine for reconstructing network-induced deployment failures.
    
    Guarantees strict determinism by using a seeded Python random.Random generator instance
    owned entirely by the simulation context.
    """

    def __init__(self, scenario: Scenario, seed: int = 48291):
        self.scenario = scenario
        self.seed = seed
        self._rng = random.Random(seed)
        self._order_counter = 0
        self._current_time_ms = 0.0
        self._events: List[SimulationEvent] = []

    def _next_event_id(self) -> str:
        # Purely sequential and deterministic event ID
        return f"EV-{self._order_counter:03d}"

    def _log_event(
        self,
        event_type: EventType,
        service: str,
        message: str,
        status: str = "INFO",
        source_service: Optional[str] = None,
        destination_service: Optional[str] = None,
        candidate_id: Optional[str] = None,
    ) -> SimulationEvent:
        self._order_counter += 1
        # Add deterministic jitter to timestamp
        self._current_time_ms += round(self._rng.uniform(12.5, 28.0), 2)
        event = SimulationEvent(
            event_id=self._next_event_id(),
            order=self._order_counter,
            timestamp_offset_ms=self._current_time_ms,
            service=service,
            event_type=event_type,
            message=message,
            candidate_id=candidate_id,
            source_service=source_service,
            destination_service=destination_service,
            status=status,
        )
        self._events.append(event)
        return event

    def run(self) -> SimulationResult:
        """Executes the scenario deterministically and returns structured SimulationResult."""
        self._order_counter = 0
        self._current_time_ms = 0.0
        self._events.clear()

        topology = ServiceTopology(self.scenario.topology_path)
        evaluator = NetworkEvaluator(self.scenario.candidates)

        # 1. Deployment Start Event
        self._log_event(
            event_type=EventType.DEPLOYMENT_START,
            service=topology.path[0],
            message=f"Deployment initiated for scenario '{self.scenario.scenario_id}' with seed {self.seed}.",
            status="INFO",
        )

        # 2. Log Candidate Network Events Evaluation
        for candidate in self.scenario.candidates:
            eval_msg = f"Candidate network change evaluated: [{candidate.candidate_type.value}] {candidate.description}"
            self._log_event(
                event_type=EventType.NETWORK_EVENT_EVALUATION,
                service=candidate.affected_source or topology.path[0],
                message=eval_msg,
                candidate_id=candidate.candidate_id,
                source_service=candidate.affected_source,
                destination_service=candidate.affected_destination,
                status="INTERRUPTING" if candidate.interrupts_path else "PASS",
            )

        # 3. Simulate Topology Path Communication Hops
        hops = topology.get_hops()
        deployment_status = DeploymentStatus.SUCCESS
        failure_path: List[str] = []

        for idx, (source, destination) in enumerate(hops):
            self._log_event(
                event_type=EventType.HOP_ATTEMPT,
                service=source,
                message=f"Attempting communication hop: {source} -> {destination}",
                source_service=source,
                destination_service=destination,
                status="ATTEMPT",
            )

            interrupting_candidate = evaluator.evaluate_hop(source, destination)

            if interrupting_candidate:
                deployment_status = DeploymentStatus.FAILED
                
                # Record hop failure event
                self._log_event(
                    event_type=EventType.HOP_FAILURE,
                    service=source,
                    message=(
                        f"Communication failed from {source} to {destination} "
                        f"due to network candidate {interrupting_candidate.candidate_id} ({interrupting_candidate.candidate_type.value})."
                    ),
                    candidate_id=interrupting_candidate.candidate_id,
                    source_service=source,
                    destination_service=destination,
                    status="FAILED",
                )

                # Determine affected failure path segment (source -> destination -> downstream services if any)
                failure_start_idx = topology.path.index(source)
                # Take source, destination, and the next downstream node if available
                failure_end_idx = min(len(topology.path), failure_start_idx + 3)
                failure_path = topology.path[failure_start_idx:failure_end_idx]

                break
            else:
                self._log_event(
                    event_type=EventType.HOP_SUCCESS,
                    service=source,
                    message=f"Communication succeeded from {source} to {destination}.",
                    source_service=source,
                    destination_service=destination,
                    status="SUCCESS",
                )

        # 4. Deployment End Event
        final_service = failure_path[0] if failure_path else topology.path[-1]
        self._log_event(
            event_type=EventType.DEPLOYMENT_END,
            service=final_service,
            message=f"Deployment simulation completed with status: {deployment_status.value}.",
            status=deployment_status.value,
        )

        return SimulationResult(
            scenario_id=self.scenario.scenario_id,
            seed=self.seed,
            status=deployment_status,
            topology_path=topology.path,
            evaluated_candidates=self.scenario.candidates,
            application_input=self.scenario.application_input,
            failure_path=failure_path,
            events=list(self._events),
        )
