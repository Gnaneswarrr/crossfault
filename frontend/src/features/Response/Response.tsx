import { useState } from 'react';
import { CheckSquare, Square, CheckCircle2, AlertCircle } from 'lucide-react';
import type { AIRecommendations } from '../../api/types';
import './Response.css';

export default function ResponseChecklist({ recommendations }: { recommendations: AIRecommendations | null }) {
  const [checkedItems, setCheckedItems] = useState<Set<number>>(new Set());

  if (!recommendations || !recommendations.remediation_steps || recommendations.remediation_steps.length === 0) {
    return (
      <div className="phase-container">
        <h3 className="phase-header">07 &mdash; RESPONSE</h3>
        <div className="response-container glass-panel response-unavailable-panel">
          <div className="verified-complete-banner">
            <CheckCircle2 size={18} color="var(--color-verified, #00E676)" />
            <span>VERIFIED INVESTIGATION COMPLETE</span>
          </div>

          <div className="response-header warning">
            <AlertCircle size={18} />
            <div className="response-status-title-group">
              <span className="response-title">AI RECOMMENDATIONS</span>
              <span className="response-status-pill">Currently unavailable</span>
            </div>
          </div>

          <div className="response-body">
            <p className="response-unavailable-text">
              No AI-generated remediation recommendations were accepted.
            </p>
            <p className="response-unavailable-subtext">
              The AI is optional. Verified causal evidence remains available.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const toggleCheck = (index: number) => {
    const next = new Set(checkedItems);
    if (next.has(index)) {
      next.delete(index);
    } else {
      next.add(index);
    }
    setCheckedItems(next);
  };

  return (
    <div className="phase-container">
      <h3 className="phase-header">07 &mdash; RESPONSE</h3>
      
      <div className="response-container glass-panel">
        <div className="response-header">
          <span>AI RECOMMENDATIONS</span>
        </div>
        
        <div className="response-list">
          {recommendations.remediation_steps.map((step, index) => {
            const isChecked = checkedItems.has(index);
            return (
              <div 
                key={index} 
                className={`response-item ${isChecked ? 'checked' : ''}`}
                onClick={() => toggleCheck(index)}
              >
                <div className="checkbox-icon">
                  {isChecked ? <CheckSquare color="var(--color-success)" /> : <Square color="var(--text-secondary)" />}
                </div>
                <div className="step-text">{step}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
