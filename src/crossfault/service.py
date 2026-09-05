"""Service layer for CrossFault investigation orchestration."""

from typing import Optional
from crossfault.ai_layer import AIInvestigator, LLMClient, VerifiedAIResponse
from crossfault.analyzer import CausalAnalyzer
from crossfault.assembler import EvidenceAssembler
from crossfault.gemini_client import GeminiClient
from crossfault.replay import ReplayEngine
from crossfault.scenario import create_cf002_scenario, create_initial_scenario


class InvestigationService:
    """Centralizes investigation orchestration."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        if llm_client is None:
            llm_client = GeminiClient()
        self.ai_investigator = AIInvestigator(llm_client)
        self.replay_engine = ReplayEngine()
        self.analyzer = CausalAnalyzer()
        self.assembler = EvidenceAssembler()

    def run_investigation(self, scenario_id: str, seed: int = 48291) -> VerifiedAIResponse:
        """
        Runs the full deterministic investigation pipeline and AI interpretation.
        
        Args:
            scenario_id: Either 'CF-001' or 'CF-002'.
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
        else:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

        # Phase 2: Counterfactual Replay Investigation
        investigation_result = self.replay_engine.run(scenario=scenario, seed=seed)

        # Phase 3: Causal Analysis
        analysis_result = self.analyzer.analyze(investigation_result)

        # Phase 4: Verified Evidence Assembly
        verified_evidence = self.assembler.assemble(investigation_result, analysis_result)

        # Phase 5: AI Investigation
        return self.ai_investigator.investigate(scenario, verified_evidence)
