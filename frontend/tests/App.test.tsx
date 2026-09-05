import React from 'react';
import { render, screen } from '@testing-library/react';
import Incident from '../src/features/Incident/Incident';
import EvidenceLock from '../src/features/EvidenceLock/EvidenceLock';
import CounterfactualLab from '../src/features/CounterfactualLab/CounterfactualLab';
import PathTrace from '../src/features/PathTrace/PathTrace';
import { ErrorState } from '../src/components/LoadingError';

const mockEvidence = {
  scenario_id: 'CF-001',
  seed: 48291,
  analysis_status: 'VALID' as any,
  causal_verdict: 'NECESSARY_FOR_OBSERVED_FAILURE' as any,
  baseline_outcome: 'FAILED' as any,
  per_candidate_evidence: [
    {
      candidate_id: 'NET-004',
      candidate_type: 'LIS_PATH_INTERRUPTION' as any,
      candidate_name: 'LIS Gateway Port Block',
      candidate_enabled_in_baseline: true,
      candidate_enabled_in_counterfactual: false,
      baseline_status: 'FAILED' as any,
      counterfactual_status: 'SUCCESS' as any,
      outcome_changed: true,
      affected_path: ['Clinic', 'LIS Gateway'],
      candidate_conclusion: 'NECESSARY_FOR_OBSERVED_FAILURE' as any
    }
  ],
  necessary_candidate: 'NET-004',
  dependency_path: ['Clinic', 'LIS Gateway', 'Results DB'],
  divergence_event_id: 'EV-005',
  limitation_flags: []
};

describe('CrossFault Investigation Workspace', () => {
  test('renders Incident component correctly', () => {
    render(<Incident evidence={mockEvidence} />);
    expect(screen.getAllByText('CF-001').length).toBeGreaterThan(0);
    expect(screen.getByText('FAILED')).toBeInTheDocument();
  });

  test('renders Evidence Lock component correctly', () => {
    render(<EvidenceLock evidence={mockEvidence} />);
    expect(screen.getByText(/VERIFIED EVIDENCE FROM BOUNDED REPLAY EXPERIMENT/i)).toBeInTheDocument();
    expect(screen.getByText('NET-004')).toBeInTheDocument();
  });

  test('renders Counterfactual Lab component correctly', () => {
    render(<CounterfactualLab evidence={mockEvidence} />);
    expect(screen.getByText('LIS Gateway Port Block')).toBeInTheDocument();
  });

  test('AMBIGUOUS edge case handles lack of single necessity and rejects joint causality', () => {
    const ambiguousEvidence = {
      ...mockEvidence,
      causal_verdict: 'AMBIGUOUS' as any,
    };
    render(<EvidenceLock evidence={ambiguousEvidence} />);
    expect(screen.getByText(/Multiple candidates changed the observed outcome/i)).toBeInTheDocument();
    expect(screen.getByText(/Individual necessity cannot be established/i)).toBeInTheDocument();
    expect(screen.getByText(/Joint-causality analysis is outside the current experiment boundary/i)).toBeInTheDocument();
  });

  test('Missing dependency path edge case handles gracefully without fake nodes', () => {
    const emptyPathEvidence = {
      ...mockEvidence,
      dependency_path: []
    };
    const { container } = render(<PathTrace evidence={emptyPathEvidence} />);
    expect(screen.getByText(/Dependency path unavailable for this investigation/i)).toBeInTheDocument();
    expect(container.querySelector('.path-node')).not.toBeInTheDocument();
  });

  test('API 500 / 502 error edge case renders clear error state', () => {
    const error500 = { status: 500, message: 'Internal Server Error' };
    const { unmount } = render(<ErrorState error={error500} onRetry={() => {}} />);
    expect(screen.getByText(/API ERROR 500/i)).toBeInTheDocument();
    expect(screen.getByText(/Internal Server Error/i)).toBeInTheDocument();
    
    unmount();
    
    const error502 = { status: 502, message: 'Bad Gateway' };
    render(<ErrorState error={error502} onRetry={() => {}} />);
    expect(screen.getByText(/API ERROR 502/i)).toBeInTheDocument();
    expect(screen.getByText(/Bad Gateway/i)).toBeInTheDocument();
  });
});
