"""Domain models for CrossFault simulator."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DeploymentStatus(str, Enum):
    """Status of the deployment simulation run."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class CandidateType(str, Enum):
    """Types of candidate network changes."""
    ROUTE_CHANGE = "ROUTE_CHANGE"
    ACCESS_RULE_CHANGE = "ACCESS_RULE_CHANGE"
    DNS_CHANGE = "DNS_CHANGE"
    LIS_PATH_INTERRUPTION = "LIS_PATH_INTERRUPTION"


class CausalVerdict(str, Enum):
    """Typed causal verdicts derived from bounded replay evidence."""
    NECESSARY_FOR_OBSERVED_FAILURE = "NECESSARY_FOR_OBSERVED_FAILURE"
    NOT_NECESSARY = "NOT_NECESSARY"
    NO_CAUSAL_CANDIDATE = "NO_CAUSAL_CANDIDATE"
    AMBIGUOUS = "AMBIGUOUS"


class AnalysisStatus(str, Enum):
    """Validity state of the causal analysis investigation."""
    VALID = "VALID"
    BASELINE_NOT_FAILED = "BASELINE_NOT_FAILED"
    INVALID_EVIDENCE = "INVALID_EVIDENCE"


@dataclass(frozen=True)
class ApplicationInput:
    """Deterministic synthetic application deployment payload."""
    request_id: str
    workload_type: str
    target_environment: str
    specimen_type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "workload_type": self.workload_type,
            "target_environment": self.target_environment,
            "specimen_type": self.specimen_type,
        }


class EventType(str, Enum):
    """Types of simulation lifecycle and communication events."""
    DEPLOYMENT_START = "DEPLOYMENT_START"
    NETWORK_EVENT_EVALUATION = "NETWORK_EVENT_EVALUATION"
    HOP_ATTEMPT = "HOP_ATTEMPT"
    HOP_SUCCESS = "HOP_SUCCESS"
    HOP_FAILURE = "HOP_FAILURE"
    DEPLOYMENT_END = "DEPLOYMENT_END"


@dataclass(frozen=True)
class NetworkCandidate:
    """Represents a candidate network change that occurred around the deployment time."""
    candidate_id: str
    candidate_type: CandidateType
    description: str
    affected_source: Optional[str] = None
    affected_destination: Optional[str] = None
    interrupts_path: bool = False
    is_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_type": self.candidate_type.value,
            "description": self.description,
            "affected_source": self.affected_source,
            "affected_destination": self.affected_destination,
            "interrupts_path": self.interrupts_path,
            "is_enabled": self.is_enabled,
        }


@dataclass(frozen=True)
class SimulationEvent:
    """Structured event recorded during simulation execution."""
    event_id: str
    order: int
    timestamp_offset_ms: float
    service: str
    event_type: EventType
    message: str
    candidate_id: Optional[str] = None
    source_service: Optional[str] = None
    destination_service: Optional[str] = None
    status: str = "INFO"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "order": self.order,
            "timestamp_offset_ms": round(self.timestamp_offset_ms, 2),
            "service": self.service,
            "event_type": self.event_type.value,
            "message": self.message,
            "candidate_id": self.candidate_id,
            "source_service": self.source_service,
            "destination_service": self.destination_service,
            "status": self.status,
        }


@dataclass(frozen=True)
class Scenario:
    """Configuration for a deployment scenario to simulate."""
    scenario_id: str
    name: str
    description: str
    topology_path: List[str]
    candidates: List[NetworkCandidate]
    application_input: ApplicationInput

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "description": self.description,
            "topology_path": self.topology_path,
            "candidates": [c.to_dict() for c in self.candidates],
            "application_input": self.application_input.to_dict(),
        }


@dataclass
class SimulationResult:
    """Structured simulation output."""
    scenario_id: str
    seed: int
    status: DeploymentStatus
    topology_path: List[str]
    evaluated_candidates: List[NetworkCandidate]
    application_input: ApplicationInput
    failure_path: List[str]
    events: List[SimulationEvent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "status": self.status.value,
            "topology_path": self.topology_path,
            "evaluated_candidates": [c.to_dict() for c in self.evaluated_candidates],
            "application_input": self.application_input.to_dict(),
            "failure_path": self.failure_path,
            "events": [e.to_dict() for e in self.events],
        }


@dataclass(frozen=True)
class ReplayConfiguration:
    """Configuration isolated for a specific replay run."""
    scenario_id: str
    seed: int
    disabled_candidate_id: Optional[str]
    application_input: ApplicationInput
    topology_path: List[str]
    candidates: List[NetworkCandidate]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "disabled_candidate_id": self.disabled_candidate_id,
            "application_input": self.application_input.to_dict(),
            "topology_path": self.topology_path,
            "candidates": [c.to_dict() for c in self.candidates],
        }


@dataclass
class CounterfactualResult:
    """The complete result of an isolated replay."""
    configuration: ReplayConfiguration
    result: SimulationResult

    def to_dict(self) -> Dict[str, Any]:
        return {
            "configuration": self.configuration.to_dict(),
            "result": self.result.to_dict(),
        }


@dataclass
class InvestigationReplayResult:
    """The aggregate findings of an entire replay investigation for a scenario."""
    scenario_id: str
    seed: int
    baseline_result: SimulationResult
    counterfactual_results: List[CounterfactualResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "baseline_result": self.baseline_result.to_dict(),
            "counterfactual_results": [r.to_dict() for r in self.counterfactual_results],
        }


@dataclass(frozen=True)
class CandidateEvidence:
    """Verified experimental evidence for a single candidate."""
    scenario_id: str
    seed: int
    candidate_id: str
    candidate_type: CandidateType
    candidate_name: str
    candidate_enabled_in_baseline: bool
    candidate_enabled_in_counterfactual: bool
    baseline_status: DeploymentStatus
    counterfactual_status: DeploymentStatus
    outcome_changed: bool
    affected_path: List[str]
    candidate_conclusion: CausalVerdict

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "candidate_id": self.candidate_id,
            "candidate_type": self.candidate_type.value,
            "candidate_name": self.candidate_name,
            "candidate_enabled_in_baseline": self.candidate_enabled_in_baseline,
            "candidate_enabled_in_counterfactual": self.candidate_enabled_in_counterfactual,
            "baseline_status": self.baseline_status.value,
            "counterfactual_status": self.counterfactual_status.value,
            "outcome_changed": self.outcome_changed,
            "affected_path": self.affected_path,
            "candidate_conclusion": self.candidate_conclusion.value,
        }


@dataclass
class InvestigationAnalysis:
    """The overarching causal verdict derived from an investigation."""
    status: AnalysisStatus
    investigation_verdict: Optional[CausalVerdict]
    identified_candidate: Optional[str]
    candidate_evidence: List[CandidateEvidence]
    validation_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "investigation_verdict": self.investigation_verdict.value if self.investigation_verdict else None,
            "identified_candidate": self.identified_candidate,
            "candidate_evidence": [e.to_dict() for e in self.candidate_evidence],
            "validation_error": self.validation_error,
        }
