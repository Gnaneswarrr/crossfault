"""Human-readable text output formatter for CrossFault simulation results."""

from crossfault.models import (
    AnalysisStatus,
    CandidateType,
    CausalVerdict,
    DeploymentStatus,
    InvestigationAnalysis,
    InvestigationReplayResult,
    SimulationResult,
    VerifiedInvestigationEvidence,
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


def format_causal_analysis(analysis: InvestigationAnalysis) -> str:
    """Formats an InvestigationAnalysis into human-readable causal verdicts."""
    lines = [
        "CAUSAL ANALYSIS:",
        ""
    ]

    if analysis.status != AnalysisStatus.VALID:
        lines.extend([
            "Investigation Status:",
            analysis.status.value,
            ""
        ])

    if analysis.investigation_verdict:
        lines.extend([
            "Verdict:",
            analysis.investigation_verdict.value,
            ""
        ])

    if analysis.validation_error:
        lines.extend([
            "Validation Error:",
            analysis.validation_error,
            ""
        ])

    if analysis.identified_candidate:
        identified_label = analysis.identified_candidate
        # Try to find human readable name from evidence
        for ev in analysis.candidate_evidence:
            if ev.candidate_id == analysis.identified_candidate:
                identified_label = CANDIDATE_LABELS.get(ev.candidate_type, ev.candidate_type.value)
                break
        
        lines.extend([
            "Candidate:",
            identified_label,
            ""
        ])

        # Print detailed verified evidence for the identified candidate
        for ev in analysis.candidate_evidence:
            if ev.candidate_id == analysis.identified_candidate:
                changed_str = "YES" if ev.outcome_changed else "NO"
                lines.extend([
                    "Verified Evidence:",
                    f"Baseline: {ev.baseline_status.value}",
                    f"Without {identified_label}: {ev.counterfactual_status.value}",
                    f"Outcome changed: {changed_str}",
                    "",
                    "Bound:",
                    "Necessary for reproducing the observed failure under the bounded deterministic replay experiment.",
                    ""
                ])
                break

    return "\n".join(lines).strip()


def format_verified_evidence(evidence: VerifiedInvestigationEvidence) -> str:
    """Formats the VerifiedInvestigationEvidence path output."""
    lines = [
        "VERIFIED EVIDENCE ASSEMBLY:",
        ""
    ]

    if evidence.limitation_flags:
        lines.append("Limitations:")
        for flag in evidence.limitation_flags:
            lines.append(f"- {flag.value}")
        lines.append("")

    if evidence.dependency_path:
        lines.extend([
            "Dependency / Divergence Path:",
            " → ".join(evidence.dependency_path),
            ""
        ])
        
    if evidence.divergence_event_id:
        lines.extend([
            "Divergence Provenance:",
            f"Event ID: {evidence.divergence_event_id}",
            ""
        ])

    return "\n".join(lines).strip()
