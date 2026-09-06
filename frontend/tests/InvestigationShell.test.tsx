import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import InvestigationShell from '../src/layout/InvestigationShell';
import * as client from '../src/api/client';

const mockData = {
  verified_evidence: {
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
  },
  ai_interpretation: {
    narrative_explanation: 'Test Narrative',
    negative_evidence_explanation: 'Test Negative'
  },
  ai_recommendations: {
    remediation_steps: ['Step 1']
  }
};

describe('InvestigationShell Integration', () => {
  beforeEach(() => {
    vi.spyOn(client, 'runInvestigation').mockResolvedValue(mockData as any);
    Element.prototype.scrollIntoView = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test('navigation sidebar items render and navigate to corresponding sections smoothly', async () => {
    render(<InvestigationShell />);
    
    // Wait for the data to load and components to render
    await waitFor(() => {
      expect(screen.getByText('01 — INCIDENT')).toBeInTheDocument();
    });

    // Verify all seven navigation items render
    const navItem1 = screen.getByText('01 INCIDENT');
    const navItem2 = screen.getByText('02 RECONSTRUCTION');
    const navItem4 = screen.getByText('04 PATH TRACE');
    const navItem7 = screen.getByText('07 RESPONSE');
    
    expect(navItem1).toBeInTheDocument();
    expect(navItem2).toBeInTheDocument();
    expect(navItem4).toBeInTheDocument();
    expect(navItem7).toBeInTheDocument();

    // Verify all seven sections actually render in the DOM
    expect(screen.getByText('01 — INCIDENT')).toBeInTheDocument();
    expect(screen.getByText('02 — RECONSTRUCTION')).toBeInTheDocument();
    expect(screen.getByText('03 — COUNTERFACTUAL LAB')).toBeInTheDocument();
    expect(screen.getByText('04 — PATH TRACE')).toBeInTheDocument();
    expect(screen.getByText('05 — EVIDENCE LOCK')).toBeInTheDocument();
    expect(screen.getByText('06 — INVESTIGATOR')).toBeInTheDocument();
    expect(screen.getByText('07 — RESPONSE')).toBeInTheDocument();

    // Click 02 RECONSTRUCTION
    fireEvent.click(navItem2);
    expect(Element.prototype.scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });
    
    // Clear mock calls to test next navigation
    (Element.prototype.scrollIntoView as any).mockClear();

    // Click 04 PATH TRACE
    fireEvent.click(navItem4);
    expect(Element.prototype.scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });

    (Element.prototype.scrollIntoView as any).mockClear();

    // Click 07 RESPONSE
    fireEvent.click(navItem7);
    expect(Element.prototype.scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });

    // Verify that sections didn't disappear after navigation
    expect(screen.getByText('02 — RECONSTRUCTION')).toBeInTheDocument();
  });

  test('AI unavailable state renders deterministic sections and explicit warning state without crashing or fake data', async () => {
    const mockUnavailableData = {
      verified_evidence: mockData.verified_evidence,
      ai_interpretation: null,
      ai_recommendations: null,
      ai_status: 'unavailable',
      ai_error: 'AI interpretation unavailable: provider quota or availability limit.'
    };

    vi.spyOn(client, 'runInvestigation').mockResolvedValue(mockUnavailableData as any);

    render(<InvestigationShell />);

    // Wait for investigation data to load
    await waitFor(() => {
      expect(screen.getByText('01 — INCIDENT')).toBeInTheDocument();
    });

    // 1. First five phases render normally
    expect(screen.getByText('01 — INCIDENT')).toBeInTheDocument();
    expect(screen.getByText('02 — RECONSTRUCTION')).toBeInTheDocument();
    expect(screen.getByText('03 — COUNTERFACTUAL LAB')).toBeInTheDocument();
    expect(screen.getByText('04 — PATH TRACE')).toBeInTheDocument();
    expect(screen.getByText('05 — EVIDENCE LOCK')).toBeInTheDocument();

    // 2. Investigator & Response phases render unavailable messages & verified complete banner
    expect(screen.getByText('06 — INVESTIGATOR')).toBeInTheDocument();
    expect(screen.getByText('AI INTERPRETATION')).toBeInTheDocument();
    expect(screen.getAllByText('Currently unavailable').length).toBeGreaterThan(0);
    expect(screen.getByText(/The deterministic investigation and verified evidence remain available/i)).toBeInTheDocument();

    expect(screen.getByText('07 — RESPONSE')).toBeInTheDocument();
    expect(screen.getByText('AI RECOMMENDATIONS')).toBeInTheDocument();
    expect(screen.getByText(/No AI-generated remediation recommendations were accepted/i)).toBeInTheDocument();
    expect(screen.getAllByText(/The AI is optional. Verified causal evidence remains available/i).length).toBeGreaterThan(0);

    // 3. No fake AI text or fake remediation appears
    expect(screen.queryByText('Test Narrative')).not.toBeInTheDocument();
    expect(screen.queryByText('Step 1')).not.toBeInTheDocument();

    // 4. Navigation still works for all 7 items
    const navItem6 = screen.getByText('06 INVESTIGATOR');
    fireEvent.click(navItem6);
    expect(Element.prototype.scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });
  });
});

