"""Tests for Phase 2 Counterfactual Replay Engine."""

import copy
import os
import sys
import unittest

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from crossfault.models import DeploymentStatus
from crossfault.replay import ReplayEngine
from crossfault.scenario import create_initial_scenario


class TestReplayEngine(unittest.TestCase):

    def setUp(self):
        self.scenario = create_initial_scenario()
        self.engine = ReplayEngine()
        self.seed = 48291

    def test_baseline_remains_failed(self):
        """1. Baseline remains FAILED."""
        result = self.engine.run(self.scenario, self.seed)
        self.assertEqual(result.baseline_result.status, DeploymentStatus.FAILED)

    def test_exactly_one_replay_per_candidate(self):
        """2. Exactly one replay exists per declared candidate."""
        result = self.engine.run(self.scenario, self.seed)
        self.assertEqual(len(result.counterfactual_results), len(self.scenario.candidates))

    def test_replays_preserve_core_configuration(self):
        """5, 6, 7. All replays preserve application input, topology, and disable exactly one candidate."""
        result = self.engine.run(self.scenario, self.seed)
        
        for i, cf in enumerate(result.counterfactual_results):
            # Verify Application Input preserved
            self.assertEqual(cf.configuration.application_input, self.scenario.application_input)
            
            # Verify Topology preserved
            self.assertEqual(cf.configuration.topology_path, self.scenario.topology_path)
            
            # Verify exactly one candidate is disabled, and it matches the configuration disabled_candidate_id
            disabled_count = 0
            for candidate in cf.configuration.candidates:
                if not candidate.is_enabled:
                    disabled_count += 1
                    self.assertEqual(candidate.candidate_id, cf.configuration.disabled_candidate_id)
            
            self.assertEqual(disabled_count, 1)

    def test_cf001_expected_outcomes(self):
        """8. CF-001 produces the expected four outcomes (LIS -> SUCCESS, others -> FAILED)."""
        result = self.engine.run(self.scenario, self.seed)
        
        for cf in result.counterfactual_results:
            if cf.configuration.disabled_candidate_id == "NET-004":  # LIS_PATH_INTERRUPTION
                self.assertEqual(cf.result.status, DeploymentStatus.SUCCESS)
            else:
                self.assertEqual(cf.result.status, DeploymentStatus.FAILED)

    def test_original_scenario_is_not_mutated(self):
        """9. Original Scenario is not mutated. (Isolation test)"""
        original_copy = copy.deepcopy(self.scenario)
        self.engine.run(self.scenario, self.seed)
        
        self.assertEqual(self.scenario, original_copy)
        # Explicit check that all candidates are still enabled in original
        for candidate in self.scenario.candidates:
            self.assertTrue(candidate.is_enabled)

    def test_investigation_determinism(self):
        """11. Running the complete investigation twice produces equivalent results."""
        result1 = self.engine.run(self.scenario, self.seed)
        result2 = self.engine.run(self.scenario, self.seed)
        
        self.assertEqual(result1.to_dict(), result2.to_dict())

    def test_baseline_event_trace_determinism(self):
        """12. Baseline event traces are perfectly deterministic."""
        result1 = self.engine.run(self.scenario, self.seed)
        result2 = self.engine.run(self.scenario, self.seed)
        
        events1 = result1.baseline_result.events
        events2 = result2.baseline_result.events
        
        self.assertEqual(len(events1), len(events2))
        for e1, e2 in zip(events1, events2):
            self.assertEqual(e1.event_id, e2.event_id)
            self.assertEqual(e1.order, e2.order)
            self.assertEqual(e1.timestamp_offset_ms, e2.timestamp_offset_ms)
            self.assertEqual(e1.service, e2.service)
            self.assertEqual(e1.event_type, e2.event_type)
            self.assertEqual(e1.message, e2.message)
            self.assertEqual(e1.candidate_id, e2.candidate_id)
            self.assertEqual(e1.source_service, e2.source_service)
            self.assertEqual(e1.destination_service, e2.destination_service)
            self.assertEqual(e1.status, e2.status)

    def test_counterfactual_event_trace_isolation(self):
        """13. Counterfactual traces isolate behavior perfectly."""
        result = self.engine.run(self.scenario, self.seed)
        
        # Select two replays that both still fail (e.g., ROUTE_CHANGE and ACCESS_RULE_CHANGE disabled)
        cf1 = result.counterfactual_results[0]  # NET-001 disabled
        cf2 = result.counterfactual_results[1]  # NET-002 disabled
        
        events1 = cf1.result.events
        events2 = cf2.result.events
        
        self.assertEqual(len(events1), len(events2))
        
        for e1, e2 in zip(events1, events2):
            self.assertEqual(e1.order, e2.order)
            self.assertEqual(e1.timestamp_offset_ms, e2.timestamp_offset_ms)
            self.assertEqual(e1.service, e2.service)
            self.assertEqual(e1.event_type, e2.event_type)
            self.assertEqual(e1.message, e2.message)
            
            # The only difference should be the status of the specific candidate evaluation
            if e1.candidate_id in ["NET-001", "NET-002"]:
                if e1.candidate_id == cf1.configuration.disabled_candidate_id:
                    self.assertEqual(e1.status, "DISABLED")
                    self.assertEqual(e2.status, "PASS")
                elif e1.candidate_id == cf2.configuration.disabled_candidate_id:
                    self.assertEqual(e1.status, "PASS")
                    self.assertEqual(e2.status, "DISABLED")
            else:
                self.assertEqual(e1.status, e2.status)


    def test_cf002_expected_outcomes(self):
        from crossfault.scenario import create_cf002_scenario
        scenario2 = create_cf002_scenario()
        result = self.engine.run(scenario2, self.seed)

        self.assertEqual(result.baseline_result.status, DeploymentStatus.FAILED)

        for cf in result.counterfactual_results:
            if cf.configuration.disabled_candidate_id == "NET-014":  # ACCESS_RULE_CHANGE
                self.assertEqual(cf.result.status, DeploymentStatus.SUCCESS)
            else:
                self.assertEqual(cf.result.status, DeploymentStatus.FAILED)

    def test_cf002_investigation_determinism(self):
        from crossfault.scenario import create_cf002_scenario
        scenario2 = create_cf002_scenario()
        result1 = self.engine.run(scenario2, self.seed)
        result2 = self.engine.run(scenario2, self.seed)

        self.assertEqual(result1.to_dict(), result2.to_dict())

if __name__ == "__main__":
    unittest.main()
