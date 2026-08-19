# Phase 3: Problem Evaluation, Litmus Testing & Master Charter Selection — PLAN

**Status:** Ready to execute  
**Depends on:** Phase 2 Deliverables (`problems/02-03-problem-bank.md`, `problems/02-02-failure-modes.md`)  
**Requirements:** P3-01 (Litmus & Cluster Scoring), P3-02 (Autonomy & HITL Guardrails), P3-03 (Master Problem Charter & Platform Blueprint)

---

## 0. Context Ingestion & Upstream Rules (MANDATORY)

Before executing any task below, the agent **MUST**:
1. **Ingest Phase 2 Problem Bank & Clusters:** Read and parse all 16 candidate problems and the 6 Root-Cause Clusters in `problems/02-03-problem-bank.md`.
2. **No Hallucinated Problems:** Evaluate strictly from the established Problem Bank. Do not invent new standalone problems.
3. **Dual-Layer Evaluation:** Evaluate both **individual problem viability** (for prototype demo depth) and **cluster leverage** (for architectural scalability).

---

## Tasks

### 03-01: Apply 5-Point Litmus Test & Cluster-Weighted Scoring Matrix

Evaluate all candidate problems against the Agentic Litmus Filter, score the root-cause clusters, and identify the **Winning Cluster** along with its **Top Flagship Anchor Candidate**.

**Deliverable:** `problems/03-01-litmus-test-scores.md`

#### Stage 1: Individual Problem 5-Point Litmus Filter (Binary PASS / FAIL)
Score every candidate (PB-01 to PB-16) across the 5 mandatory criteria:

| # | Criterion | Pass Condition | Fail Condition |
| :--- | :--- | :--- | :--- |
| **L1** | **Non-Deterministic Reasoning** | Requires situational trade-off analysis, fuzzy logic, or reconciling conflicting information across unstructured/semi-structured data. | Can be solved with an SQL query, static rule engine (`if/else`), or a pure linear programming optimizer alone. |
| **L2** | **Multi-Tool Orchestration** | Requires dynamic interactions with $\ge 3$ distinct systems/APIs (e.g., PORTNET, CITOS, Haulier TMS, AIS feeds, Weather). | Interacts with only 1 or 2 isolated databases without cross-system orchestration. |
| **L3** | **Multi-Step Dynamic Plan** | Execution requires a multi-step loop: Ingest $\rightarrow$ Diagnose $\rightarrow$ Formulate Recovery $\rightarrow$ Call Tool A $\rightarrow$ Evaluate Result $\rightarrow$ Call Tool B. | Single-turn prompt-response or single API call execution. |
| **L4** | **Uncertainty & Latency** | Operates with missing parameters, noisy telemetry, delayed data, or external stakeholder unresponsiveness. | All inputs are 100% complete, synchronous, and deterministic at runtime. |
| **L5** | **Quantifiable ROI & Impact** | Direct, measurable reduction in vessel dwell time, quay crane idling, yard re-handles, haulier wait time, or demurrage fees. | Vague, non-measurable benefits (e.g., "improves communication"). |


*Disqualification Rule:* Any problem with a single **FAIL** is eliminated from standalone consideration.

#### Stage 2: Root-Cause Cluster Evaluation Matrix (Scored 1–5)
Score each of the 6 Root-Cause Clusters across 4 dimensions:
1. **Agentic AI Sweet Spot (30%):** How strongly the cluster's root cause requires LLM reasoning, multi-party coordination, and semantic reconciliation vs. simple math solvers.
2. **Cluster Multiplier / Addressable Coverage (25%):** Number of candidate problems resolved and total aggregate market impact across PSA Singapore.
3. **Demo Execution & Trace Drama (25%):** How compelling, visible, and dynamic the execution trace (thoughts, tool calls, human gates) will appear in a 10-minute video.
4. **Feasibility & API Mockability (20%):** Practicality of building high-fidelity mock environments and data streams within hackathon timelines.

#### Stage 3: Solution Capability Check, Selection of Winning Cluster & Flagship Anchor
**Mandatory 6-Point Solution Capability Check (For well-ranked passed problems):**
- Ingests a distinct event trigger (Alert, Webhook, Sensor, or EDI state change).
- Formulates a dynamic multi-step plan (Not a fixed if/else tree).
- Calls >= 3 distinct mock tools/APIs.
- Generates an observable step-by-step Execution Trace.
- Contains a clear Human-in-the-Loop (HITL) approval gate for high-risk mutations.
- Demonstrates recovery from at least one injected tool failure or missing parameter.

**Final choice for competition use**
* Identify the #1 Ranked Cluster.
* Select the single strongest problem in that cluster to serve as the **Flagship Anchor Scenario** for the prototype build.

**Acceptance Criteria for 03-01:**
- [ ] All 16 candidate problems scored in Stage 1.
- [ ] All 6 Root-Cause Clusters scored in Stage 2 with explicit justifications.
- [ ] Exactly ONE Winning Cluster and ONE Flagship Anchor Problem selected.

---

### 03-02: Calibrate Autonomy Levels & Human-in-the-Loop (HITL) Guardrails

Perform an operational risk assessment on the Flagship Anchor problem and its parent cluster to establish defensible autonomy boundaries and safety trigger policies.

**Deliverable:** `problems/03-02-autonomy-level.md`

#### Step 1: Operational Risk & Hazard Profiling
Evaluate the Flagship Problem across 4 risk vectors (Rated: Low / Medium / High / Critical):
1. **Physical Safety & Terminal Equipment:** Risk of physical collision, crane damage, or dangerous goods handling violation.
2. **Financial & Demurrage Liability:** Exposure to immediate charter party penalties, missed feeder connections, or customs fines.
3. **Operational Cascade Risk:** Probability that a wrong action triggers secondary gridlock across adjacent yard blocks or berths.
4. **Stakeholder & Regulatory Exposure:** Legal/compliance implications with Singapore Customs, MPA, or shipping lines.

#### Step 2: Autonomy Level Selection & Justification
Select and defend the operational autonomy tier:
* **Tier 1: Advisory Copilot (High Risk):** Agent synthesizes data and presents ranked recovery options; human operator manually executes all actions.
* **Tier 2: Human-in-the-Loop (HITL) Exception Solver (Medium Risk - *Recommended*):** Agent autonomously diagnoses the issue, queries tools, runs simulations, and drafts API payloads, but halts at a designated **Approval Gate** for a 1-click human verification before committing state changes.
* **Tier 3: Supervised Autonomous (Low Risk):** Agent executes actions autonomously and logs results; only triggers human intervention when confidence is low or an API error occurs.

#### Step 3: Define HITL Trigger Policies & Safety Guardrails
* **Automated Action Space:** Which read-only or low-risk tool calls execute without human approval (e.g., `query_vessel_eta()`, `simulate_rehandle_cost()`, `check_customs_clearance()`).
* **Human Approval Gates:** Which state-mutating actions require mandatory human sign-off (e.g., `commit_berth_reallocation()`, `issue_dg_override()`, `charge_demurrage_waiver()`).
* **Escalation Trigger Thresholds:** Specific conditions (e.g., model confidence $< 0.85$, data latency $> 30\text{ min}$, or financial recovery cost $> \$10,000$) that force escalation to the Terminal Duty Manager.

**Acceptance Criteria for 03-02:**
- [ ] Risk profiles documented across all 4 risk vectors.
- [ ] Explicit justification countering the "Autonomy Trap" (proving why higher autonomy is not blindly chosen).
- [ ] Concrete HITL policies (automated actions vs. mandatory human gates) established for the flagship build.

---

### 03-03: Lock the Master Problem Charter & Platform Generalization Blueprint

Formalize the winning flagship problem and its cluster scalability blueprint into a single Master Charter document for Phase 4 engineering.

**Deliverable:** `problems/03-03-master-charter.md`

**Required Charter Schema:**

# Master Problem Charter: [Flagship Problem Title]

## 1. Executive Summary & Problem Definition
- **Sector:** [Berth & Marine | Container Yard | Gate & Haulage | Multimodal]
- **Target User Persona:** [Specific role, e.g., Terminal Duty Manager, ITT Operations Controller]
- **Parent Root-Cause Cluster:** [e.g., Cluster 2: Manual Multi-Party Coordination Engine]
- **Core Operational Friction:** [2–3 sentences defining the exact disruption and why existing systems fail]
- **Selected Autonomy Level:** [Advisory | HITL Exception Solver | Supervised Autonomous]

## 2. As-Is vs. To-Be Workflow Comparison
- **As-Is Baseline (Current Manual Process):** Step-by-step description of current human firefighting (emails, phone calls, spreadsheets, time to resolve).
- **To-Be Agentic Workflow:** Step-by-step description of how the Agent ingests the event, reasons, orchestrates tools, hits the HITL gate, and resolves the issue.

## 3. Systems Integration & Mock API Specifications
- **Baseline Systems Interfaced:** [e.g., CITOS Berth Planner, PORTNET EDI, OptETruck TMS, MPA Marinet]
- **Required Mock API Toolset (Minimum 3–5 tools for Phase 4 build):**
  1. `tool_name_1(param1, param2)`: Description, input types, and expected JSON return payload.
  2. `tool_name_2(...)`: ...
  3. `tool_name_3(...)`: ...
  4. `tool_name_4(...)`: ...

## 4. Operational Risk, Safety Guardrails & Fallbacks
- **Mandatory HITL Gate:** [Exact action and UI card that pauses for human confirmation]
- **Data Validation Guardrails:** [Input schema checks, sanity bounds, rate limits]
- **Fallback / Exception Protocol:** [What the agent does if an API times out or returns 500]

## 5. Dual-Layer Quantified Business Impact & ROI Model
- **Anchor Mathematical Impact Formula (The Flagship Problem):**
  $$\text{Anchor Annual Savings} = (\Delta \text{Vessel Dwell Hrs} \times C_{\text{vessel}}) + (\Delta \text{Yard Re-handles} \times C_{\text{move}}) + (\Delta \text{Truck Wait Hrs} \times C_{\text{truck}})$$
- **Cluster Generalization Impact Formula (Total Addressable Scaling):**
  $$\text{Total Cluster Impact} = \text{Anchor Annual Savings} + \sum_{i=1}^{N} \text{Annual Savings}(\text{Sibling Problem}_i)$$
- **Cost Parameters & Assumptions:**
  - Vessel Demurrage / Charter Rate: $\$X/\text{hr}$
  - Yard Crane Move Cost: $\$Y/\text{move}$
  - Haulier Wait / Detention Cost: $\$Z/\text{hr}$
  - Annual Incident Frequencies across PSA Singapore terminals
- **Projected Net ROI:** Detailed breakdown of single-incident savings, annual flagship savings, and total addressable cluster value.

## 6. Cluster Scalability Blueprint (Platform Generalization)
- **Sibling Problems Addressed by Same Core Architecture:** [List 3–5 sibling problem IDs from the cluster, e.g., PB-04, PB-09, PB-10]
- **Shared Agentic Primitives:** How the same Planner, State Graph, and HITL framework solve sibling problems with minimal tool customization.

## 7. Execution Trace & Demo Storyboard
- **Trigger Event Payload (Simulated Input):** [Sample JSON event initiating the agent]
- **Step-by-Step Expected Trace (Happy Path):** [Thought $\rightarrow$ Action $\rightarrow$ Observation sequence]
- **Injected Failure / Edge Case Test:** [Specific edge-case to be demonstrated in video: missing parameter, API failure, or safety threshold trigger]

**Acceptance Criteria for 03-03:**
- [ ] Single winning Flagship Problem locked with zero ambiguity.
- [ ] Clear Platform Generalization Blueprint linking back to the parent cluster.
- [ ] Mathematical impact model contains both Anchor ROI and Total Cluster Addressable ROI.
- [ ] Defines at least 3–5 mock tool signatures with input/output expectations.
- [ ] Provides the exact demo storyboard and injected failure scenario for Phase 4 & 5 builds.

---

## Deliverables Summary

| Task | Deliverable File | Target Output |
| :--- | :--- | :--- |
| **03-01** | `problems/03-01-litmus-test-scores.md` | Scored Litmus Filter & Cluster Weighted Matrix |
| **03-02** | `problems/03-02-autonomy-level.md` | Operational risk profiling, autonomy tier selection, and HITL gate rules |
| **03-03** | `problems/03-03-master-charter.md` | The locked Master Problem Charter & Platform Blueprint for Phase 4 engineering |

---

## Exit Gate Checklist

Phase 3 is complete when:
- [ ] All 3 deliverables exist in `problems/`.
- [ ] Exactly ONE Flagship Problem and its parent cluster are locked.
- [ ] The Master Problem Charter contains complete API schemas, dual-layer ROI math, and HITL gate definitions.
- [ ] Architecture design (Phase 4) can begin immediately using `problems/03-03-master-charter.md`.
