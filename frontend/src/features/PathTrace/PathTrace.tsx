import React from 'react';
import { VerifiedInvestigationEvidence } from '../../api/types';
import './PathTrace.css';

export default function PathTrace({ evidence }: { evidence: VerifiedInvestigationEvidence }) {
  if (!evidence.dependency_path || evidence.dependency_path.length === 0) {
    return (
      <div className="phase-container">
        <h3 className="phase-header">04 &mdash; PATH TRACE</h3>
        <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          Dependency path unavailable for this investigation.
          {evidence.limitation_flags.length > 0 && (
            <div style={{ marginTop: '1rem', color: 'var(--color-warning)' }}>
              Limitations: {evidence.limitation_flags.join(', ')}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="phase-container">
      <h3 className="phase-header">04 &mdash; PATH TRACE</h3>
      
      <div className="path-trace-container glass-panel">
        <div className="path-trace-pipeline">
          {evidence.dependency_path.map((node, index) => {
            const isLast = index === evidence.dependency_path.length - 1;
            // A simple heuristic for visualization: put the divergence event near the middle or end
            const showDivergence = index === Math.max(0, evidence.dependency_path.length - 2);
            
            return (
              <React.Fragment key={index}>
                <div className="path-node">
                  <div className="node-circle"></div>
                  <div className="node-label">{node}</div>
                  
                  {showDivergence && evidence.divergence_event_id && (
                    <div className="divergence-provenance">
                      <div className="prov-header">DIVERGENCE PROVENANCE</div>
                      <div className="prov-id mono">{evidence.divergence_event_id}</div>
                    </div>
                  )}
                </div>
                {!isLast && (
                  <div className="path-edge">
                    <div className="edge-line"></div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}
