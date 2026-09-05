"""Tests for Phase 4 Evidence Assembler."""

import copy
import os
import sys
import unittest
from unittest.mock import patch

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from crossfault.analyzer import CausalAnalyzer
from crossfault.assembler import EvidenceAssembler
from crossfault.models import (
    AnalysisStatus,
    CausalVerdict,
    DeploymentStatus,
    EventType,
    LimitationFlag,
    SimulationEvent,
    VerifiedInvestigationEvidence,
)
from crossfault.replay import ReplayEngine
from crossfault.scenario import create_initial_scenario


class TestEvidenceAssembler(unittest.TestCase):

    def setUp(self):
        self.scenario = create_initial_scenario()
        self.replay_engine = ReplayEngine()
        self.analyzer = CausalAnalyzer()
        self.assembler = EvidenceAssembler()
        self.seed = 48291
        
        # Pre-compute valid baseline investigation for CF-001
        self.investigation = self.replay_engine.run(self.scenario, self.seed)
        self.analysis = self.analyzer.analyze(self.investigation)

    def test_a_resolved_cf001(self):
        """Test A: Resolved CF-001 properly extracts the dependency path."""
        evidence = self.assembler.assemble(self.investigation, self.analysis)
        
        self.assertIsInstance(evidence, VerifiedInvestigationEvidence)
        self.assertEqual(evidence.causal_verdict, CausalVerdict.NECESSARY_FOR_OBSERVED_FAILURE)
        self.assertEqual(evidence.seed, self.seed)
        self.assertTrue(len(evidence.per_candidate_evidence) > 0)
        
        self.assertTrue(len(evidence.dependency_path) > 0)
        self.assertIsInstance(evidence.dependency_path, tuple)
        self.assertEqual(evidence.dependency_path, (
            "Clinic",
            "Lab Order Service",
            "Specimen Processing Service",
            "LIS Gateway",
            "Results Service",
            "Results Database"
        ))
        self.assertIsNotNone(evidence.divergence_event_id)
        self.assertEqual(len(evidence.limitation_flags), 0)

    def test_b_trace_derived_path(self):
        """Test B: Prove the path is derived from traces and not hardcoded to CF-001."""
        investigation_mock = copy.deepcopy(self.investigation)
        analysis_mock = copy.deepcopy(self.analysis)
        
        # Manipulate the counterfactual trace to have a completely different topology path
        cf = next(c for c in investigation_mock.counterfactual_results 
                  if c.configuration.disabled_candidate_id == "NET-004")
        
        # Override the events with a fake alternative path
        fake_events = [
            SimulationEvent(event_id="e1", order=1, timestamp_offset_ms=0, service="Alpha", 
                            event_type=EventType.HOP_SUCCESS, message="", 
                            source_service="Alpha", destination_service="Beta"),
            SimulationEvent(event_id="e2", order=2, timestamp_offset_ms=10, service="Beta", 
                            event_type=EventType.HOP_SUCCESS, message="", 
                            source_service="Beta", destination_service="Gamma")
        ]
        cf.result.events = fake_events
        
        evidence = self.assembler.assemble(investigation_mock, analysis_mock)
        
        # The path should match the fake trace, proving it's trace-derived!
        self.assertEqual(evidence.dependency_path, ("Alpha", "Beta", "Gamma"))

    def test_c_no_causal_candidate(self):
        """Test C: NO_CAUSAL_CANDIDATE returns limitation and empty path."""
        analysis_mock = copy.deepcopy(self.analysis)
        analysis_mock.investigation_verdict = CausalVerdict.NO_CAUSAL_CANDIDATE
        
        evidence = self.assembler.assemble(self.investigation, analysis_mock)
        
        self.assertEqual(evidence.dependency_path, tuple())
        self.assertIn(LimitationFlag.NO_SINGLE_VERIFIED_DEPENDENCY_PATH, evidence.limitation_flags)

    def test_d_ambiguous(self):
        """Test D: AMBIGUOUS returns limitation and empty path."""
        analysis_mock = copy.deepcopy(self.analysis)
        analysis_mock.investigation_verdict = CausalVerdict.AMBIGUOUS
        
        evidence = self.assembler.assemble(self.investigation, analysis_mock)
        
        self.assertEqual(evidence.dependency_path, tuple())
        self.assertIn(LimitationFlag.NO_SINGLE_VERIFIED_DEPENDENCY_PATH, evidence.limitation_flags)

    def test_e_baseline_not_failed(self):
        """Test E: BASELINE_NOT_FAILED returns limitation and empty path."""
        analysis_mock = copy.deepcopy(self.analysis)
        analysis_mock.status = AnalysisStatus.BASELINE_NOT_FAILED
        analysis_mock.investigation_verdict = None
        
        evidence = self.assembler.assemble(self.investigation, analysis_mock)
        
        self.assertEqual(evidence.dependency_path, tuple())
        self.assertIn(LimitationFlag.NO_SINGLE_VERIFIED_DEPENDENCY_PATH, evidence.limitation_flags)

    def test_f_invalid_evidence(self):
        """Test F: INVALID_EVIDENCE returns limitation and empty path."""
        analysis_mock = copy.deepcopy(self.analysis)
        analysis_mock.status = AnalysisStatus.INVALID_EVIDENCE
        analysis_mock.investigation_verdict = None
        
        evidence = self.assembler.assemble(self.investigation, analysis_mock)
        
        self.assertEqual(evidence.dependency_path, tuple())
        self.assertIn(LimitationFlag.NO_SINGLE_VERIFIED_DEPENDENCY_PATH, evidence.limitation_flags)

    def test_g_no_simulator_replay_invocation(self):
        """Test G: Asserts SimulationEngine and ReplayEngine are completely bypassed."""
        with patch("crossfault.engine.SimulationEngine") as mock_sim, \
             patch("crossfault.replay.ReplayEngine") as mock_replay:
            
            evidence = self.assembler.assemble(self.investigation, self.analysis)
            
            mock_sim.assert_not_called()
            mock_replay.assert_not_called()
            self.assertEqual(evidence.causal_verdict, CausalVerdict.NECESSARY_FOR_OBSERVED_FAILURE)

    def test_h_evidence_determinism(self):
        """Test H: Evidence assembler is deterministic given the same inputs."""
        evidence1 = self.assembler.assemble(self.investigation, self.analysis)
        evidence2 = self.assembler.assemble(self.investigation, self.analysis)
        
        self.assertEqual(evidence1.to_dict(), evidence2.to_dict())

    def test_i_provenance(self):
        """Test I: Provenance divergence event matches actual recorded baseline event ID."""
        evidence = self.assembler.assemble(self.investigation, self.analysis)
        
        # Ensure the divergence_event_id is present
        self.assertIsNotNone(evidence.divergence_event_id)
        
        # Verify that it exists in the baseline trace
        matching_baseline_events = [e for e in self.investigation.baseline_result.events if e.event_id == evidence.divergence_event_id]
        self.assertTrue(len(matching_baseline_events) == 1)
        self.assertEqual(matching_baseline_events[0].candidate_id, "NET-004")

if __name__ == "__main__":
    unittest.main()
