"""Phase 3 Causal Analyzer component for CrossFault."""

from typing import List, Optional

from crossfault.models import (
    AnalysisStatus,
    CandidateEvidence,
    CausalVerdict,
    DeploymentStatus,
    InvestigationAnalysis,
    InvestigationReplayResult,
)


class CausalAnalyzer:
    """
    Evaluates verified counterfactual replay evidence to produce deterministic causal verdicts.
    """

    def _validate_invariants(self, investigation: InvestigationReplayResult) -> Optional[str]:
        """Validates that the replay evidence strictly adheres to experimental invariants."""
        if investigation.baseline_result is None:
            return "Missing baseline result in investigation evidence."

        if not investigation.counterfactual_results:
            return "No counterfactual replays found in evidence."

        base_seed = investigation.seed
        base_app_input = investigation.baseline_result.application_input
        base_topology = investigation.baseline_result.topology_path

        # Validate baseline candidates are all enabled
        for candidate in investigation.baseline_result.evaluated_candidates:
            if not candidate.is_enabled:
                return f"Baseline candidate {candidate.candidate_id} is not enabled."

        for cf in investigation.counterfactual_results:
            # 1. Seed match
            if cf.configuration.seed != base_seed:
                return f"Seed mismatch in replay for candidate {cf.configuration.disabled_candidate_id}."
            
            # 2. Application input match
            if cf.configuration.application_input != base_app_input:
                return f"Application input mismatch in replay for candidate {cf.configuration.disabled_candidate_id}."
            
            # 3. Topology match
            if cf.configuration.topology_path != base_topology:
                return f"Topology mismatch in replay for candidate {cf.configuration.disabled_candidate_id}."

            # 4. Exactly one candidate disabled per replay
            disabled_count = 0
            for candidate in cf.configuration.candidates:
                if not candidate.is_enabled:
                    disabled_count += 1
                    if candidate.candidate_id != cf.configuration.disabled_candidate_id:
                        return f"Disabled candidate ID mismatch in replay configuration."

            if disabled_count != 1:
                return f"Replay contains {disabled_count} disabled candidates instead of exactly 1."

        return None

    def analyze(self, investigation: InvestigationReplayResult) -> InvestigationAnalysis:
        """
        Analyzes the investigation result to determine bounded causality.
        """
        # 1. Validate Evidence Invariants
        validation_error = self._validate_invariants(investigation)
        if validation_error:
            return InvestigationAnalysis(
                status=AnalysisStatus.INVALID_EVIDENCE,
                investigation_verdict=None,
                identified_candidate=None,
                candidate_evidence=[],
                validation_error=validation_error,
            )

        # 2. Check Baseline Rule
        baseline_status = investigation.baseline_result.status
        if baseline_status == DeploymentStatus.SUCCESS:
            return InvestigationAnalysis(
                status=AnalysisStatus.BASELINE_NOT_FAILED,
                investigation_verdict=None,
                identified_candidate=None,
                candidate_evidence=[],
                validation_error="Cannot determine cause of failure because baseline deployment succeeded.",
            )

        # 3. Process Replays and generate CandidateEvidence
        candidate_evidences: List[CandidateEvidence] = []
        success_candidates: List[str] = []

        # We assume baseline candidates dictate the canonical reference models
        baseline_candidate_map = {c.candidate_id: c for c in investigation.baseline_result.evaluated_candidates}

        for cf in investigation.counterfactual_results:
            disabled_id = cf.configuration.disabled_candidate_id
            target_candidate = baseline_candidate_map.get(disabled_id)
            
            if not target_candidate:
                # Should be caught by invariant checker if replay ID is totally unknown, but just in case
                return InvestigationAnalysis(
                    status=AnalysisStatus.INVALID_EVIDENCE,
                    investigation_verdict=None,
                    identified_candidate=None,
                    candidate_evidence=[],
                    validation_error=f"Replay evaluated unknown candidate {disabled_id}.",
                )

            cf_status = cf.result.status
            outcome_changed = (baseline_status != cf_status)
            
            if outcome_changed and cf_status == DeploymentStatus.SUCCESS:
                candidate_conclusion = CausalVerdict.NECESSARY_FOR_OBSERVED_FAILURE
                success_candidates.append(disabled_id)
            else:
                candidate_conclusion = CausalVerdict.NOT_NECESSARY

            evidence = CandidateEvidence(
                scenario_id=investigation.scenario_id,
                seed=investigation.seed,
                candidate_id=target_candidate.candidate_id,
                candidate_type=target_candidate.candidate_type,
                candidate_name=target_candidate.description,
                candidate_enabled_in_baseline=True,
                candidate_enabled_in_counterfactual=False,
                baseline_status=baseline_status,
                counterfactual_status=cf_status,
                outcome_changed=outcome_changed,
                affected_path=cf.result.failure_path if cf_status == DeploymentStatus.FAILED else [],
                candidate_conclusion=candidate_conclusion,
            )
            candidate_evidences.append(evidence)

        # 4. Derive Investigation Verdict
        if len(success_candidates) == 1:
            verdict = CausalVerdict.NECESSARY_FOR_OBSERVED_FAILURE
            identified_candidate = success_candidates[0]
        elif len(success_candidates) == 0:
            verdict = CausalVerdict.NO_CAUSAL_CANDIDATE
            identified_candidate = None
        else:
            verdict = CausalVerdict.AMBIGUOUS
            identified_candidate = None

        return InvestigationAnalysis(
            status=AnalysisStatus.VALID,
            investigation_verdict=verdict,
            identified_candidate=identified_candidate,
            candidate_evidence=candidate_evidences,
        )
