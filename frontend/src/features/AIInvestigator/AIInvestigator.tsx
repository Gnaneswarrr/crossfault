import React from 'react';
import { Bot } from 'lucide-react';
import { AIInterpretation } from '../../api/types';
import './AIInvestigator.css';

export default function AIInvestigator({ interpretation }: { interpretation: AIInterpretation }) {
  if (!interpretation) return null;

  return (
    <div className="phase-container">
      <h3 className="phase-header">06 &mdash; INVESTIGATOR</h3>
      
      <div className="ai-container glass-panel">
        <div className="ai-disclaimer">
          <Bot size={18} />
          <span>AI Interpretation of Verified Evidence</span>
        </div>
        
        <div className="ai-body">
          <div className="ai-section">
            <h4 className="ai-section-title">NARRATIVE</h4>
            <p className="ai-text">{interpretation.narrative_explanation}</p>
          </div>
          
          <div className="ai-section">
            <h4 className="ai-section-title">NEGATIVE EVIDENCE EXPLANATION</h4>
            <p className="ai-text">{interpretation.negative_evidence_explanation}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
