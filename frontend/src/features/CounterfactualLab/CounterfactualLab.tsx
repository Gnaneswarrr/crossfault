import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play } from 'lucide-react';
import { VerifiedInvestigationEvidence } from '../../api/types';
import './CounterfactualLab.css';

export default function CounterfactualLab({ evidence }: { evidence: VerifiedInvestigationEvidence }) {
  const [isPlaying, setIsPlaying] = useState(false);
  
  const handleProveIt = () => {
    setIsPlaying(false);
    setTimeout(() => setIsPlaying(true), 100);
  };

  return (
    <div className="phase-container">
      <h3 className="phase-header">03 &mdash; COUNTERFACTUAL LAB</h3>
      
      <div className="lab-controls">
        <button className="run-button prove-it-btn" onClick={handleProveIt}>
          <Play size={16} /> PROVE IT ANIMATION
        </button>
        <span className="lab-note">Visualizing bounded backend experiments.</span>
      </div>

      <div className="lab-layout">
        <div className="lab-baseline">
          <div className="lab-title">BASELINE</div>
          <div className={`giant-outcome ${evidence.baseline_outcome.toLowerCase()}`}>
            {evidence.baseline_outcome}
          </div>
        </div>

        <div className="lab-divider">
          <span className="divider-text">REMOVE ONE CANDIDATE &rarr;</span>
        </div>

        <div className="lab-experiments">
          <div className="lab-title">COUNTERFACTUAL OUTCOME</div>
          <div className="experiments-list">
            {evidence.per_candidate_evidence.map((candidate, i) => {
              const changed = candidate.outcome_changed;
              return (
                <motion.div 
                  key={candidate.candidate_id} 
                  className={`experiment-row glass-panel ${changed ? 'outcome-changed' : ''}`}
                  initial={{ opacity: 1, x: 0 }}
                  animate={isPlaying ? { 
                    opacity: [0, 1],
                    x: [20, 0],
                    transition: { delay: i * 0.4, duration: 0.5 }
                  } : {}}
                >
                  <div className="exp-candidate">
                    <strong>Without:</strong> {candidate.candidate_name}
                  </div>
                  <div className="exp-arrow">&rarr;</div>
                  <div className={`exp-outcome ${candidate.counterfactual_status.toLowerCase()}`}>
                    {candidate.counterfactual_status}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
