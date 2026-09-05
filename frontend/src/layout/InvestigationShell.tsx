import React, { useState, useEffect } from 'react';
import { ShieldAlert, AlertTriangle } from 'lucide-react';
import { runInvestigation, APIError } from '../api/client';
import { VerifiedAIResponse } from '../api/types';

// Feature components
import Incident from '../features/Incident/Incident';
import Reconstruction from '../features/Reconstruction/Reconstruction';
import CounterfactualLab from '../features/CounterfactualLab/CounterfactualLab';
import PathTrace from '../features/PathTrace/PathTrace';
import EvidenceLock from '../features/EvidenceLock/EvidenceLock';
import AIInvestigator from '../features/AIInvestigator/AIInvestigator';
import ResponseChecklist from '../features/Response/Response';

// Core components
import { ErrorState } from '../components/LoadingError';
import LoadingSkeleton from '../components/LoadingError';

import './InvestigationShell.css';

export default function InvestigationShell() {
  const [scenario, setScenario] = useState('CF-001');
  const [seed, setSeed] = useState(48291);
  const [data, setData] = useState<VerifiedAIResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<{ status: number; message: string } | null>(null);
  const [activePhase, setActivePhase] = useState('01 INCIDENT');

  const navItems = [
    '01 INCIDENT',
    '02 RECONSTRUCTION',
    '03 COUNTERFACTUAL LAB',
    '04 PATH TRACE',
    '05 EVIDENCE LOCK',
    '06 INVESTIGATOR',
    '07 RESPONSE',
  ];

  const handleRunInvestigation = async () => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const result = await runInvestigation(scenario, seed);
      setData(result);
    } catch (err: any) {
      if (err instanceof APIError) {
        setError({ status: err.status, message: err.message });
      } else {
        setError({ status: 500, message: err.message || 'An unknown error occurred' });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleRunInvestigation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="shell-container">
      <header className="shell-header">
        <div className="logo-area">
          <ShieldAlert className="logo-icon" size={24} color="#00E5FF" />
          <span className="logo-text">CROSSFAULT</span>
        </div>
        <div className="controls">
          <label>
            SCENARIO:
            <select value={scenario} onChange={(e) => setScenario(e.target.value)}>
              <option value="CF-001">CF-001</option>
              <option value="CF-002">CF-002</option>
            </select>
          </label>
          <label>
            SEED:
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(parseInt(e.target.value))}
              className="mono"
            />
          </label>
          <button className="run-button" onClick={handleRunInvestigation} disabled={loading}>
            {loading ? 'RUNNING...' : 'RE-RUN INVESTIGATION'}
          </button>
        </div>
      </header>

      <div className="shell-body">
        <aside className="shell-sidebar">
          <nav>
            <ul>
              {navItems.map((item) => (
                <li key={item} className={activePhase === item ? 'active' : ''}>
                  {item}
                </li>
              ))}
            </ul>
          </nav>
        </aside>

        <main className="shell-content" onScroll={(e) => {
          // Simple scroll spy logic would go here
        }}>
          {loading && <LoadingSkeleton />}
          
          {error && <ErrorState error={error} onRetry={handleRunInvestigation} />}
          
          {!loading && !error && data && (
            <div className="phases-container">
              {/* Edge Case Overrides */}
              {data.verified_evidence.analysis_status === 'INVALID_EVIDENCE' ? (
                <div className="glass-panel critical-error-panel">
                  <AlertTriangle color="#FF3366" size={48} />
                  <h2>INVESTIGATION HALTED</h2>
                  <p>The evidence failed validation and no causal conclusion was accepted.</p>
                </div>
              ) : data.verified_evidence.analysis_status === 'BASELINE_NOT_FAILED' ? (
                <div className="glass-panel success-panel">
                  <ShieldAlert color="#00E676" size={48} />
                  <h2>BASELINE DEPLOYMENT SUCCEEDED</h2>
                  <p>No causal investigation was required.</p>
                </div>
              ) : (
                <>
                  <section id="phase-01">
                    <Incident evidence={data.verified_evidence} />
                  </section>
                  <section id="phase-02">
                    <Reconstruction evidence={data.verified_evidence} />
                  </section>
                  <section id="phase-03">
                    <CounterfactualLab evidence={data.verified_evidence} />
                  </section>
                  <section id="phase-04">
                    <PathTrace evidence={data.verified_evidence} />
                  </section>
                  <section id="phase-05">
                    <EvidenceLock evidence={data.verified_evidence} />
                  </section>
                  <section id="phase-06">
                    <AIInvestigator interpretation={data.ai_interpretation} />
                  </section>
                  <section id="phase-07">
                    <ResponseChecklist recommendations={data.ai_recommendations} />
                  </section>
                </>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
