import { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, CheckCircle2, XCircle } from 'lucide-react';
import type { VerifiedInvestigationEvidence } from '../../api/types';
import { getCategoryInfo } from '../../utils/candidateFormatter';
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
        <span className="lab-note">Visualizing bounded backend counterfactual replay experiments.</span>
      </div>

      <div className="lab-layout">
        {/* Baseline Card */}
        <div className="lab-baseline glass-panel">
          <div className="lab-title">BASELINE EXPERIMENT</div>
          <div className="baseline-state-badge">All candidates ON</div>
          <div className="baseline-flow-arrow">&darr;</div>
          <div className={`giant-outcome ${evidence.baseline_outcome.toLowerCase()}`}>
            {evidence.baseline_outcome}
          </div>
        </div>

        <div className="lab-divider">
          <span className="divider-text">TOGGLE OFF ONE CANDIDATE AT A TIME &rarr;</span>
        </div>

        {/* Counterfactual Replays List */}
        <div className="lab-experiments">
          <div className="lab-title">INDIVIDUAL COUNTERFACTUAL REPLAYS</div>
          <div className="experiments-list">
            {evidence.per_candidate_evidence.map((candidate, i) => {
              const changed = candidate.outcome_changed;
              const isNecessary = candidate.candidate_conclusion === 'NECESSARY_FOR_OBSERVED_FAILURE' || candidate.candidate_id === evidence.necessary_candidate;
              const category = getCategoryInfo(candidate.candidate_type);
              const Icon = category.icon;

              return (
                <motion.div 
                  key={candidate.candidate_id} 
                  className={`experiment-row glass-panel ${changed ? 'outcome-changed' : ''}`}
                  initial={{ opacity: 1, x: 0 }}
                  animate={isPlaying ? { 
                    opacity: [0, 1],
                    x: [20, 0],
                    transition: { delay: i * 0.3, duration: 0.4 }
                  } : {}}
                >
                  <div className="exp-meta">
                    <div className={`category-pill ${category.badgeClass}`}>
                      <Icon size={13} />
                      <span>{category.label}</span>
                    </div>
                    <span className="candidate-id-badge mono">{candidate.candidate_id}</span>
                    <span className="candidate-name">{candidate.candidate_name}</span>
                  </div>

                  <div className="exp-toggle-state">
                    <span className="state-on">ON</span>
                    <span className="arrow">&rarr;</span>
                    <span className="state-off">OFF</span>
                  </div>

                  <div className="exp-outcome-group">
                    <span className="arrow">&rarr;</span>
                    <div className={`exp-outcome ${candidate.counterfactual_status.toLowerCase()}`}>
                      {candidate.counterfactual_status === 'SUCCESS' ? (
                        <CheckCircle2 size={16} />
                      ) : (
                        <XCircle size={16} />
                      )}
                      <span>{candidate.counterfactual_status}</span>
                    </div>
                  </div>

                  {changed && (
                    <div className="exp-badges">
                      <span className="badge outcome-changed-badge">✓ OUTCOME CHANGED</span>
                      {isNecessary && (
                        <span className="badge necessary-candidate-badge">✓ NECESSARY CANDIDATE</span>
                      )}
                    </div>
                  )}
                  {!changed && (
                    <div className="exp-badges">
                      <span className="badge unchanged-badge">OUTCOME UNCHANGED</span>
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
