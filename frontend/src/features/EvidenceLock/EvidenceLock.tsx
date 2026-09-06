import { ShieldCheck, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import type { VerifiedInvestigationEvidence } from '../../api/types';
import { getCategoryInfo } from '../../utils/candidateFormatter';
import './EvidenceLock.css';

export default function EvidenceLock({ evidence }: { evidence: VerifiedInvestigationEvidence }) {
  const isAmbiguous = evidence.causal_verdict === 'AMBIGUOUS';
  const hasNoCandidate = evidence.causal_verdict === 'NO_CAUSAL_CANDIDATE';

  return (
    <div className="phase-container">
      <h3 className="phase-header">05 &mdash; EVIDENCE LOCK</h3>
      
      <div className="evidence-certificate glass-panel">
        <div className="cert-header">
          <ShieldCheck color="var(--color-verified)" size={32} />
          <span>VERIFIED EVIDENCE FROM BOUNDED REPLAY EXPERIMENT</span>
        </div>
        
        <div className="cert-body">
          {evidence.limitation_flags.length > 0 && (
            <div className="cert-warning">
              <AlertTriangle size={16} />
              <span>Limitations present: {evidence.limitation_flags.join(', ')}</span>
            </div>
          )}

          <div className="cert-row">
            <div className="cert-label">CAUSAL VERDICT</div>
            <div className={`cert-value mono ${isAmbiguous || hasNoCandidate ? 'warning-text' : 'verified-text'}`}>
              {evidence.causal_verdict || 'NONE'}
            </div>
          </div>
          
          <div className="cert-row">
            <div className="cert-label">NECESSARY CANDIDATE</div>
            <div className="cert-value mono">
              {evidence.necessary_candidate || 'N/A'}
            </div>
          </div>

          <div className="cert-row">
            <div className="cert-label">EXPERIMENT BOUND</div>
            <div className="cert-value bound-text">
              "Necessary for reproducing the observed failure under the bounded deterministic replay experiment."
            </div>
          </div>

          {/* Compact Evidence Summary Matrix */}
          <div className="evidence-matrix-box">
            <div className="cert-label">EXPERIMENTAL REPLAY MATRIX</div>
            <div className="matrix-rows">
              <div className="matrix-item baseline-row">
                <span className="matrix-label mono">Baseline (All ON)</span>
                <span className="matrix-arrow">&rarr;</span>
                <span className={`matrix-outcome ${evidence.baseline_outcome.toLowerCase()}`}>
                  {evidence.baseline_outcome}
                </span>
              </div>

              {evidence.per_candidate_evidence.map((candidate) => {
                const isSelected = candidate.outcome_changed || candidate.candidate_id === evidence.necessary_candidate;
                const category = getCategoryInfo(candidate.candidate_type);
                const Icon = category.icon;

                return (
                  <div
                    key={candidate.candidate_id}
                    className={`matrix-item ${isSelected ? 'matrix-item-selected' : ''}`}
                  >
                    <span className="matrix-label mono">{candidate.candidate_id} OFF</span>
                    <div className={`category-pill ${category.badgeClass}`} style={{ fontSize: '0.68rem', padding: '0.15rem 0.5rem' }}>
                      <Icon size={12} />
                      <span>{category.shortLabel}</span>
                    </div>
                    <span className="matrix-arrow">&rarr;</span>
                    <span className={`matrix-outcome ${candidate.counterfactual_status.toLowerCase()}`}>
                      {candidate.counterfactual_status === 'SUCCESS' ? (
                        <CheckCircle2 size={14} />
                      ) : (
                        <XCircle size={14} />
                      )}
                      <span>{candidate.counterfactual_status}</span>
                    </span>
                    {isSelected && (
                      <span className="matrix-badge">✓ CAUSAL CANDIDATE</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
          
          {isAmbiguous && (
            <div className="cert-disclaimer">
              Multiple candidates changed the observed outcome. Individual necessity cannot be established by this experiment. Joint-causality analysis is outside the current experiment boundary.
            </div>
          )}
          
          {hasNoCandidate && (
            <div className="cert-disclaimer">
              No individual candidate was necessary for reproducing the observed failure under this experiment.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
