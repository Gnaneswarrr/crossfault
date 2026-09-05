"""Tests for Phase 1 corrections: ApplicationInput and sequential Event IDs."""

import os
import sys
import unittest

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from crossfault.engine import SimulationEngine
from crossfault.models import ApplicationInput
from crossfault.scenario import create_initial_scenario


class TestCorrections(unittest.TestCase):

    def test_application_input_presence_and_immutability(self):
        """Verify scenario contains application input, it is preserved, and not mutated."""
        scenario = create_initial_scenario()
        
        # 1. Scenario contains expected deterministic application input
        self.assertIsInstance(scenario.application_input, ApplicationInput)
        self.assertEqual(scenario.application_input.request_id, "REQ-HC-10024")
        self.assertEqual(scenario.application_input.workload_type, "LabResultDeployment")
        self.assertEqual(scenario.application_input.target_environment, "Production")
        self.assertEqual(scenario.application_input.specimen_type, "BloodPanel")

        # Create a copy of the dictionary to check for mutation later
        original_dict = scenario.application_input.to_dict()

        engine = SimulationEngine(scenario=scenario, seed=48291)
        result = engine.run()

        # 2. SimulationResult preserves the same application input
        self.assertIsInstance(result.application_input, ApplicationInput)
        self.assertEqual(result.application_input.request_id, "REQ-HC-10024")

        # 3. Application input is not mutated during simulation
        self.assertEqual(result.application_input.to_dict(), original_dict)
        # Because dataclasses are frozen, mutation would fail anyway, but we explicitly test equivalence

    def test_event_ids_are_sequential_and_deterministic(self):
        """Verify event IDs are purely sequential and deterministic across runs."""
        scenario = create_initial_scenario()
        
        engine1 = SimulationEngine(scenario=scenario, seed=48291)
        result1 = engine1.run()

        # 4. Event IDs are sequential
        for i, event in enumerate(result1.events):
            expected_id = f"EV-{i + 1:03d}"
            self.assertEqual(event.event_id, expected_id)
            self.assertEqual(event.order, i + 1)

        # 5. Event IDs are deterministic across repeated runs
        engine2 = SimulationEngine(scenario=scenario, seed=48291)
        result2 = engine2.run()

        for ev1, ev2 in zip(result1.events, result2.events):
            self.assertEqual(ev1.event_id, ev2.event_id)
            self.assertEqual(ev1.order, ev2.order)


if __name__ == "__main__":
    unittest.main()
