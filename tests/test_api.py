"""Tests for CrossFault FastAPI backend."""

import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from crossfault.ai_layer import AIValidationError
from crossfault.api import app, get_service
from crossfault.service import InvestigationService

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        
        # We replace the global service instance with a mock for API boundary testing.
        # This ensures we don't hit the real ReplayEngine or Gemini LLM.
        self.mock_service = MagicMock(spec=InvestigationService)
        app.dependency_overrides[get_service] = lambda: self.mock_service
        
        # To override the global variable directly if dependency_overrides doesn't catch it
        # because we used a global getter in api.py:
        patcher = patch("crossfault.api.get_service", return_value=self.mock_service)
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_1_health_check(self):
        """1. /health returns HTTP 200."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_2_cf001_endpoint_works(self):
        """2. CF-001 endpoint works with a mocked service."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"verified_evidence": {"causal_candidate_id": "NET-004"}}
        self.mock_service.run_investigation.return_value = mock_response
        
        response = self.client.get("/api/investigate?scenario=CF-001")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"verified_evidence": {"causal_candidate_id": "NET-004"}})
        self.mock_service.run_investigation.assert_called_once_with(scenario_id="CF-001", seed=48291)

    def test_3_cf002_endpoint_works(self):
        """3. CF-002 endpoint works with a mocked service."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"verified_evidence": {"causal_candidate_id": "NET-014"}}
        self.mock_service.run_investigation.return_value = mock_response
        
        response = self.client.get("/api/investigate?scenario=CF-002")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"verified_evidence": {"causal_candidate_id": "NET-014"}})
        self.mock_service.run_investigation.assert_called_once_with(scenario_id="CF-002", seed=48291)

    def test_3b_cf004_endpoint_works(self):
        """3b. CF-004 endpoint works with a mocked service."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"verified_evidence": {"causal_candidate_id": "NET-033"}}
        self.mock_service.run_investigation.return_value = mock_response

        response = self.client.get("/api/investigate?scenario=CF-004")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"verified_evidence": {"causal_candidate_id": "NET-033"}})
        self.mock_service.run_investigation.assert_called_once_with(scenario_id="CF-004", seed=48291)

    def test_3c_cf005_endpoint_works(self):
        """3c. CF-005 endpoint works with a mocked service."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"verified_evidence": {"causal_candidate_id": "NET-043"}}
        self.mock_service.run_investigation.return_value = mock_response

        response = self.client.get("/api/investigate?scenario=CF-005")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"verified_evidence": {"causal_candidate_id": "NET-043"}})
        self.mock_service.run_investigation.assert_called_once_with(scenario_id="CF-005", seed=48291)

    def test_4_default_seed(self):
        """4. Default seed is 48291."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {}
        self.mock_service.run_investigation.return_value = mock_response
        
        self.client.get("/api/investigate")
        self.mock_service.run_investigation.assert_called_once_with(scenario_id="CF-001", seed=48291)

    def test_5_invalid_scenario_rejected(self):
        """5. Invalid scenario is rejected with 400."""
        response = self.client.get("/api/investigate?scenario=CF-999")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid scenario", response.json()["detail"])
        self.mock_service.run_investigation.assert_not_called()

    def test_6_service_runtime_failure(self):
        """6. Service runtime failure becomes a clean HTTP error."""
        self.mock_service.run_investigation.side_effect = RuntimeError("Upstream API is down")
        
        response = self.client.get("/api/investigate")
        
        self.assertEqual(response.status_code, 502)
        self.assertIn("Upstream API is down", response.json()["detail"])

    def test_7_ai_failure_returns_200_with_unavailable_state(self):
        """7. AI failure returns HTTP 200 with verified evidence and explicit AI-unavailable state."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "verified_evidence": {"necessary_candidate": "NET-004"},
            "ai_interpretation": None,
            "ai_recommendations": None,
            "ai_status": "unavailable",
            "ai_error": "AI interpretation unavailable: provider quota or availability limit."
        }
        self.mock_service.run_investigation.return_value = mock_response
        
        response = self.client.get("/api/investigate")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ai_status"], "unavailable")
        self.assertIsNone(data["ai_interpretation"])
        self.assertIsNone(data["ai_recommendations"])
        self.assertEqual(data["verified_evidence"]["necessary_candidate"], "NET-004")

    def test_8_response_separation(self):
        """8. Response clearly separates verified evidence from AI interpretation/recommendations."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "verified_evidence": {"causal_candidate_id": "NET-004"},
            "ai_interpretation": {"narrative_explanation": "Test explanation"},
            "ai_recommendations": {"remediation_steps": ["Step 1"]}
        }
        self.mock_service.run_investigation.return_value = mock_response
        
        response = self.client.get("/api/investigate")
        data = response.json()
        
        self.assertIn("verified_evidence", data)
        self.assertIn("ai_interpretation", data)
        self.assertIn("ai_recommendations", data)
        self.assertEqual(data["verified_evidence"]["causal_candidate_id"], "NET-004")
        self.assertEqual(data["ai_interpretation"]["narrative_explanation"], "Test explanation")
        self.assertEqual(data["ai_recommendations"]["remediation_steps"], ["Step 1"])

    def test_9_api_uses_service_layer(self):
        """9. API route uses InvestigationService rather than directly running engines."""
        # This is implicitly proven by the fact that overriding the service mock
        # prevents the real engines from running, and the mock receives the calls.
        self.client.get("/api/investigate")
        self.mock_service.run_investigation.assert_called_once()

    def test_10_path_disclosure_prevention_in_502_error(self):
        """10. Unanticipated exceptions strip absolute filesystem paths from 502 detail."""
        self.mock_service.run_investigation.side_effect = RuntimeError(
            "Failed reading configuration file at C:\\Users\\hp\\secret\\data.json"
        )
        response = self.client.get("/api/investigate")
        self.assertEqual(response.status_code, 502)
        detail = response.json()["detail"]
        self.assertNotIn("C:\\Users\\hp\\secret\\data.json", detail)
        self.assertIn("[path]", detail)

    def test_11_invalid_seed_input_handling(self):
        """11. Non-integer seed returns HTTP 422 validation error; negative seed handled cleanly."""
        # Non-integer seed string -> 422 Unprocessable Entity
        response_str = self.client.get("/api/investigate?seed=invalid_seed")
        self.assertEqual(response_str.status_code, 422)

        # Negative seed -> passed to service cleanly without crashing
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"verified_evidence": {}}
        self.mock_service.run_investigation.return_value = mock_response

        response_neg = self.client.get("/api/investigate?seed=-48291")
        self.assertEqual(response_neg.status_code, 200)
        self.mock_service.run_investigation.assert_called_with(scenario_id="CF-001", seed=-48291)

    def test_12_adversarial_scenario_strings(self):
        """12. Path traversal and script injection scenario inputs returned as 400 clean errors."""
        adversarial_scenarios = [
            "../../etc/passwd",
            "<script>alert(1)</script>",
            "CF-003",
            "ADMIN",
        ]
        for bad_scenario in adversarial_scenarios:
            response = self.client.get(f"/api/investigate?scenario={bad_scenario}")
            self.assertEqual(response.status_code, 400)
            self.assertIn("Invalid scenario", response.json()["detail"])
            # Ensure no stack trace or raw input reflection vulnerability
            self.assertNotIn("<script>", response.json()["detail"])
            self.assertNotIn("passwd", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
