import React from 'react';
import { VerifiedInvestigationEvidence } from '../../api/types';
import './Incident.css';

export default function Incident({ evidence }: { evidence: VerifiedInvestigationEvidence }) {
  return (
    <div className="phase-container">
      <h3 className="phase-header">01 &mdash; INCIDENT</h3>
      
      <div className="incident-grid">
        <div className="incident-stat glass-panel">
          <div className="stat-label">OUTCOME</div>
          <div className="stat-value error">{evidence.baseline_outcome}</div>
        </div>
        <div className="incident-stat glass-panel">
          <div className="stat-label">SCENARIO ID</div>
          <div className="stat-value mono">{evidence.scenario_id}</div>
        </div>
        <div className="incident-stat glass-panel">
          <div className="stat-label">SEED</div>
          <div className="stat-value mono">{evidence.seed}</div>
        </div>
      </div>
      
      <div className="glass-panel incident-summary">
        <p>Deployment failed during execution of scenario <strong>{evidence.scenario_id}</strong>. The bounded investigation evaluates candidate network changes to determine individual necessity.</p>
      </div>
    </div>
  );
}
