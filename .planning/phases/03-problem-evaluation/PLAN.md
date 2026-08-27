# Phase 3: Problem Evaluation, Litmus Testing & Master Charter Selection — PLAN (V2 Hardened)

**Status:** ✅ COMPLETE (2026-08-17)
**Depends on:** Phase 2 Deliverables (`problems/02-03-problem-bank.md`, `problems/02-02-failure-modes.md`, `research/`)
**Requirements:** P3-01 (Discriminative Litmus & Cluster Scoring), P3-02 (Autonomy & Stakeholder Governance), P3-03 (Master Charter & API Blueprint)

---

## 0. Context Ingestion & Negative Guardrails (MANDATORY)

Before executing any task below, the agent **MUST adhere to the following rules**:
1. **Ingest Phase 2 Artifacts:** Read and parse all 16 candidate problems and 6 clusters in `problems/02-03-problem-bank.md`.
2. **Enforce Critical Discrimination (Anti-Sycophancy Rule):** A filter that passes 100% of candidates is invalid. You **MUST critically evaluate and FAIL** problems that are:
   - *Pure Operations Research / Linear Solvers:* Problems solvable by deterministic Mixed-Integer Linear Programming without LLM reasoning (e.g., PB-16 Empty Container Imbalance) $\rightarrow$ **FAIL L1**.
   - *Hardware / Network Layer Problems:* Problems requiring microsecond PLC/telecom failover rather than operational agent reasoning (e.g., PB-07 5G Outage) $\rightarrow$ **FAIL L1 / Feasibility**.
   - *Micro-ROI / Low Macro Impact:* Problems with trivial business impact (<$1,000 per incident) compared to mega-terminal scale (e.g., PB-14 Container Reuse) $\rightarrow$ **FAIL L5**.
3. **Strict Domain Vocabulary & Sector Boundaries:**
   - **Berth & Marine (PB-01 to PB-04, PB-13):** Entities are *Mother Vessels, Feeders, Quay Cranes (QC), TEUs, Berths, Tidal Windows*. (DO NOT mention flights, airports, or airfreight).
   - **Multimodal Sea-to-Air (PB-10, PB-11):** Entities are *Airlines, Changi Airport, Airway Bills (AWB), Flight Cut-offs, ULDs*.

---

## Tasks

### 03-01: Apply 5-Point Discriminative Litmus Test & Cluster Matrix

Critically filter all 16 candidates, score the 6 root-cause clusters, and select the **Winning Cluster** and **Flagship Anchor Problem**.

**Deliverable:** `problem-selection/03-01-litmus-test-scores.md`

#### Stage 1: Individual 5-Point Litmus Filter (PASS / FAIL with Rigorous Justification)
Evaluate all 16 problems (PB-01 to PB-16) against the 5 criteria:

| # | Criterion | Pass Requirement | Strict Fail Condition |
|---|---|---|---|
| **L1** | **Non-Deterministic Reasoning** | Involves unstructured communications (emails, EDI remarks), fuzzy trade-offs, or dynamic multi-party negotiation. | Solvable by standard SQL, deterministic `if/else` rules, or pure MILP/math solvers alone. |
| **L2** | **Multi-Tool Calling (≥3 Systems)** | Dynamically queries/mutates $\ge 3$ distinct platforms (e.g., PORTNET, CITOS, AIS feeds, Carrier TMS). | Operates within 1 or 2 isolated databases without cross-system orchestration. |
| **L3** | **Multi-Step Dynamic Loop** | Requires: Ingest $\rightarrow$ Diagnose $\rightarrow$ Simulate $\rightarrow$ Coordinate $\rightarrow$ Verify $\rightarrow$ Execute. | Single-turn prompt-response or single API execution. |
| **L4** | **Uncertainty & Latency** | Operates with noisy telemetry, unconfirmed carrier replies, or delayed manifest data. | All runtime inputs are 100% complete, synchronous, and static. |
| **L5** | **Significant Macro ROI** | Directly saves $\ge \$5,000$ per incident in vessel demurrage, crane idling, re-handles, or SLA penalties. | Minor cost savings (<$1,000/incident) with negligible macro impact on PSA throughput. |

*Output Requirement:* Explicitly document why failing candidates were eliminated to demonstrate objective filtering rigor.

#### Stage 2: Root-Cause Cluster Evaluation Matrix (Scored 1–5)
Score each of the 6 clusters across 4 weighted dimensions:
1. **Agentic AI Sweet Spot (30%):** Degree of unstructured data, semantic ambiguity, and multi-party negotiation vs. simple math solvers.
2. **Cluster Multiplier / Total Addressable Coverage (25%):** Number of candidate problems resolved and annual aggregate value across PSA Singapore.
3. **Demo Drama & Trace Visibility (25%):** How visually clear and impressive the execution trace (thoughts, tool calls, human gates) will be in a 10-minute video.
4. **Feasibility & API Mockability (20%):** Practicality of simulating realistic mock endpoints and event payloads during the hackathon.

#### Stage 3: Flagship Anchor Selection
* Identify the #1 Ranked Cluster.
* Select the single strongest problem in that cluster to serve as the **Flagship Anchor Scenario** for the prototype.
* Verify the flagship passes the **4-Point Capability Check:** (1) Event Trigger Ingestion, (2) Observable Multi-Step Trace, (3) HITL Risk Gate, (4) Injected Failure Recovery.

**Acceptance Criteria for 03-01:**
- [ ] At least 2–4 candidates objectively failed in Stage 1 with clear technical justification.
- [ ] All 6 clusters scored with mathematical weighting in Stage 2.
- [ ] Exactly ONE Winning Cluster and ONE Flagship Anchor Problem selected without sector/domain vocabulary errors.

---

### 03-02: Calibrate Autonomy Levels & Stakeholder Governance

Perform an operational risk and governance assessment on the Flagship Problem to define safe autonomy limits and HITL trigger policies.

**Deliverable:** `problem-selection/03-02-autonomy-level.md`

#### Step 1: Stakeholder Authority & Governance Mapping
Define who owns what decision in the real world:
- **PSA Singapore (Terminal Operator):** Controls berth allocation, quay crane split intensity, yard block routing, and internal AGV/haulier dispatch. *Does NOT own the cargo or the vessel departure command.*
- **Shipping Line (Carrier):** Owns the cargo contracts, stowage plan approvals, and cargo roll authorizations.
- **Feeder Operator:** Owns the feeder vessel schedule, bunker burn rate, and destination port arrival commitments (e.g., tidal windows at Chittagong, Jakarta, Bangkok).

#### Step 2: Operational Risk Profiling (Low / Medium / High / Critical)
Evaluate the Flagship Problem across 4 risk vectors:
1. **Physical & Terminal Risk:** Quay crane overload, bay congestion, hazardous cargo proximity.
2. **Demurrage & Charter Liability:** Vessel idle penalties (~$1,500–$3,500/hr), feeder delay costs.
3. **Downstream Cascade Risk:** Feeder missing downstream tidal window at destination port due to holding in Singapore.
4. **Contractual & Commercial Risk:** Rolling high-value reefer cargo vs. standard dry cargo.

#### Step 3: Autonomy Level & HITL Trigger Policies
- **Selected Autonomy Level:** Defend why **Tier 2: Human-in-the-Loop (HITL) Exception Solver** is the optimal choice over full autonomy (countering the "Autonomy Trap").
- **Automated Actions (Read-Only / Low-Risk Simulations):**
  - e.g., `query_citos_berth_schedule()`, `parse_unstructured_carrier_email()`, `simulate_crane_split_options()`, `check_destination_tidal_window()`.
- **Mandatory Human Approval Gates (State-Mutating / Financial Actions):**
  - e.g., Committing a 45-minute Feeder Hold, Reallocating an extra Quay Crane gang, Authorizing a cargo roll for non-critical containers.
- **Escalation Triggers:** Conditions forcing human review (e.g., Confidence Score $< 0.85$, Reefer temperature breach detected, Destination tidal window margin $< 30\text{ min}$, or Financial cost $> \$10,000$).

**Acceptance Criteria for 03-02:**
- [ ] Clear separation between PSA authority vs. Carrier/Feeder authority.
- [ ] Defensible justification against full autonomy.
- [ ] Concrete table of Automated Tool Calls vs. Mandatory HITL Approval Gates.

---

### 03-03: Lock Master Problem Charter & Platform Technical Blueprint

Formalize the winning Flagship Problem and its Cluster Scalability Blueprint into a comprehensive Master Charter for Phase 4 engineering.

**Deliverable:** `buildplan/03-03-master-charter.md`

#### Required Charter Schema:

# Master Problem Charter: [Flagship Problem Title]

## 1. Executive Summary & Operational Context
- **Sector:** [Berth & Marine | Container Yard | Gate & Haulage | Multimodal]
- **Target User Persona:** [e.g., PSA Transhipment Duty Officer / Terminal Controller]
- **Parent Cluster:** [e.g., Cluster 2: Manual Multi-Party Coordination Engine]
- **Operational Problem Statement:** [2–3 sentences defining the exact disruption, data asymmetry, and why deterministic systems fail]
- **Selected Autonomy Level:** Tier 2 (Human-in-the-Loop Exception Solver)

## 2. As-Is vs. To-Be Workflow Comparison
- **As-Is Baseline (Current Manual Process):** Step-by-step breakdown of how humans handle the issue today (unstructured emails, phone calls, Excel sheets, 2–4 hours resolution latency).
- **To-Be Agentic Workflow:** Step-by-step breakdown of how the Agent ingests the disruption, parses unstructured inputs, calls simulation tools, negotiates constraints, hits the HITL gate, and executes in <3 minutes.

## 3. Mock API Toolset Specification (Phase 4 Build Contract)
Define at least 4 specific mock API tools with exact parameters and return data:
1. `tool_1_name(param1: type, param2: type) -> dict`:
   - *Description:* ...
   - *Sample Output JSON:* `{ ... }`
2. `tool_2_name(...) -> dict`: ...
3. `tool_3_name(...) -> dict`: ...
4. `tool_4_name(...) -> dict`: ...

## 4. Safety Guardrails, Schema Validation & Injected Failure Scenarios
- **Mandatory HITL Gate Card:** Description of the UI review modal presented to the operator.
- **Input Validation Guardrails:** Sanity checks on crane capacity, vessel draft, and container weights.
- **Fallback / Error Protocol:** How the agent behaves when a mock API returns a `500 Server Error` or timeout.

## 5. Dual-Layer Mathematical ROI & Economic Model
- **Grounded Singapore Cost Parameters:**
  - Vessel Demurrage / Charter Rate: $\$2,500/\text{hour}$
  - Feeder Vessel Charter Rate: $\$800/\text{hour}$
  - Quay Crane Gang Hourly Operating Cost: $\$350/\text{hour}$
  - Unproductive Yard Re-handle: $\$35/\text{move}$
  - Reefer Cargo Cold-Chain SLA Breach Penalty: $\$5,000/\text{container}$
  - Dry Container Missed Connection Delay Cost: $\$150/\text{container}$
- **Anchor Problem ROI Equation (PB-04):**
  $$\text{Savings}_{\text{incident}} = \text{Avoided Cargo Penalties} + \text{Avoided Demurrage} - \text{Extra Crane/Hold Costs}$$
- **Annualized Flagship ROI:** Single-incident savings $\times$ Estimated annual frequency at PSA terminals.
- **Cluster Addressable Impact (Platform Generalization):** Total savings when applying this agent architecture to sibling problems in the cluster.

## 6. Platform Generalization (Cluster Scalability)
- **Sibling Problems Addressed:** [List 3–5 sibling candidate IDs from Cluster 2]
- **Shared Agentic Core:** How the same reasoning planner, email/EDI parser, and HITL gate generalize across the entire cluster.

## 7. Execution Trace & Demo Script
- **Trigger Event Payload (Simulated JSON Input):** Inbound delay webhook + manifest discrepancy.
- **Happy Path Step-by-Step Trace:** (Thought $\rightarrow$ Action $\rightarrow$ Observation $\rightarrow$ HITL Sign-off $\rightarrow$ Mutation).
- **Edge Case / Injected Failure Path:** (e.g., Feeder destination tidal window too tight $\rightarrow$ Agent dynamically pivots from "Hold Feeder" to "Prioritize High-Value Reefer Crane Discharge + Roll Dry Cargo").

**Acceptance Criteria for 03-03:**
- [ ] Exact mock tool JSON signatures defined with parameters and outputs.
- [ ] Cost model differentiates between cargo tiers (Reefers vs. Dry).
- [ ] Realistic multi-party coordination model including downstream destination constraints.
- [ ] Demo script includes both Happy Path and Injected Edge-Case Failure.

---

## Deliverables Summary

| Task | Deliverable File | Target Output |
|---|---|---|
| **03-01** | `problem-selection/03-01-litmus-test-scores.md` | Scored Litmus Filter (with realistic fails) & Cluster Matrix |
| **03-02** | `problem-selection/03-02-autonomy-level.md` | Stakeholder authority mapping & HITL trigger policies |
| **03-03** | `buildplan/03-03-master-charter.md` | Locked Master Problem Charter & Mock API build contract for Phase 4 |

---

## Exit Gate Checklist

Phase 3 is complete when:
- [ ] All 3 deliverables exist in `problem-selection/`.
- [ ] No sector vocabulary mix-ups (marine vs. airfreight).
- [ ] Problem filtering is objectively defended with valid rejections.
- [ ] Phase 4 architecture and synthetic environment development can begin immediately.
