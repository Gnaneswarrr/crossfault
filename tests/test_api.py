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


if __name__ == "__main__":
    unittest.main()
