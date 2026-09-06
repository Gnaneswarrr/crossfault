export type DeploymentStatus = 'SUCCESS' | 'FAILED';
export type CandidateType = 'ROUTE_CHANGE' | 'ACCESS_RULE_CHANGE' | 'DNS_CHANGE' | 'LIS_PATH_INTERRUPTION';
export type CausalVerdict = 'NECESSARY_FOR_OBSERVED_FAILURE' | 'NOT_NECESSARY' | 'NO_CAUSAL_CANDIDATE' | 'AMBIGUOUS';
export type AnalysisStatus = 'VALID' | 'BASELINE_NOT_FAILED' | 'INVALID_EVIDENCE';
export type LimitationFlag = 'NO_SINGLE_VERIFIED_DEPENDENCY_PATH';

export interface CandidateEvidence {
  scenario_id: string;
  seed: number;
  candidate_id: string;
  candidate_type: CandidateType;
  candidate_name: string;
  candidate_enabled_in_baseline: boolean;
  candidate_enabled_in_counterfactual: boolean;
  baseline_status: DeploymentStatus;
  counterfactual_status: DeploymentStatus;
  outcome_changed: boolean;
  affected_path: string[];
  candidate_conclusion: CausalVerdict;
}

export interface VerifiedInvestigationEvidence {
  scenario_id: string;
  seed: number;
  analysis_status: AnalysisStatus;
  causal_verdict: CausalVerdict | null;
  baseline_outcome: DeploymentStatus;
  per_candidate_evidence: CandidateEvidence[];
  necessary_candidate: string | null;
  dependency_path: string[];
  divergence_event_id: string | null;
  limitation_flags: LimitationFlag[];
}

export interface AIInterpretation {
  narrative_explanation: string;
  negative_evidence_explanation: string;
}

export interface AIRecommendations {
  remediation_steps: string[];
}

export interface VerifiedAIResponse {
  verified_evidence: VerifiedInvestigationEvidence;
  ai_interpretation: AIInterpretation | null;
  ai_recommendations: AIRecommendations | null;
  ai_status?: string;
  ai_error?: string | null;
}
