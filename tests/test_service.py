"""Tests for InvestigationService graceful degradation and AI failure handling."""

import json
import unittest
from unittest.mock import MagicMock, patch

from crossfault.ai_layer import LLMClient
from crossfault.models import CausalVerdict
from crossfault.service import InvestigationService


class FailingLLMClient(LLMClient):
    """LLM client mock that simulates a provider rate-limit failure (429)."""
    def generate_json(self, prompt: str, payload: dict) -> str:
        raise RuntimeError("Gemini API Error: 429 RESOURCE_EXHAUSTED Quota exceeded")


class SuccessfulLLMClient(LLMClient):
    """LLM client mock that returns valid structured JSON matching deterministic evidence."""
    def generate_json(self, prompt: str, payload: dict) -> str:
        return json.dumps({
            "causal_candidate_id": payload["identified_necessary_candidate"],
            "causal_verdict": payload["causal_verdict"],
            "dependency_path": payload["verified_dependency_path"],
            "narrative_explanation": "Verified AI interpretation explanation.",
            "negative_evidence_explanation": "Verified AI negative evidence explanation.",
            "remediation_steps": ["Restore network connectivity."]
        })


class TestInvestigationService(unittest.TestCase):

    def test_ai_provider_failure_graceful_degradation_cf001(self):
        """Verify CF-001 completes deterministic investigation when AI provider fails."""
        failing_client = FailingLLMClient()
        service = InvestigationService(llm_client=failing_client)

        response = service.run_investigation("CF-001", seed=48291)

        # Deterministic evidence must be intact
        evidence = response.verified_evidence
        self.assertIsNotNone(evidence)
        self.assertEqual(evidence.scenario_id, "CF-001")
        self.assertEqual(evidence.causal_verdict, CausalVerdict.NECESSARY_FOR_OBSERVED_FAILURE)
        self.assertEqual(evidence.necessary_candidate, "NET-004")
        self.assertTrue(len(evidence.dependency_path) > 0)
        self.assertEqual(evidence.dependency_path[0], "Clinic")

        # AI fields must be null/absent
        self.assertIsNone(response.ai_interpretation)
        self.assertIsNone(response.ai_recommendations)

        # AI status metadata must explicitly indicate unavailability without leaking raw details
        self.assertEqual(response.ai_status, "unavailable")
        self.assertIn("AI interpretation unavailable", response.ai_error)
        self.assertNotIn("429", response.ai_error)
        self.assertNotIn("GEMINI_API_KEY", response.ai_error)

    def test_ai_provider_failure_graceful_degradation_cf002(self):
        """Verify CF-002 completes deterministic candidate NET-014 when AI provider fails."""
        failing_client = FailingLLMClient()
        service = InvestigationService(llm_client=failing_client)

        response = service.run_investigation("CF-002", seed=48291)

        evidence = response.verified_evidence
        self.assertIsNotNone(evidence)
        self.assertEqual(evidence.scenario_id, "CF-002")
        self.assertEqual(evidence.causal_verdict, CausalVerdict.NECESSARY_FOR_OBSERVED_FAILURE)
        self.assertEqual(evidence.necessary_candidate, "NET-014")

        self.assertIsNone(response.ai_interpretation)
        self.assertIsNone(response.ai_recommendations)
        self.assertEqual(response.ai_status, "unavailable")

    def test_successful_ai_execution(self):
        """Verify full response when AI provider succeeds."""
        successful_client = SuccessfulLLMClient()
        service = InvestigationService(llm_client=successful_client)

        response = service.run_investigation("CF-001", seed=48291)

        self.assertIsNotNone(response.verified_evidence)
        self.assertEqual(response.verified_evidence.necessary_candidate, "NET-004")
        self.assertIsNotNone(response.ai_interpretation)
        self.assertEqual(response.ai_interpretation.narrative_explanation, "Verified AI interpretation explanation.")
        self.assertIsNotNone(response.ai_recommendations)
        self.assertEqual(response.ai_recommendations.remediation_steps, ["Restore network connectivity."])
        self.assertEqual(response.ai_status, "available")
        self.assertIsNone(response.ai_error)

    def test_deterministic_engine_failure_not_swallowed(self):
        """Verify that failures in deterministic replay/analysis are NOT swallowed as AI failures."""
        service = InvestigationService(llm_client=FailingLLMClient())

        with patch.object(service.replay_engine, "run", side_effect=RuntimeError("Replay memory corruption")):
            with self.assertRaises(RuntimeError) as ctx:
                service.run_investigation("CF-001", seed=48291)
            self.assertIn("Replay memory corruption", str(ctx.exception))


    def test_cf004_investigation_execution(self):
        """Verify CF-004 produces verified evidence with NET-033 as necessary candidate."""
        service = InvestigationService(llm_client=SuccessfulLLMClient())
        response = service.run_investigation("CF-004", seed=48291)

        evidence = response.verified_evidence
        self.assertEqual(evidence.scenario_id, "CF-004")
        self.assertEqual(evidence.baseline_outcome.value, "FAILED")
        self.assertEqual(evidence.causal_verdict, CausalVerdict.NECESSARY_FOR_OBSERVED_FAILURE)
        self.assertEqual(evidence.necessary_candidate, "NET-033")

        # Verify candidate counterfactual outcomes
        candidate_map = {c.candidate_id: c for c in evidence.per_candidate_evidence}
        self.assertEqual(candidate_map["NET-031"].counterfactual_status.value, "FAILED")
        self.assertFalse(candidate_map["NET-031"].outcome_changed)
        self.assertEqual(candidate_map["NET-032"].counterfactual_status.value, "FAILED")
        self.assertFalse(candidate_map["NET-032"].outcome_changed)
        self.assertEqual(candidate_map["NET-033"].counterfactual_status.value, "SUCCESS")
        self.assertTrue(candidate_map["NET-033"].outcome_changed)
        self.assertEqual(candidate_map["NET-034"].counterfactual_status.value, "FAILED")
        self.assertFalse(candidate_map["NET-034"].outcome_changed)

        # Verify trace-derived dependency path and divergence
        self.assertIn("ICU Gateway Router", evidence.dependency_path)
        self.assertIsNotNone(evidence.divergence_event_id)

    def test_cf005_investigation_execution(self):
        """Verify CF-005 produces verified evidence with NET-043 as necessary candidate."""
        service = InvestigationService(llm_client=SuccessfulLLMClient())
        response = service.run_investigation("CF-005", seed=48291)

        evidence = response.verified_evidence
        self.assertEqual(evidence.scenario_id, "CF-005")
        self.assertEqual(evidence.baseline_outcome.value, "FAILED")
        self.assertEqual(evidence.causal_verdict, CausalVerdict.NECESSARY_FOR_OBSERVED_FAILURE)
        self.assertEqual(evidence.necessary_candidate, "NET-043")

        # Verify candidate counterfactual outcomes
        candidate_map = {c.candidate_id: c for c in evidence.per_candidate_evidence}
        self.assertEqual(candidate_map["NET-041"].counterfactual_status.value, "FAILED")
        self.assertFalse(candidate_map["NET-041"].outcome_changed)
        self.assertEqual(candidate_map["NET-042"].counterfactual_status.value, "FAILED")
        self.assertFalse(candidate_map["NET-042"].outcome_changed)
        self.assertEqual(candidate_map["NET-043"].counterfactual_status.value, "SUCCESS")
        self.assertTrue(candidate_map["NET-043"].outcome_changed)
        self.assertEqual(candidate_map["NET-044"].counterfactual_status.value, "FAILED")
        self.assertFalse(candidate_map["NET-044"].outcome_changed)

        # Verify trace-derived dependency path and divergence
        self.assertIn("Drug Interaction Gateway", evidence.dependency_path)
        self.assertIsNotNone(evidence.divergence_event_id)


if __name__ == "__main__":
    unittest.main()
