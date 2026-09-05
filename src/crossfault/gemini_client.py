"""Gemini LLM Provider Adapter."""

import json
import os
from google import genai
from google.genai import types

class GeminiClient:
    """A real LLM provider adapter using Google Gemini SDK."""

    def __init__(self, model: str = "gemini-3.6-flash"):
        # The genai SDK will automatically look for GEMINI_API_KEY in os.environ.
        # We enforce its presence to prevent silent fallback failures.
        if "GEMINI_API_KEY" not in os.environ:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set.")
        
        self.client = genai.Client()
        self.model = model

    def generate_json(self, prompt: str, payload: dict) -> str:
        """
        Sends the payload to Gemini and requests a structured JSON response.
        """
        full_prompt = (
            f"{prompt}\n\n"
            "CRITICAL RULES:\n"
            "1. Causal truth comes strictly from the supplied verified evidence payload.\n"
            "2. DO NOT invent candidates.\n"
            "3. DO NOT invent dependency paths. Copy the path exactly as provided.\n"
            "4. Reproduce structured facts exactly.\n"
            "5. Explain negative evidence (why other candidates were not causal based on outcome_changed being false).\n"
            "6. Remediation is recommendation only. Do not claim remediation was experimentally verified.\n"
            "7. Do not claim universal causality.\n"
            "8. Do not claim joint causality unless explicitly represented in verified evidence.\n\n"
            "Input Evidence Payload:\n"
            f"{json.dumps(payload, indent=2)}\n\n"
            "Provide your response STRICTLY as a JSON object matching exactly this schema:\n"
            "{\n"
            '  "causal_candidate_id": "string",\n'
            '  "causal_verdict": "string",\n'
            '  "dependency_path": ["string", "string"],\n'
            '  "narrative_explanation": "string",\n'
            '  "negative_evidence_explanation": "string",\n'
            '  "remediation_steps": ["string", "string"]\n'
            "}"
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0  # Zero temperature for deterministic adherence
                )
            )
            
            if not response.text:
                raise RuntimeError("Empty response received from Gemini API.")
                
            return response.text
            
        except Exception as e:
            # We catch network/API errors and wrap them to prevent silent failures.
            # We do NOT expose the raw exception directly if it risks leaking tokens,
            # though standard SDK exceptions are usually safe.
            raise RuntimeError(f"Gemini API Error: {str(e)}")
