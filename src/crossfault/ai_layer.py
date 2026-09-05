"""Phase 5: AI Investigator and AI Output Validator."""

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Protocol

from crossfault.models import Scenario, VerifiedInvestigationEvidence


class AIValidationError(Exception):
    """Raised when the AI output violates the deterministic evidence boundary or schema."""
    pass


@dataclass(frozen=True)
class AIInterpretation:
    """The AI's semantic explanation of the deterministic facts."""
    narrative_explanation: str
    negative_evidence_explanation: str


@dataclass(frozen=True)
class AIRecommendations:
    """The AI's suggested remediation steps (NOT verified causal evidence)."""
    remediation_steps: List[str]


@dataclass(frozen=True)
class VerifiedAIResponse:
    """
    The final, structurally validated response containing the strictly separated
    verified evidence, interpretation, and recommendations.
    """
    verified_evidence: VerifiedInvestigationEvidence
    ai_interpretation: AIInterpretation
    ai_recommendations: AIRecommendations


class LLMClient(Protocol):
    """Injectable interface for LLM providers."""
    def generate_json(self, prompt: str, payload: dict) -> str:
        ...


class EvidenceSummarizer:
    """Extracts a compact, structured payload for the LLM without sending raw traces."""

    @staticmethod
    def summarize(scenario: Scenario, evidence: VerifiedInvestigationEvidence) -> Dict[str, Any]:
        return {
            "scenario_id": scenario.scenario_id,
            "scenario_description": scenario.description,
            "application_input": scenario.application_input.to_dict(),
            "causal_verdict": evidence.causal_verdict.name if evidence.causal_verdict else None,
            "identified_necessary_candidate": evidence.necessary_candidate,
            "baseline_outcome": evidence.baseline_outcome.value,
            "verified_dependency_path": list(evidence.dependency_path),
            "divergence_event_id": evidence.divergence_event_id,
            "candidates": [
                {
                    "candidate_id": ce.candidate_id,
                    "type": ce.candidate_type.value,
                    "description": ce.candidate_name,
                    "counterfactual_outcome": ce.counterfactual_status.value,
                    "outcome_changed": ce.outcome_changed,
                }
                for ce in evidence.per_candidate_evidence
            ],
            "experiment_bound": "Necessary for reproducing the observed failure under the bounded deterministic replay experiment."
        }


class AIOutputValidator:
    """Enforces deterministic boundaries on LLM output."""

    @staticmethod
    def validate(llm_response_text: str, evidence: VerifiedInvestigationEvidence) -> VerifiedAIResponse:
        # 1. Parse JSON safely, stripping markdown fences if present
        text = llm_response_text.strip()
        if text.startswith("```"):
            # Try to extract content between fences
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                text = match.group(1)
            else:
                text = text.lstrip("`json").lstrip("`").rstrip("`")
                
        # Clean up any trailing backticks just in case
        text = text.strip().rstrip("`").strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            raise AIValidationError(f"Malformed JSON returned by AI: {e}")

        # 2. Check required fields
        required_keys = {
            "causal_candidate_id", "causal_verdict", "dependency_path",
            "narrative_explanation", "negative_evidence_explanation", "remediation_steps"
        }
        missing_keys = required_keys - set(parsed.keys())
        if missing_keys:
            raise AIValidationError(f"Missing required keys in AI response: {missing_keys}")

        # 3. Check field types
        if not isinstance(parsed["dependency_path"], list):
            raise AIValidationError("'dependency_path' must be a list")
        if not isinstance(parsed["remediation_steps"], list):
            raise AIValidationError("'remediation_steps' must be a list")
        if not isinstance(parsed["narrative_explanation"], str):
            raise AIValidationError("'narrative_explanation' must be a string")
        if not isinstance(parsed["negative_evidence_explanation"], str):
            raise AIValidationError("'negative_evidence_explanation' must be a string")

        # 4. Enforce deterministic boundaries (reject contradictions)
        if parsed["causal_candidate_id"] != evidence.necessary_candidate:
            raise AIValidationError(
                f"AI halluincated/contradicted necessary candidate. "
                f"Expected '{evidence.necessary_candidate}', got '{parsed['causal_candidate_id']}'"
            )

        if evidence.causal_verdict:
            if parsed["causal_verdict"] != evidence.causal_verdict.value:
                raise AIValidationError(
                    f"AI contradicted causal verdict. "
                    f"Expected '{evidence.causal_verdict.value}', got '{parsed['causal_verdict']}'"
                )
        else:
            if parsed["causal_verdict"] is not None:
                raise AIValidationError("AI provided a causal verdict but evidence has none.")

        if parsed["dependency_path"] != list(evidence.dependency_path):
            raise AIValidationError(
                f"AI contradicted dependency path. "
                f"Expected {list(evidence.dependency_path)}, got {parsed['dependency_path']}"
            )

        # Build separated verified response
        interpretation = AIInterpretation(
            narrative_explanation=parsed["narrative_explanation"],
            negative_evidence_explanation=parsed["negative_evidence_explanation"],
        )
        recommendations = AIRecommendations(
            remediation_steps=parsed["remediation_steps"]
        )

        return VerifiedAIResponse(
            verified_evidence=evidence,
            ai_interpretation=interpretation,
            ai_recommendations=recommendations,
        )


class AIInvestigator:
    """Orchestrates the investigation without determining causality."""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def investigate(self, scenario: Scenario, evidence: VerifiedInvestigationEvidence) -> VerifiedAIResponse:
        prompt = (
            "You are an AI investigator explaining a deterministic causal replay experiment. "
            "Explain the failure and provide remediations. Do NOT invent a causal candidate. "
            "Do NOT change the causal verdict. Do NOT invent a dependency path. "
            "Respond strictly in JSON matching the required schema."
        )
        payload = EvidenceSummarizer.summarize(scenario, evidence)
        llm_response = self.llm_client.generate_json(prompt, payload)
        
        return AIOutputValidator.validate(llm_response, evidence)
