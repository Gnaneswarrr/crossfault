"""Human-readable text output formatter for CrossFault simulation results."""

from crossfault.models import (
    CandidateType,
    DeploymentStatus,
    InvestigationReplayResult,
    SimulationResult,
)


# Human-friendly labels for CandidateTypes
CANDIDATE_LABELS = {
    CandidateType.ROUTE_CHANGE: "Route Change",
    CandidateType.ACCESS_RULE_CHANGE: "Access Rule Change",
    CandidateType.DNS_CHANGE: "DNS Change",
    CandidateType.LIS_PATH_INTERRUPTION: "LIS Path Interruption",
}


def format_simulation_summary(result: SimulationResult) -> str:
    """
    Formats a SimulationResult into a concise, human-readable summary.
    """
    topology_str = " → ".join(result.topology_path)

    events_lines = []
    for candidate in result.evaluated_candidates:
        label = CANDIDATE_LABELS.get(candidate.candidate_type, candidate.candidate_type.value)
        if candidate.interrupts_path:
            events_lines.append(f"✕ {label}")
        else:
            events_lines.append(f"✓ {label}")

    network_events_str = "\n".join(events_lines)

    if result.failure_path:
        failure_path_str = " → ".join(result.failure_path)
    else:
        failure_path_str = "None (All communication paths succeeded)"

    summary = (
        f"Scenario: {result.scenario_id}\n"
        f"Seed: {result.seed}\n\n"
        f"Topology:\n"
        f"{topology_str}\n\n"
        f"Network Events:\n"
        f"{network_events_str}\n\n"
        f"Deployment Result:\n"
        f"{result.status.value}\n\n"
        f"Failure Path:\n"
        f"{failure_path_str}"
    )
    return summary


def format_investigation_summary(investigation: InvestigationReplayResult) -> str:
    """
    Formats an InvestigationReplayResult into a concise, human-readable summary.
    """
    baseline_status = investigation.baseline_result.status.value

    lines = [
        f"Scenario: {investigation.scenario_id}",
        f"Seed: {investigation.seed}",
        "",
        f"BASELINE:",
        f"{baseline_status}",
        "",
        f"COUNTERFACTUAL REPLAYS:",
        ""
    ]

    changed_candidates = []

    for cf in investigation.counterfactual_results:
        disabled_id = cf.configuration.disabled_candidate_id
        
        # Find the candidate label
        label = "Unknown Candidate"
        for c in investigation.baseline_result.evaluated_candidates:
            if c.candidate_id == disabled_id:
                label = CANDIDATE_LABELS.get(c.candidate_type, c.candidate_type.value)
                break
                
        outcome = cf.result.status.value
        lines.append(f"Disable {label} → {outcome}")

        if cf.result.status != investigation.baseline_result.status:
            changed_candidates.append(label)

    lines.append("")
    if changed_candidates:
        labels_str = " and ".join(changed_candidates)
        lines.append(f"Outcome changed when {labels_str} was disabled.")
    else:
        lines.append("Outcome did not change in any counterfactual replay.")

    return "\n".join(lines)
