"""Tests for initial demonstration scenario CF-001."""

import os
import sys
import unittest

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from crossfault.engine import SimulationEngine
from crossfault.models import DeploymentStatus, EventType
from crossfault.scenario import create_initial_scenario


class TestScenario(unittest.TestCase):

    def test_2_initial_scenario_fails(self):
        """Test 2: Initial scenario expected result status = FAILED."""
        scenario = create_initial_scenario()
        engine = SimulationEngine(scenario=scenario, seed=48291)
        result = engine.run()

        self.assertEqual(result.status, DeploymentStatus.FAILED)

    def test_3_failure_involves_lis_path(self):
        """Test 3: Failure involves LIS path.
        Expected:
        - Event log identifies LIS_PATH_INTERRUPTION candidate (NET-004)
        - Affected path includes LIS Gateway
        """
        scenario = create_initial_scenario()
        engine = SimulationEngine(scenario=scenario, seed=48291)
        result = engine.run()

        # Verify failure path includes LIS Gateway
        self.assertIn("LIS Gateway", result.failure_path)

        # Verify event log contains candidate NET-004 / LIS_PATH_INTERRUPTION failure event
        lis_events = [
            event for event in result.events
            if event.candidate_id == "NET-004" or event.event_type == EventType.HOP_FAILURE
        ]

        self.assertTrue(len(lis_events) > 0)

        failure_event = lis_events[-1]
        self.assertEqual(failure_event.event_type, EventType.HOP_FAILURE)
        self.assertEqual(failure_event.candidate_id, "NET-004")
        self.assertEqual(failure_event.source_service, "Specimen Processing Service")
        self.assertEqual(failure_event.destination_service, "LIS Gateway")
        self.assertIn("LIS Gateway", failure_event.message)
        self.assertIn("NET-004", failure_event.message)

    def test_cf002_initialization(self):
        from crossfault.scenario import create_cf002_scenario, AUTH_TOPOLOGY_PATH
        scenario = create_cf002_scenario()
        self.assertEqual(scenario.scenario_id, "CF-002")
        self.assertEqual(scenario.application_input.workload_type, "PhysicianLogin")
        self.assertEqual(scenario.topology_path, AUTH_TOPOLOGY_PATH)
        self.assertEqual(len(scenario.candidates), 4)

        # Check Candidate IDs and Types
        candidate_ids = [c.candidate_id for c in scenario.candidates]
        self.assertEqual(candidate_ids, ["NET-011", "NET-012", "NET-013", "NET-014"])

        net_014 = next(c for c in scenario.candidates if c.candidate_id == "NET-014")
        self.assertEqual(net_014.candidate_type.value, "ACCESS_RULE_CHANGE")
        self.assertTrue(net_014.interrupts_path)

if __name__ == "__main__":
    unittest.main()
