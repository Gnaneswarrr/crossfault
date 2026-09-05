"""Tests for deterministic execution and seeded randomness isolation."""

import random
import unittest
import sys
import os

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from crossfault.engine import SimulationEngine
from crossfault.scenario import create_initial_scenario


class TestDeterminism(unittest.TestCase):

    def test_1_deterministic_execution(self):
        """Test 1: Run the same scenario twice with the same seed.
        Expected: same deployment result, equivalent event sequence.
        """
        seed = 48291
        scenario = create_initial_scenario()

        engine1 = SimulationEngine(scenario=scenario, seed=seed)
        result1 = engine1.run()

        engine2 = SimulationEngine(scenario=scenario, seed=seed)
        result2 = engine2.run()

        # 1. Deployment status must match
        self.assertEqual(result1.status, result2.status)

        # 2. Evaluated candidates and failure path must match
        self.assertEqual(result1.failure_path, result2.failure_path)
        self.assertEqual(len(result1.events), len(result2.events))

        # 3. Every event in the log sequence must be identical
        for e1, e2 in zip(result1.events, result2.events):
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

    def test_5_no_uncontrolled_randomness(self):
        """Test 5: Ensure simulation behavior comes strictly from the seeded simulation context.
        Mutating global random state before simulation run must NOT alter simulation output.
        """
        seed = 48291
        scenario = create_initial_scenario()

        # Baseline run
        engine_baseline = SimulationEngine(scenario=scenario, seed=seed)
        res_baseline = engine_baseline.run()

        # Mess up global random state
        random.seed(999999)
        _ = [random.random() for _ in range(100)]

        # Second run with same simulation seed
        engine_isolated = SimulationEngine(scenario=scenario, seed=seed)
        res_isolated = engine_isolated.run()

        # Verify identical output despite global random state mutations
        self.assertEqual(res_baseline.status, res_isolated.status)
        self.assertEqual(res_baseline.failure_path, res_isolated.failure_path)
        self.assertEqual(
            [e.to_dict() for e in res_baseline.events],
            [e.to_dict() for e in res_isolated.events],
        )


if __name__ == "__main__":
    unittest.main()
