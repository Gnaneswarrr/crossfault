"""Verified Evidence Assembler for Phase 4."""

from typing import List, Tuple

from crossfault.models import (
    AnalysisStatus,
    CausalVerdict,
    EventType,
    InvestigationAnalysis,
    InvestigationReplayResult,
    LimitationFlag,
    VerifiedInvestigationEvidence,
)


class EvidenceAssembler:
    """Assembles verified evidence and extracts dependency paths from traces."""

    def assemble(
        self,
        investigation: InvestigationReplayResult,
        analysis: InvestigationAnalysis,
    ) -> VerifiedInvestigationEvidence:
        """Constructs immutable verified evidence from the investigation results."""
        
        # 1. Base Setup
        scenario_id = investigation.scenario_id
        seed = investigation.seed
        analysis_status = analysis.status
        causal_verdict = analysis.investigation_verdict
        baseline_outcome = investigation.baseline_result.status
        per_candidate_evidence = tuple(analysis.candidate_evidence)
        necessary_candidate = analysis.identified_candidate

        # 2. Check for unresolved states requiring limitations
        if analysis_status != AnalysisStatus.VALID or causal_verdict != CausalVerdict.NECESSARY_FOR_OBSERVED_FAILURE:
            return VerifiedInvestigationEvidence(
                scenario_id=scenario_id,
                seed=seed,
                analysis_status=analysis_status,
                causal_verdict=causal_verdict,
                baseline_outcome=baseline_outcome,
                per_candidate_evidence=per_candidate_evidence,
                necessary_candidate=necessary_candidate,
                dependency_path=tuple(),
                divergence_event_id=None,
                limitation_flags=(LimitationFlag.NO_SINGLE_VERIFIED_DEPENDENCY_PATH,)
            )

        # 3. Path Extraction for NECESSARY_FOR_OBSERVED_FAILURE
        baseline_events = investigation.baseline_result.events
        
        # Find the specific counterfactual
        cf_result = next(
            (cf for cf in investigation.counterfactual_results 
             if cf.configuration.disabled_candidate_id == necessary_candidate),
            None
        )

        if not cf_result:
            # Fallback if somehow missing
            return VerifiedInvestigationEvidence(
                scenario_id=scenario_id,
                seed=seed,
                analysis_status=analysis_status,
                causal_verdict=causal_verdict,
                baseline_outcome=baseline_outcome,
                per_candidate_evidence=per_candidate_evidence,
                necessary_candidate=necessary_candidate,
                dependency_path=tuple(),
                divergence_event_id=None,
                limitation_flags=(LimitationFlag.NO_SINGLE_VERIFIED_DEPENDENCY_PATH,)
            )

        cf_events = cf_result.result.events

        # Identify divergence
        divergence_event_id = None
        for b_ev, c_ev in zip(baseline_events, cf_events):
            if b_ev.event_type != c_ev.event_type or b_ev.status != c_ev.status:
                # This is the first meaningful divergence (either evaluation change or hop failure vs success)
                divergence_event_id = b_ev.event_id
                break

        # Extract the ordered dependency path by tracing the successful counterfactual hops
        # that resolve the identified trace divergence.
        path_nodes: List[str] = []
        divergence_resolved = False

        for i, ev in enumerate(cf_events):
            if divergence_event_id and i < len(baseline_events):
                if baseline_events[i].event_id == divergence_event_id:
                    divergence_resolved = True
                    
            if ev.event_type == EventType.HOP_SUCCESS:
                if not path_nodes:
                    if ev.source_service:
                        path_nodes.append(ev.source_service)
                if ev.destination_service and (not path_nodes or path_nodes[-1] != ev.destination_service):
                    path_nodes.append(ev.destination_service)

        # Only return the path if we successfully traced through the divergence
        if divergence_event_id and not divergence_resolved:
            path_nodes = []

        return VerifiedInvestigationEvidence(
            scenario_id=scenario_id,
            seed=seed,
            analysis_status=analysis_status,
            causal_verdict=causal_verdict,
            baseline_outcome=baseline_outcome,
            per_candidate_evidence=per_candidate_evidence,
            necessary_candidate=necessary_candidate,
            dependency_path=tuple(path_nodes),
            divergence_event_id=divergence_event_id,
            limitation_flags=tuple()
        )
