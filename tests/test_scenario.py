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


if __name__ == "__main__":
    unittest.main()
