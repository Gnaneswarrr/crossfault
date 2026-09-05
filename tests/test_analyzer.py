"""Tests for Phase 3 Causal Analyzer."""

import copy
import os
import sys
import unittest

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from crossfault.analyzer import CausalAnalyzer
from crossfault.models import (
    AnalysisStatus,
    CausalVerdict,
    DeploymentStatus,
)
from crossfault.replay import ReplayEngine
from crossfault.scenario import create_initial_scenario


class TestCausalAnalyzer(unittest.TestCase):

    def setUp(self):
        # We generate a valid baseline using Phase 2 logic so we can manually tweak it for tests
        self.scenario = create_initial_scenario()
        self.replay_engine = ReplayEngine()
        self.valid_evidence = self.replay_engine.run(self.scenario, seed=48291)
        self.analyzer = CausalAnalyzer()

    def test_1_cf001_like_evidence(self):
        """TEST 1: CF-001 evidence should yield NECESSARY_FOR_OBSERVED_FAILURE."""
        analysis = self.analyzer.analyze(self.valid_evidence)
        self.assertEqual(analysis.investigation_verdict, CausalVerdict.NECESSARY_FOR_OBSERVED_FAILURE)
        self.assertEqual(analysis.identified_candidate, "NET-004")
        self.assertIsNone(analysis.validation_error)

    def test_2_disabled_but_remains_failed(self):
        """TEST 2: Candidate disabled but deployment remains FAILED -> NOT_NECESSARY."""
        analysis = self.analyzer.analyze(self.valid_evidence)
        # Find ROUTE_CHANGE (NET-001) evidence
        net1_evidence = next(e for e in analysis.candidate_evidence if e.candidate_id == "NET-001")
        self.assertEqual(net1_evidence.candidate_conclusion, CausalVerdict.NOT_NECESSARY)
        self.assertFalse(net1_evidence.outcome_changed)

    def test_3_all_candidates_failed(self):
        """TEST 3: All disabled still produce FAILED -> NO_CAUSAL_CANDIDATE."""
        evidence = copy.deepcopy(self.valid_evidence)
        # Force all replays to result in FAILED
        for cf in evidence.counterfactual_results:
            cf.result.status = DeploymentStatus.FAILED

        analysis = self.analyzer.analyze(evidence)
        self.assertEqual(analysis.investigation_verdict, CausalVerdict.NO_CAUSAL_CANDIDATE)
        self.assertIsNone(analysis.identified_candidate)

    def test_4_multiple_successes(self):
        """TEST 4: Two different candidate replays independently produce SUCCESS -> AMBIGUOUS."""
        evidence = copy.deepcopy(self.valid_evidence)
        # Force NET-001 (Route change) to also yield SUCCESS
        for cf in evidence.counterfactual_results:
            if cf.configuration.disabled_candidate_id in ["NET-001", "NET-004"]:
                cf.result.status = DeploymentStatus.SUCCESS

        analysis = self.analyzer.analyze(evidence)
        self.assertEqual(analysis.investigation_verdict, CausalVerdict.AMBIGUOUS)
        self.assertIsNone(analysis.identified_candidate)

    def test_5_ordering_reversed(self):
        """TEST 5: Candidate ordering is reversed -> same verdict."""
        evidence = copy.deepcopy(self.valid_evidence)
        evidence.counterfactual_results.reverse()

        analysis = self.analyzer.analyze(evidence)
        self.assertEqual(analysis.investigation_verdict, CausalVerdict.NECESSARY_FOR_OBSERVED_FAILURE)
        self.assertEqual(analysis.identified_candidate, "NET-004")

    def test_6_baseline_is_success(self):
        """TEST 6: Baseline is SUCCESS -> BASELINE_NOT_FAILED."""
        evidence = copy.deepcopy(self.valid_evidence)
        evidence.baseline_result.status = DeploymentStatus.SUCCESS

        analysis = self.analyzer.analyze(evidence)
        self.assertEqual(analysis.status, AnalysisStatus.BASELINE_NOT_FAILED)
        self.assertIsNone(analysis.investigation_verdict)
        self.assertIsNotNone(analysis.validation_error)
        self.assertEqual(len(analysis.candidate_evidence), 0)

    def test_7_malformed_evidence(self):
        """TEST 7: Malformed replay evidence (0 disabled candidates) -> INVALID_EVIDENCE."""
        evidence = copy.deepcopy(self.valid_evidence)
        # Force a replay to have all candidates enabled (0 disabled)
        for c in evidence.counterfactual_results[0].configuration.candidates:
            # We must bypass the frozen dataclass constraints for the mock test
            object.__setattr__(c, 'is_enabled', True)

        analysis = self.analyzer.analyze(evidence)
        self.assertEqual(analysis.status, AnalysisStatus.INVALID_EVIDENCE)
        self.assertIsNone(analysis.investigation_verdict)
        self.assertIsNotNone(analysis.validation_error)

    def test_8_seed_mismatch(self):
        """TEST 8: Seed mismatch -> INVALID_EVIDENCE."""
        evidence = copy.deepcopy(self.valid_evidence)
        # Mutate the seed in one replay configuration
        object.__setattr__(evidence.counterfactual_results[0].configuration, 'seed', 99999)

        analysis = self.analyzer.analyze(evidence)
        self.assertEqual(analysis.status, AnalysisStatus.INVALID_EVIDENCE)
        self.assertIsNone(analysis.investigation_verdict)
        self.assertIn("Seed mismatch", analysis.validation_error)

    def test_9_application_input_mismatch(self):
        """TEST 9: Application input mismatch -> INVALID_EVIDENCE."""
        evidence = copy.deepcopy(self.valid_evidence)
        # Replace app input
        object.__setattr__(evidence.counterfactual_results[0].configuration, 'application_input', None)

        analysis = self.analyzer.analyze(evidence)
        self.assertEqual(analysis.status, AnalysisStatus.INVALID_EVIDENCE)
        self.assertIsNone(analysis.investigation_verdict)
        self.assertIn("Application input mismatch", analysis.validation_error)

    def test_10_topology_mismatch(self):
        """TEST 10: Topology mismatch -> INVALID_EVIDENCE."""
        evidence = copy.deepcopy(self.valid_evidence)
        # Mutate topology path
        object.__setattr__(evidence.counterfactual_results[0].configuration, 'topology_path', ["Some", "Other", "Path"])

        analysis = self.analyzer.analyze(evidence)
        self.assertEqual(analysis.status, AnalysisStatus.INVALID_EVIDENCE)
        self.assertIsNone(analysis.investigation_verdict)
        self.assertIn("Topology mismatch", analysis.validation_error)

    def test_11_determinism(self):
        """TEST 11: Analyzer determinism (run twice -> equivalent results)."""
        analysis1 = self.analyzer.analyze(self.valid_evidence)
        analysis2 = self.analyzer.analyze(self.valid_evidence)
        self.assertEqual(analysis1.to_dict(), analysis2.to_dict())

    def test_12_no_simulation_engine_call(self):
        """TEST 12: Analyzer does not invoke SimulationEngine or ReplayEngine."""
        from unittest.mock import patch
        
        mock_evidence = copy.deepcopy(self.valid_evidence)

        with patch("crossfault.engine.SimulationEngine") as mock_sim, \
             patch("crossfault.replay.ReplayEngine") as mock_replay:
            
            analysis = self.analyzer.analyze(mock_evidence)
            
            # Assert they were not instantiated or called
            mock_sim.assert_not_called()
            mock_replay.assert_not_called()
            
        self.assertEqual(analysis.status, AnalysisStatus.VALID)
        self.assertIsInstance(analysis.investigation_verdict, CausalVerdict)

    def test_13_missing_baseline(self):
        """TEST 13: Missing baseline returns INVALID_EVIDENCE status rather than crashing."""
        evidence = copy.deepcopy(self.valid_evidence)
        evidence.baseline_result = None

        analysis = self.analyzer.analyze(evidence)
        self.assertEqual(analysis.status, AnalysisStatus.INVALID_EVIDENCE)
        self.assertIsNone(analysis.investigation_verdict)
        self.assertIn("Missing baseline result", analysis.validation_error)


    def test_cf002_causal_analysis(self):
        from crossfault.scenario import create_cf002_scenario
        scenario2 = create_cf002_scenario()
        valid_evidence2 = self.replay_engine.run(scenario2, seed=48291)
        analysis = self.analyzer.analyze(valid_evidence2)

        self.assertEqual(analysis.status, AnalysisStatus.VALID)
        self.assertEqual(analysis.investigation_verdict, CausalVerdict.NECESSARY_FOR_OBSERVED_FAILURE)
        self.assertEqual(analysis.identified_candidate, "NET-014")

        # Verify unrelated candidates are NOT_NECESSARY
        net11_evidence = next(e for e in analysis.candidate_evidence if e.candidate_id == "NET-011")
        self.assertEqual(net11_evidence.candidate_conclusion, CausalVerdict.NOT_NECESSARY)


if __name__ == "__main__":
    unittest.main()
