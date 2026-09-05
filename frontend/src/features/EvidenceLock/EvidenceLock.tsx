import React from 'react';
import { ShieldCheck, AlertTriangle } from 'lucide-react';
import { VerifiedInvestigationEvidence } from '../../api/types';
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
              Necessary for reproducing the observed failure under the bounded deterministic replay experiment.
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
