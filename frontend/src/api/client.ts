import { VerifiedAIResponse } from './types';

export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

export async function runInvestigation(scenario: string, seed: number = 48291): Promise<VerifiedAIResponse> {
  const params = new URLSearchParams({
    scenario,
    seed: seed.toString(),
  });
  
  const response = await fetch(`/api/investigate?${params}`);
  
  if (!response.ok) {
    let detail = 'An unknown error occurred';
    try {
      const errorData = await response.json();
      detail = errorData.detail || detail;
    } catch (e) {
      // Ignored
    }
    throw new APIError(response.status, detail);
  }
  
  return response.json() as Promise<VerifiedAIResponse>;
}
