# CrossFault Implementation Roadmap

This document outlines the complete implementation roadmap for the CrossFault hackathon project, explicitly separating completed, verified components from planned functionality.

---

## PHASE 1 — Deterministic Simulator
**Status: COMPLETE**

Phase 1 establishes the foundational modeling constraints for the deployment network simulator. 

**Implemented Features:**
*   **Synthetic Healthcare Topology**: Models a directed service path from a `Clinic` origin down to a `Results Database`.
*   **Application Input**: A frozen, typed representation of the simulated payload passed through the deployment.
*   **Deterministic Seed**: Isolated, localized pseudo-random number generator (PRNG) handling ensures 100% reproducible execution loops.
*   **Network Candidates**: Explicit domain models defining the potential disruptive events occurring concurrently with the deployment.
*   **Deployment Simulation**: Multi-hop processing loop that evaluates candidates and tests node-to-node network viability.
*   **Structured Event Records**: Emits rigidly formatted event traces logging precise timing, sequence, and candidate evaluation metadata.
*   **Tests**: A comprehensive unit testing suite guarantees baseline simulation rules and immutable seed determinism.

---

## PHASE 2 — Counterfactual Replay Engine
**Status: COMPLETE**

Phase 2 introduces the orchestration logic necessary to execute a controlled boundary experiment using the Phase 1 simulator.

**Implemented Features:**
*   **Baseline Replay**: Captures the exact execution footprint of the `FAILED` deployment with all candidates active.
*   **Exactly one candidate disabled per counterfactual**: Sequentially iterates candidates, toggling `is_enabled=False` for precisely one candidate per replay while keeping all others enabled.
*   **Same scenario/seed**: Guarantees perfect PRNG alignment for every executed replay.
*   **Candidate state isolation**: Original scenarios are deep-copied; state mutation never leaks between counterfactuals.
*   **Deterministic Replay**: Ensures execution remains identically reproducible across multiple investigation calls.
*   **Preserved application input/topology**: Enforces strict topological and input integrity during the replay loop.
*   **Tests**: Unit tests confirm isolation boundaries and correct event generation across independent counterfactual outputs.

---

## PHASE 3 — Causal Analyzer
**Status: COMPLETE**

Phase 3 introduces the mathematical/rule-based processing core to evaluate Phase 2 counterfactual evidence. 

**Implemented Features:**
*   **Consumes replay evidence**: Processes `InvestigationReplayResult` directly.
*   **Does not rerun simulation**: Strictly operates on previously generated structural records.
*   **Typed Causal Conclusions**: Explicitly bounds outcomes to `NECESSARY_FOR_OBSERVED_FAILURE`, `NOT_NECESSARY`, `NO_CAUSAL_CANDIDATE`, and `AMBIGUOUS`.
*   **Typed Analysis Status**: Disambiguates valid executions from `BASELINE_NOT_FAILED` and `INVALID_EVIDENCE` states.
*   **Validation of configuration**: Strictly validates seed, application input, topology, and candidate alignment, returning invalid evidence structures safely rather than crashing.
*   **Deterministic Analysis**: Emits predictable causal verdicts without ML, heuristic variation, or AI generation.

---

## PHASE 3.x — Determinism Testing Hardening
**Status: COMPLETE**

Phase 3.x strengthens the unit testing suite to mathematically verify the fidelity of the deterministic engine models.

**Implemented Features:**
*   **Complete baseline event trace determinism**: Tests assert that independent identically-seeded executions produce identical structured trace arrays matching at every single variable tier (timestamp, string message, sequence ID).
*   **Counterfactual event trace isolation**: Tests assert that unrelated counterfactual branches are completely identical up to the precise moment a designated candidate network boundary is evaluated.
*   **28 tests passing overall**: 100% coverage across expected boundaries and invariants.

---

## PHASE 4 — Verified Evidence Assembly + Dependency Path Extraction
**Status: NOT STARTED**

Phase 4 bridges the structural simulation outputs into a packaged evidence model suitable for deterministic visualization and eventual AI summarization.

**Intended Scope:**
*   **Derive dependency/divergence path**: Map out the exact affected node chain relying upon recorded baseline and necessary-candidate-disabled traces.
*   **No new simulation runs**: Ensure mapping utilizes only pre-existing execution data.
*   **No causal logic changes**: Do not mutate Phase 3 verdicts.
*   **Create a verified evidence model**: Standardize structural outputs for Phase 5.
*   **Preserve provenance**: Tie every extracted dependency step strictly back to recorded events.
*   **Explicitly represent limitations**: Bound the representation so visualizations map appropriately to the single-candidate model constraints.
*   **Constraints**: No LLM, no UI, no FastAPI components in this phase.

**Acceptance Criteria:**
*   Resolved necessary verdict produces a non-empty ordered affected path derived strictly from trace histories.
*   `NO_CAUSAL_CANDIDATE` and `AMBIGUOUS` do not artificially fabricate a path out of arbitrary data.
*   Deterministic path extraction is guaranteed via unit tests.
*   Analyzer, replay, and simulation layers are explicitly NOT rerun during assembly.

---

## PHASE 5 — LLM Investigator + AI Output Validator
**Status: PLANNED**

Phase 5 integrates AI components specifically constrained to *explain* the deterministic evidence rather than *invent* it.

**Intended AI Responsibilities:**
*   Explain how the verified failure propagated.
*   Explain why negative candidates did not matter to the final result.
*   Summarize the verified evidence package into accessible narratives.
*   Generate grounded remediation suggestions aligned with the evidence.
*   **NEVER decide or overwrite the deterministic causal verdict.**
*   Receive strictly formatted verified evidence payloads.
*   **Validator checks AI claims**: A deterministic secondary layer that parses the LLM output, comparing assertions directly back to the verified evidence.
*   **Reject/flag unsupported causal claims**: Protect against AI hallucinations or unwarranted certainty statements outside the defined causality bounds.

> [!WARNING]
> This module is strictly PLANNED. It is explicitly NOT yet implemented in the current production codebase.

---

## PHASE 6 — Second Scenario
**Status: PLANNED**

Add one contrasting scenario with a different valid outcome and network topology, verifying the analysis ruleset generalizes beyond the hardcoded `CF-001` behavior.

---

## PHASE 7 — Thin FastAPI Backend
**Status: PLANNED**

Expose the isolated Python pipeline via a secure, minimal API layer enabling frontend decoupling and standardized REST execution endpoints.

---

## PHASE 8 — Minimal React Dashboard
**Status: PLANNED**

Implement a lightweight, highly constrained client interface.

**Target Visualization Deliverables:**
*   Scenario metadata
*   Baseline result trace
*   Counterfactual execution tracking
*   Deterministic causal verdict
*   Evidence timeline
*   Dependency path map
*   AI Explanation narrative
*   Validator sanity/assurance result

---

## PHASE 9 — Security and Adversarial Testing
**Status: PLANNED**

Rigorous adversarial evaluation of the platform boundaries.

**Include coverage for:**
*   Malformed evidence submissions
*   Prompt injection attempts passing through scenario or candidate text fields
*   Unsupported AI causal assertions deliberately injected to trigger the validator
*   Validator bypass mechanics
*   Invalid candidate identification processing
*   Inconsistent replay data injection
*   Full deterministic regression test battery execution

---

## PHASE 10 — Integration and Demo Hardening
**Status: PLANNED**

Execute exhaustive end-to-end verifications of the stack to ensure smooth demonstration capability and remove integration friction risks between backend and client.

---

## PHASE 11 — Final Audit
**Status: PLANNED**

Execute an independent review of the entire system architecture against the original PRD mandates and hackathon criteria:
*   Problem framing/architecture
*   AI-native workflow/orchestration
*   Implementation quality
*   Testing/AI output verification
*   Debugging/root cause analysis
*   Security/privacy/ownership/communication

---

## PHASE 12 — Final Demo
**Status: PLANNED**

Package a precise, reliable, repeatable system presentation:
1.  Introduce failure scenario context
2.  Review declared candidate network changes
3.  Execute the counterfactual analysis loop
4.  Present the deterministic mathematical causal verdict
5.  Render the extracted dependency path
6.  Display the AI-derived remediation and explanation
7.  Highlight the active validator protection bounds
8.  Articulate the systemic architectural limitations openly
