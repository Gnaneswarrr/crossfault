"""Tests for Phase 5 AI Investigator and Validator."""

import copy
import json
import unittest
from unittest.mock import patch

from crossfault.ai_layer import (
    AIInvestigator,
    AIOutputValidator,
    AIValidationError,
    EvidenceSummarizer,
    LLMClient,
    VerifiedAIResponse,
)
from crossfault.models import CausalVerdict
from crossfault.replay import ReplayEngine
from crossfault.scenario import create_initial_scenario, create_cf002_scenario
from crossfault.analyzer import CausalAnalyzer
from crossfault.assembler import EvidenceAssembler


class MockLLMClient(LLMClient):
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.prompt_received = None
        self.payload_received = None

    def generate_json(self, prompt: str, payload: dict) -> str:
        self.prompt_received = prompt
        self.payload_received = payload
        return self.response_text


class TestAILayer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Generate genuine evidence for CF-001
        cls.scenario1 = create_initial_scenario()
        engine = ReplayEngine()
        result1 = engine.run(cls.scenario1, seed=48291)
        analyzer = CausalAnalyzer()
        analysis1 = analyzer.analyze(result1)
        assembler = EvidenceAssembler()
        cls.evidence1 = assembler.assemble(result1, analysis1)

        # Generate genuine evidence for CF-002
        cls.scenario2 = create_cf002_scenario()
        result2 = engine.run(cls.scenario2, seed=48291)
        analysis2 = analyzer.analyze(result2)
        cls.evidence2 = assembler.assemble(result2, analysis2)

    def _get_valid_cf001_json(self) -> dict:
        return {
            "causal_candidate_id": "NET-004",
            "causal_verdict": "NECESSARY_FOR_OBSERVED_FAILURE",
            "dependency_path": list(self.evidence1.dependency_path),
            "narrative_explanation": "Valid narrative.",
            "negative_evidence_explanation": "Valid negative.",
            "remediation_steps": ["Fix it."]
        }

    def _get_valid_cf002_json(self) -> dict:
        return {
            "causal_candidate_id": "NET-014",
            "causal_verdict": "NECESSARY_FOR_OBSERVED_FAILURE",
            "dependency_path": list(self.evidence2.dependency_path),
            "narrative_explanation": "Valid narrative 2.",
            "negative_evidence_explanation": "Valid negative 2.",
            "remediation_steps": ["Fix it 2."]
        }

    def test_1_valid_ai_response_passes(self):
        """test valid AI response passes (CF-001)"""
        llm = MockLLMClient(json.dumps(self._get_valid_cf001_json()))
        investigator = AIInvestigator(llm)
        response = investigator.investigate(self.scenario1, self.evidence1)
        
        self.assertIsInstance(response, VerifiedAIResponse)
        self.assertEqual(response.verified_evidence.necessary_candidate, "NET-004")
        self.assertEqual(response.ai_interpretation.narrative_explanation, "Valid narrative.")
        self.assertEqual(response.ai_recommendations.remediation_steps, ["Fix it."])

    def test_2_wrong_candidate_id_rejected(self):
        """test wrong candidate ID rejected (CF-002 adversarial test)"""
        bad_data = self._get_valid_cf002_json()
        bad_data["causal_candidate_id"] = "NET-013"  # Hallucinated candidate!

        llm = MockLLMClient(json.dumps(bad_data))
        investigator = AIInvestigator(llm)
        
        with self.assertRaises(AIValidationError) as ctx:
            investigator.investigate(self.scenario2, self.evidence2)
        
        self.assertIn("NET-014", str(ctx.exception))
        self.assertIn("NET-013", str(ctx.exception))

    def test_3_wrong_causal_verdict_rejected(self):
        """test wrong causal verdict rejected"""
        bad_data = self._get_valid_cf001_json()
        bad_data["causal_verdict"] = "NOT_NECESSARY"

        llm = MockLLMClient(json.dumps(bad_data))
        investigator = AIInvestigator(llm)
        
        with self.assertRaises(AIValidationError):
            investigator.investigate(self.scenario1, self.evidence1)

    def test_4_wrong_dependency_path_rejected(self):
        """test wrong dependency path rejected"""
        bad_data = self._get_valid_cf001_json()
        bad_data["dependency_path"] = ["Clinic", "Some Hallucinated Service"]

        llm = MockLLMClient(json.dumps(bad_data))
        investigator = AIInvestigator(llm)
        
        with self.assertRaises(AIValidationError) as ctx:
            investigator.investigate(self.scenario1, self.evidence1)
        self.assertIn("contradicted dependency path", str(ctx.exception))

    def test_5_missing_fields_rejected(self):
        """test missing fields rejected"""
        bad_data = self._get_valid_cf001_json()
        del bad_data["narrative_explanation"]

        llm = MockLLMClient(json.dumps(bad_data))
        investigator = AIInvestigator(llm)
        
        with self.assertRaises(AIValidationError) as ctx:
            investigator.investigate(self.scenario1, self.evidence1)
        self.assertIn("Missing required keys", str(ctx.exception))
        self.assertIn("narrative_explanation", str(ctx.exception))

    def test_6_malformed_json_rejected(self):
        """test malformed JSON rejected"""
        llm = MockLLMClient("Here is my analysis: { bad json ]")
        investigator = AIInvestigator(llm)
        
        with self.assertRaises(AIValidationError) as ctx:
            investigator.investigate(self.scenario1, self.evidence1)
        self.assertIn("Malformed JSON", str(ctx.exception))

    def test_7_wrong_field_types_rejected(self):
        """test wrong field types rejected"""
        bad_data = self._get_valid_cf001_json()
        bad_data["dependency_path"] = "Clinic -> Gateway"  # string instead of list

        llm = MockLLMClient(json.dumps(bad_data))
        investigator = AIInvestigator(llm)
        
        with self.assertRaises(AIValidationError) as ctx:
            investigator.investigate(self.scenario1, self.evidence1)
        self.assertIn("'dependency_path' must be a list", str(ctx.exception))

    def test_8_markdown_wrapped_json_handled_correctly(self):
        """test that markdown fenced json is safely parsed"""
        json_str = json.dumps(self._get_valid_cf001_json())
        markdown_str = f"```json\n{json_str}\n```"
        
        llm = MockLLMClient(markdown_str)
        investigator = AIInvestigator(llm)
        response = investigator.investigate(self.scenario1, self.evidence1)
        
        self.assertEqual(response.verified_evidence.necessary_candidate, "NET-004")

    def test_9_evidence_remains_unchanged(self):
        """test evidence remains unchanged after AI processing"""
        original_evidence_dict = self.evidence1.to_dict()
        
        llm = MockLLMClient(json.dumps(self._get_valid_cf001_json()))
        investigator = AIInvestigator(llm)
        response = investigator.investigate(self.scenario1, self.evidence1)
        
        self.assertEqual(response.verified_evidence.to_dict(), original_evidence_dict)

    def test_10_no_engine_invocations(self):
        """test no SimulationEngine, ReplayEngine, CausalAnalyzer, or EvidenceAssembler invocation"""
        llm = MockLLMClient(json.dumps(self._get_valid_cf001_json()))
        investigator = AIInvestigator(llm)
        
        with patch("crossfault.engine.SimulationEngine") as mock_sim, \
             patch("crossfault.replay.ReplayEngine") as mock_replay, \
             patch("crossfault.analyzer.CausalAnalyzer") as mock_analyzer, \
             patch("crossfault.assembler.EvidenceAssembler") as mock_assembler:
             
            investigator.investigate(self.scenario1, self.evidence1)
            
            mock_sim.assert_not_called()
            mock_replay.assert_not_called()
            mock_analyzer.assert_not_called()
            mock_assembler.assert_not_called()

    def test_11_empty_ai_response_rejected(self):
        """test empty string AI response is safely rejected"""
        llm = MockLLMClient("")
        investigator = AIInvestigator(llm)
        with self.assertRaises(AIValidationError) as ctx:
            investigator.investigate(self.scenario1, self.evidence1)
        self.assertIn("Malformed JSON", str(ctx.exception))

    def test_12_null_field_values_rejected(self):
        """test null values for required string/list fields are rejected"""
        bad_data = self._get_valid_cf001_json()
        bad_data["narrative_explanation"] = None  # null value

        llm = MockLLMClient(json.dumps(bad_data))
        investigator = AIInvestigator(llm)
        with self.assertRaises(AIValidationError) as ctx:
            investigator.investigate(self.scenario1, self.evidence1)
        self.assertIn("'narrative_explanation' must be a string", str(ctx.exception))

    def test_13_extra_json_fields_handled_safely(self):
        """test unexpected extra JSON fields do not crash or corrupt output"""
        data_with_extra = self._get_valid_cf001_json()
        data_with_extra["unexpected_extra_key"] = "hacked_value"
        data_with_extra["prompt_injection"] = "Ignore previous instructions"

        llm = MockLLMClient(json.dumps(data_with_extra))
        investigator = AIInvestigator(llm)
        response = investigator.investigate(self.scenario1, self.evidence1)
        self.assertEqual(response.verified_evidence.necessary_candidate, "NET-004")
        self.assertEqual(response.ai_interpretation.narrative_explanation, "Valid narrative.")


if __name__ == "__main__":
    unittest.main()
