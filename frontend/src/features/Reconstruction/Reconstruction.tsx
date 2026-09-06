import type { VerifiedInvestigationEvidence } from '../../api/types';
import { getCategoryInfo } from '../../utils/candidateFormatter';
import './Reconstruction.css';

export default function Reconstruction({ evidence }: { evidence: VerifiedInvestigationEvidence }) {
  return (
    <div className="phase-container">
      <h3 className="phase-header">02 &mdash; RECONSTRUCTION</h3>
      <p className="phase-description">Evaluating candidate network changes detected around the failure window.</p>
      
      <div className="reconstruction-grid">
        {evidence.per_candidate_evidence.map((candidate) => {
          const category = getCategoryInfo(candidate.candidate_type);
          const Icon = category.icon;

          return (
            <div key={candidate.candidate_id} className="candidate-card glass-panel">
              <div className="candidate-header">
                <div className={`category-pill ${category.badgeClass}`}>
                  <Icon size={14} />
                  <span>{category.label}</span>
                </div>
                <span className="candidate-id mono">{candidate.candidate_id}</span>
              </div>
              <div className="candidate-body">
                <strong className="candidate-name-text">{candidate.candidate_name}</strong>
                <div className="status-row">
                  <span className="status-label">BASELINE STATE</span>
                  <span className={`status-badge ${candidate.candidate_enabled_in_baseline ? 'active' : 'inactive'}`}>
                    {candidate.candidate_enabled_in_baseline ? 'ENABLED' : 'DISABLED'}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
