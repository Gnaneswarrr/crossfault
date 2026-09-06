import { Bot, CheckCircle2, AlertCircle } from 'lucide-react';
import type { AIInterpretation } from '../../api/types';
import './AIInvestigator.css';

export default function AIInvestigator({ interpretation }: { interpretation: AIInterpretation | null }) {
  if (!interpretation) {
    return (
      <div className="phase-container">
        <h3 className="phase-header">06 &mdash; INVESTIGATOR</h3>
        <div className="ai-container glass-panel ai-unavailable-panel">
          <div className="verified-complete-banner">
            <CheckCircle2 size={18} color="var(--color-verified, #00E676)" />
            <span>VERIFIED INVESTIGATION COMPLETE</span>
          </div>

          <div className="ai-disclaimer warning">
            <AlertCircle size={18} />
            <div className="ai-status-title-group">
              <span className="ai-title">AI INTERPRETATION</span>
              <span className="ai-status-pill">Currently unavailable</span>
            </div>
          </div>
          <div className="ai-body">
            <p className="ai-unavailable-text">
              The deterministic investigation and verified evidence remain available.
            </p>
            <p className="ai-unavailable-subtext">
              The AI is optional. Verified causal evidence remains available.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="phase-container">
      <h3 className="phase-header">06 &mdash; INVESTIGATOR</h3>
      
      <div className="ai-container glass-panel">
        <div className="ai-disclaimer">
          <Bot size={18} />
          <div className="ai-header-text">
            <span>AI Interpretation of Verified Evidence</span>
            <span className="ai-subtitle">
              AI explains verified replay evidence; it does not create or override the causal verdict.
            </span>
          </div>
        </div>
        
        <div className="ai-body">
          <div className="ai-section">
            <h4 className="ai-section-title">WHAT HAPPENED?</h4>
            <p className="ai-text">{interpretation.narrative_explanation}</p>
          </div>
          
          <div className="ai-section">
            <h4 className="ai-section-title">WHY THIS CANDIDATE?</h4>
            <p className="ai-text">{interpretation.negative_evidence_explanation}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
