"""Service layer for CrossFault investigation orchestration."""

from typing import Optional
from crossfault.ai_layer import AIInvestigator, AIValidationError, LLMClient, VerifiedAIResponse
from crossfault.analyzer import CausalAnalyzer
from crossfault.assembler import EvidenceAssembler
from crossfault.gemini_client import GeminiClient
from crossfault.replay import ReplayEngine
from crossfault.scenario import (
    create_cf002_scenario,
    create_cf004_scenario,
    create_cf005_scenario,
    create_initial_scenario,
)


class InvestigationService:
    """Centralizes investigation orchestration."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self._llm_client = llm_client
        self._ai_investigator: Optional[AIInvestigator] = None
        if llm_client is not None:
            self._ai_investigator = AIInvestigator(llm_client)
        self.replay_engine = ReplayEngine()
        self.analyzer = CausalAnalyzer()
        self.assembler = EvidenceAssembler()

    @property
    def ai_investigator(self) -> Optional[AIInvestigator]:
        if self._ai_investigator is None:
            try:
                client = self._llm_client if self._llm_client is not None else GeminiClient()
                self._ai_investigator = AIInvestigator(client)
            except Exception:
                return None
        return self._ai_investigator

    def run_investigation(self, scenario_id: str, seed: int = 48291) -> VerifiedAIResponse:
        """
        Runs the full deterministic investigation pipeline and AI interpretation.
        
        Args:
            scenario_id: One of 'CF-001', 'CF-002', 'CF-004', 'CF-005'.
            seed: The deterministic seed for the simulator.
            
        Returns:
            VerifiedAIResponse: The validated AI response embedding the deterministic evidence.
            
        Raises:
            ValueError: If an unknown scenario_id is provided.
        """
        if scenario_id == "CF-002":
            scenario = create_cf002_scenario()
        elif scenario_id == "CF-001":
            scenario = create_initial_scenario()
        elif scenario_id == "CF-004":
            scenario = create_cf004_scenario()
        elif scenario_id == "CF-005":
            scenario = create_cf005_scenario()
        else:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

        # Phase 2: Counterfactual Replay Investigation
        investigation_result = self.replay_engine.run(scenario=scenario, seed=seed)

        # Phase 3: Causal Analysis
        analysis_result = self.analyzer.analyze(investigation_result)

        # Phase 4: Verified Evidence Assembly
        verified_evidence = self.assembler.assemble(investigation_result, analysis_result)

        # Phase 5: AI Investigation
        try:
            investigator = self.ai_investigator
            if investigator is None:
                raise RuntimeError("AI client unavailable")
            return investigator.investigate(scenario, verified_evidence)
        except AIValidationError as e:
            return VerifiedAIResponse(
                verified_evidence=verified_evidence,
                ai_interpretation=None,
                ai_recommendations=None,
                ai_status="unavailable",
                ai_error="AI interpretation unavailable: response failed verification boundary.",
            )
        except Exception:
            return VerifiedAIResponse(
                verified_evidence=verified_evidence,
                ai_interpretation=None,
                ai_recommendations=None,
                ai_status="unavailable",
                ai_error="AI interpretation unavailable: provider quota or availability limit.",
            )
