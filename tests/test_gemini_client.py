"""Tests for GeminiClient."""

import os
import unittest
from unittest.mock import patch, MagicMock

from crossfault.gemini_client import GeminiClient

class TestGeminiClient(unittest.TestCase):

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"})
    @patch("crossfault.gemini_client.genai.Client")
    def test_gemini_generate_json_success(self, mock_client_class):
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.text = '{"causal_candidate_id": "NET-014"}'
        mock_client_instance.models.generate_content.return_value = mock_response
        
        client = GeminiClient()
        result = client.generate_json("Prompt", {"payload": "data"})
        
        self.assertEqual(result, '{"causal_candidate_id": "NET-014"}')
        mock_client_instance.models.generate_content.assert_called_once()
        
    @patch.dict(os.environ, clear=True)
    def test_missing_api_key_raises_error(self):
        with self.assertRaisesRegex(RuntimeError, "GEMINI_API_KEY environment variable is not set"):
            GeminiClient()

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"})
    @patch("crossfault.gemini_client.genai.Client")
    def test_empty_response_raises_error(self, mock_client_class):
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.text = ""
        mock_client_instance.models.generate_content.return_value = mock_response
        
        client = GeminiClient()
        with self.assertRaisesRegex(RuntimeError, "Empty response received from Gemini API"):
            client.generate_json("Prompt", {})
            
    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"})
    @patch("crossfault.gemini_client.genai.Client")
    def test_api_exception_handled_safely(self, mock_client_class):
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        
        mock_client_instance.models.generate_content.side_effect = Exception("Network Error")
        
        client = GeminiClient()
        with self.assertRaisesRegex(RuntimeError, "Gemini API Error: Network Error"):
            client.generate_json("Prompt", {})

if __name__ == "__main__":
    unittest.main()
