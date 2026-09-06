import { Award, ShieldCheck, ArrowRight } from 'lucide-react';
import type { VerifiedInvestigationEvidence } from '../../api/types';
import { getCategoryInfo } from '../../utils/candidateFormatter';
import './InvestigationResult.css';

export default function InvestigationResult({ evidence }: { evidence: VerifiedInvestigationEvidence }) {
  const necessaryCandidateObj = evidence.per_candidate_evidence.find(
    (c) => c.candidate_id === evidence.necessary_candidate || c.outcome_changed
  );

  const candidateId = evidence.necessary_candidate || 'N/A';
  const candidateName = necessaryCandidateObj ? necessaryCandidateObj.candidate_name : 'Candidate';
  const candidateType = necessaryCandidateObj ? necessaryCandidateObj.candidate_type : 'LIS_PATH_INTERRUPTION';

  const category = getCategoryInfo(candidateType);
  const CategoryIcon = category.icon;

  return (
    <div className="phase-container">
      <h3 className="phase-header">FINAL &mdash; INVESTIGATION RESULT</h3>
      
      <div className="investigation-result-card glass-panel">
        <div className="result-header">
          <Award size={28} color="var(--color-verified, #00E676)" />
          <div className="result-header-text">
            <h4>INVESTIGATION RESULT</h4>
            <span className="result-subtitle">Dynamically derived from verified backend replay evidence</span>
          </div>
        </div>

        <div className="result-body">
          <div className="result-verdict-box">
            <div className="result-category-meta">
              <span className="result-meta-label">NECESSARY NETWORK CHANGE</span>
              <div className={`category-pill ${category.badgeClass}`} style={{ display: 'inline-flex', marginTop: '0.35rem' }}>
                <CategoryIcon size={14} />
                <span>{category.label}</span>
              </div>
            </div>

            <div className="result-candidate-title mono" style={{ marginTop: '0.85rem' }}>
              {candidateId} &mdash; {candidateName}
            </div>

            <p className="result-verdict-statement">
              is the necessary candidate for the observed failure under the bounded deterministic replay.
            </p>
          </div>

          <div className="result-grid">
            <div className="result-stat-box">
              <span className="stat-label">BASELINE OUTCOME</span>
              <span className={`stat-value mono ${evidence.baseline_outcome.toLowerCase()}`}>
                {evidence.baseline_outcome}
              </span>
            </div>

            <div className="result-stat-box">
              <span className="stat-label">COUNTERFACTUAL OUTCOME</span>
              <span className="stat-value mono success">
                {necessaryCandidateObj ? necessaryCandidateObj.counterfactual_status : 'SUCCESS'}
              </span>
            </div>

            <div className="result-stat-box">
              <span className="stat-label">CAUSAL VERDICT</span>
              <span className="stat-value mono verified-text">
                {evidence.causal_verdict || 'NECESSARY_FOR_OBSERVED_FAILURE'}
              </span>
            </div>
          </div>

          {evidence.dependency_path && evidence.dependency_path.length > 0 && (
            <div className="result-section">
              <span className="result-section-label">DEPENDENCY PATH</span>
              <div className="result-path-flow">
                {evidence.dependency_path.map((node, i) => (
                  <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className="result-path-node mono">{node}</span>
                    {i < evidence.dependency_path.length - 1 && (
                      <ArrowRight size={14} className="result-path-arrow" />
                    )}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="result-basis-box">
            <ShieldCheck size={16} color="var(--color-verified, #00E676)" />
            <span><strong>Evidence basis:</strong> Controlled replay + verified evidence</span>
          </div>
        </div>
      </div>
    </div>
  );
}
