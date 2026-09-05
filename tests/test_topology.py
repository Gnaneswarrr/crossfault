"""Tests for topology structure and hop verification."""

import os
import sys
import unittest

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from crossfault.scenario import HEALTHCARE_TOPOLOGY_PATH, create_initial_scenario
from crossfault.topology import ServiceTopology


class TestTopology(unittest.TestCase):

    def test_4_topology_is_correct(self):
        """Test 4: Verify expected healthcare service topology path exists."""
        expected_path = [
            "Clinic",
            "Lab Order Service",
            "Specimen Processing Service",
            "LIS Gateway",
            "Results Service",
            "Results Database",
        ]

        scenario = create_initial_scenario()
        self.assertEqual(scenario.topology_path, expected_path)

        topology = ServiceTopology(scenario.topology_path)
        self.assertEqual(topology.path, expected_path)

        expected_hops = [
            ("Clinic", "Lab Order Service"),
            ("Lab Order Service", "Specimen Processing Service"),
            ("Specimen Processing Service", "LIS Gateway"),
            ("LIS Gateway", "Results Service"),
            ("Results Service", "Results Database"),
        ]

        self.assertEqual(topology.get_hops(), expected_hops)
        for src, dst in expected_hops:
            self.assertTrue(topology.contains_hop(src, dst))


if __name__ == "__main__":
    unittest.main()
