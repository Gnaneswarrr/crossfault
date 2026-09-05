# CrossFault

**An AI-assisted causal debugging system for reconstructing network-induced deployment failures in distributed healthcare workflows.**

## The Problem

In complex distributed deployments, it's common for a deployment to fail around the same time as several network changes (such as firewall modifications or DNS record updates) occur. Simple timeline correlation tells us *when* a change happened, but it does not prove *which* change actually caused the failure. 

CrossFault eliminates the guesswork by using controlled, deterministic replay to test individual candidate changes.

## Core Idea: Bounded Counterfactual Replay

Instead of guessing causality based on timestamps, CrossFault explicitly tests it:

1. **Baseline**: Run the deployment simulation with all candidate network changes enabled and observe the failure.
2. **Counterfactual**: Disable exactly *one* candidate network change and replay the exact same scenario.
3. **Compare**: If disabling a specific candidate changes the deployment outcome from FAILED to SUCCESS, that candidate was **necessary for reproducing the observed failure under the bounded deterministic replay experiment**.

> [!NOTE]
> CrossFault provides mathematical, bounded experimental conclusions. It does *not* use phrases like "mathematically proved root cause" or claim absolute real-world causality, as the simulation itself is a bounded model.

## Simulated Healthcare Environment

To demonstrate the causal analyzer, CrossFault uses a synthetic/simulated healthcare workflow inspired by real-world distributed systems (this is NOT a reproduction of proprietary myOnsite architecture). 

**Current Topology:**
`Clinic` → `Lab Order Service` → `Specimen Processing Service` → `LIS Gateway` → `Results Service` → `Results Database`

## Network Candidates

The initial scenario (`CF-001`) declares four candidate network changes that occurred around the time of the deployment failure:
*   `ROUTE_CHANGE`
*   `ACCESS_RULE_CHANGE`
*   `DNS_CHANGE`
*   `LIS_PATH_INTERRUPTION`

## Current Result (Scenario CF-001)

When we run CrossFault on `CF-001`, the system produces the following verified behavior:

**Counterfactual Replays:**
*   Baseline → FAILED
*   Disable Route Change → FAILED
*   Disable Access Rule Change → FAILED
*   Disable DNS Change → FAILED
*   Disable LIS Path Interruption → SUCCESS

**Causal Conclusion:**
*   **Verdict**: `NECESSARY_FOR_OBSERVED_FAILURE`
*   **Candidate**: LIS Path Interruption
*   **Bound**: Necessary for reproducing the observed failure under the bounded deterministic replay experiment.

## Architecture

CrossFault is built in distinct modular phases. The following components define the causal pipeline:

*   **`SimulationEngine`**: Executes deterministic, multi-hop deployment scenarios.
*   **`ReplayEngine`**: Orchestrates counterfactual isolation and replays the scenario.
*   **`CausalAnalyzer`**: Processes replay evidence strictly without invoking the simulators.
*   **Verified Evidence / future Evidence Assembly**: [NOT YET IMPLEMENTED]
*   **Future AI Investigator**: [NOT YET IMPLEMENTED]
*   **Future AI Output Validator**: [NOT YET IMPLEMENTED]

## Testing

CrossFault is rigorously tested. Currently, **28 automated tests** pass with 100% success. 

These tests enforce strict boundaries and cover:
*   **Deterministic simulation**: Ensures RNG handling guarantees perfectly reproducible behavior.
*   **Scenario/Topology validation**: Verifies structure and application inputs.
*   **Replay correctness**: Validates baseline preservation.
*   **Causal analysis rules**: Tests the logical branches of the rule engine.
*   **Invalid evidence handling**: Confirms missing baselines or malformed structs fail safely.
*   **Analyzer independence**: Explicitly mocks and guarantees `SimulationEngine` and `ReplayEngine` are not invoked during analysis.
*   **Replay determinism**: Verifies the RNG trace and event states across equivalent replay steps.
*   **Counterfactual trace isolation**: Compares complete structured event traces rather than only final FAILED/SUCCESS results to prove absolute timeline identicality prior to candidate evaluation.

## Current Limitations

CrossFault operates strictly within its bounded model constraints:
*   **Single-intervention counterfactuals only**: We test one candidate at a time.
*   **No joint/multi-candidate causal analysis**: Combinatorial failures are not currently evaluated.
*   **No claim of absolute real-world causality**: The output is strictly bounded to the determinism of the simulated models.
*   **Healthcare environment is simulated**: It is not connected to live hospital infrastructure.
*   **Dependency/path extraction is not yet implemented**: Path visualization from trace logs is planned for Phase 4.
*   **LLM is not yet implemented**: Narrative generation is planned for Phase 5.
*   **AI validator is not yet implemented**: Verification of AI output is planned for Phase 5.
*   **API/UI are not yet implemented**: FastAPI and React are planned for future phases.

## How to Run

Clone the repository and execute the following from the root directory (`D:\crossfault`):

**Run the automated test suite:**
```bash
python -m unittest discover -s tests -v
```

**Run the CrossFault Causal Analyzer CLI:**
```bash
python -m crossfault
```

## Project Status

**Completed through Phase 3.x.** 
Phase 4 (Verified Evidence Assembly + Dependency Path Extraction) is the next implementation milestone.
