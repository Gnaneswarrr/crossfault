import React, { useState } from 'react';
import { CheckSquare, Square } from 'lucide-react';
import { AIRecommendations } from '../../api/types';
import './Response.css';

export default function ResponseChecklist({ recommendations }: { recommendations: AIRecommendations }) {
  const [checkedItems, setCheckedItems] = useState<Set<number>>(new Set());

  if (!recommendations || recommendations.remediation_steps.length === 0) return null;

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
