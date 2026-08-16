# Requirements Intel

Synthesized from: `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md`
Classification: `codesprint-md.json` — type PRD, confidence high, locked: false
PRECEDENCE of this source: PRD (default ordering ADR > SPEC > PRD > DOC)

Text below is copied verbatim from the source document (per project-owner instruction: copy-paste, do not regurgitate). Lightweight section headers and REQ-IDs are added around verbatim blocks for structure. Where an acceptance criterion is not stated verbatim in the source, it is marked `[derived]`.

---

## A. Competition Requirements (Core Objective & Deliverables)

### REQ-agentic-solution — Engineer an Agentic AI System
- Title: PSA Code Sprint: Agentic AI in Action — core objective
- Source: `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (§1. The Core Objective & Theme)
- Scope: Competition-level — PSA Singapore operational / supply chain ecosystem
- Description (verbatim):

> The competition, **PSA Code Sprint: Agentic AI in Action**, requires teams to identify a real problem within PSA Singapore's operational or supply chain ecosystem and engineer an **Agentic AI system** capable of reasoning, making decisions, and coordinating actions toward a defined objective. [scope: PSA → PSA Singapore]

- Acceptance criteria (verbatim, organizer technical expectations):

> * **Inputs to handle:** State changes, operational alerts, event logs, process metrics, sensor anomalies, or cross-stakeholder requests.

### REQ-input-handling — Handle Operational Input Types
- Source: `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (§1. The Core Objective & Theme)
- Scope: Agent input layer
- Description (verbatim):

> **Inputs to handle:** State changes, operational alerts, event logs, process metrics, sensor anomalies, or cross-stakeholder requests.

- Acceptance criteria (verbatim): "State changes, operational alerts, event logs, process metrics, sensor anomalies, or cross-stakeholder requests" must all be handled by the agent.

### REQ-deliverable-deck — 10-Slide Presentation Deck
- Source: `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (§2. Key Deliverables & Format)
- Scope: Submission deliverable
- Description (verbatim):

> * **10-Slide Presentation Deck:** Problem articulation, baseline vs. agentic delta, architecture, decision logic, safety/security guardrails, and quantified business impact.

- Acceptance criteria [derived]: Deck must contain problem articulation, baseline vs. agentic delta, architecture, decision logic, safety/security guardrails, and quantified business impact.

### REQ-deliverable-video — 10-Minute Demonstration Video
- Source: `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (§2. Key Deliverables & Format)
- Scope: Submission deliverable
- Description (verbatim):

> * **10-Minute Demonstration Video:** Walkthrough of the running agent handling normal and edge-case inputs, showcasing the execution trace and UI/operator integration.

- Acceptance criteria (verbatim): "Walkthrough of the running agent handling normal and edge-case inputs, showcasing the execution trace and UI/operator integration."

### REQ-deadline-submission — Submission Deadline 4 September 2026
- Source: `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (§2. Key Deliverables & Format)
- Scope: Schedule / hard gate
- Description (verbatim):

> * **Submission Deadline:** 4 September 2026.

- Acceptance criteria [derived]: All submission assets complete by 2026-09-04.

---

## B. The Six Agentic Capabilities (solution must demonstrate all six)

Source: `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (§1. Definition of the Agentic Solution) — the source frames these six as mandatory:

> For this competition, an **Agentic AI Solution** shouldn't be a simple chatbot or a linear rule engine but rather an intelligent operational system capable of autonomous reasoning, dynamic tool usage, and safe human interaction.
>
> Final solution must demonstrate six core technical capabilities:

### REQ-cap-event-ingestion — Event Ingestion & Perception
- Source: CodeSprint.md (§1. Definition of the Agentic Solution)
- Scope: Agent capability 1
- Description (verbatim):

> * **Event Ingestion & Perception:** Ingests operational inputs such as real-time event logs, sensor alerts, state changes, status updates, or operator requests.

- Acceptance criteria [derived]: Agent ingests real-time event logs, sensor alerts, state changes, status updates, or operator requests.

### REQ-cap-reasoning-planning — Reasoning & Dynamic Planning
- Source: CodeSprint.md (§1. Definition of the Agentic Solution)
- Scope: Agent capability 2
- Description (verbatim):

> * **Reasoning & Dynamic Planning:** Analyzes the situation to identify root causes, evaluates trade-offs, and formulates a multi-step plan of action without hardcoded scripts.

- Acceptance criteria [derived]: Agent identifies root causes, evaluates trade-offs, and formulates multi-step plans without hardcoded scripts.

### REQ-cap-tool-orchestration — Tool & System Orchestration
- Source: CodeSprint.md (§1. Definition of the Agentic Solution)
- Scope: Agent capability 3
- Description (verbatim):

> * **Tool & System Orchestration:** Interacts with external systems by calling mock APIs, querying databases, and triggering operational workflows (e.g., dispatching hauliers, rescheduling berths, checking reefer status).

- Acceptance criteria [derived]: Agent calls mock APIs, queries databases, and triggers operational workflows (haulier dispatch, berth rescheduling, reefer status checks).

### REQ-cap-execution-trace — State Tracking & Observable Execution Trace
- Source: CodeSprint.md (§1. Definition of the Agentic Solution)
- Scope: Agent capability 4
- Description (verbatim):

> * **State Tracking & Observable Execution Trace:** Maintains an internal state across multiple steps and outputs a clear, real-time log of its reasoning chain, tool inputs, tool outputs, human approvals, and errors.

- Acceptance criteria (verbatim): "Maintains an internal state across multiple steps and outputs a clear, real-time log of its reasoning chain, tool inputs, tool outputs, human approvals, and errors."

### REQ-cap-hitl-controls — Human-in-the-Loop (HITL) Controls
- Source: CodeSprint.md (§1. Definition of the Agentic Solution)
- Scope: Agent capability 5
- Description (verbatim):

> * **Human-in-the-Loop (HITL) Controls:** Automatically assesses operational risk and pauses execution to request human verification or override when confidence is low or when high-risk actions are involved.

- Acceptance criteria (verbatim): "Automatically assesses operational risk and pauses execution to request human verification or override when confidence is low or when high-risk actions are involved."

### REQ-cap-error-recovery — Uncertainty & Error Recovery
- Source: CodeSprint.md (§1. Definition of the Agentic Solution)
- Scope: Agent capability 6
- Description (verbatim):

> * **Uncertainty & Error Recovery:** Handles missing data, ambiguous information, or failed API calls gracefully by trying alternative actions or escalating safely rather than crashing.

- Acceptance criteria (verbatim): "Handles missing data, ambiguous information, or failed API calls gracefully by trying alternative actions or escalating safely rather than crashing."

### Verbatim appendix — Organizer "Core Agent capabilities" list (Section 1)
The organizers' own capability list (from §1. The Core Objective & Theme) is preserved verbatim as supporting context for the six capabilities above:

> * **Core Agent capabilities:**
>   1. Parse unstructured/structured inputs to deduce intent/root cause.
>   2. Formulate dynamic plans or recovery strategies.
>   3. Orchestrate tools, internal APIs, and downstream systems.
>   4. Handle uncertainty, ambiguous information, latency, and tool failures gracefully.
>   5. Incorporate human review/escalation protocols with calibrated confidence thresholds.
>   6. **Produce an observable Execution Trace** (displaying thoughts, tool calls, arguments, outputs, approvals, fallback routines, and error handling).

---

## C. Evaluation Criteria (rubric requirements — also enforced as gates in constraints.md)

Source: `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (§2. Key Deliverables & Format). Verbatim:

> * **Evaluation Criteria:**
>   1. *Agentic AI Design & Technical Execution* (ReAct/Plan-and-Solve mechanics, tool orchestration, state management, trace logging).
>   2. *Innovation & Originality* (Tackling non-trivial port/logistics challenges beyond simple chatbots).
>   3. *Scalability & Responsible AI* (Risk-calibrated human-in-the-loop, latency, security, safety guardrails).
>   4. *Presentation & Clarity* (System architecture rigor, clear ROI/throughput impact math).

### REQ-eval-design-execution — Agentic AI Design & Technical Execution
- Source: CodeSprint.md (§2. Key Deliverables & Format)
- Scope: Evaluation criterion 1
- Description (verbatim): "*Agentic AI Design & Technical Execution* (ReAct/Plan-and-Solve mechanics, tool orchestration, state management, trace logging)."
- Acceptance criteria [derived]: Solution exhibits ReAct/Plan-and-Solve mechanics, tool orchestration, state management, and trace logging.

### REQ-eval-innovation-originality — Innovation & Originality
- Source: CodeSprint.md (§2. Key Deliverables & Format)
- Scope: Evaluation criterion 2
- Description (verbatim): "*Innovation & Originality* (Tackling non-trivial port/logistics challenges beyond simple chatbots)."
- Acceptance criteria [derived]: The chosen problem is a non-trivial port/logistics challenge, not a simple chatbot.

### REQ-eval-scalability-responsible — Scalability & Responsible AI
- Source: CodeSprint.md (§2. Key Deliverables & Format)
- Scope: Evaluation criterion 3
- Description (verbatim): "*Scalability & Responsible AI* (Risk-calibrated human-in-the-loop, latency, security, safety guardrails)."
- Acceptance criteria [derived]: Risk-calibrated HITL, acceptable latency, security, and safety guardrails demonstrated.

### REQ-eval-presentation-clarity — Presentation & Clarity
- Source: CodeSprint.md (§2. Key Deliverables & Format)
- Scope: Evaluation criterion 4
- Description (verbatim): "*Presentation & Clarity* (System architecture rigor, clear ROI/throughput impact math)."
- Acceptance criteria [derived]: Rigorous system architecture and clear ROI/throughput impact math presented.

---

## D. Phase 1–3 Workflow Requirements (the .planning/ roadmap scope)

Phases map verbatim from `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (§2. Overarching Workflow):

> Phase 1: Broad PSA Singapore Operations & Systems Mapping [scope: PSA → PSA Singapore]
>   ↓
> Phase 2: Disruption Mining (Identify Current Frictions within PSA Singapore areas) & Problem Bank Creation [scope: PSA → PSA Singapore]
>   ↓
> Phase 3: Problem Evaluation, Litmus Testing (Where to apply Agentic Solution) & Final Selection

NOTE: Phases 4–6 exist in the source workflow but are OUT OF SCOPE for this directory's .planning/ roadmap (see constraints.md C-02; captured at projection stage only).

---

### Phase 1 — Broad PSA Singapore Operations & Systems Mapping

### REQ-p1-mapping — Phase 1: Broad PSA Singapore Operations & Systems Mapping
- Source: CodeSprint.md (§3. Detailed Phase-by-Phase Workflows, Phase 1)
- Scope: Phase 1 (goal + whole-phase mandate)
- Description (verbatim):

> *Goal: Build a clear technical understanding of PSA Singapore's operations and existing digital infrastructure across all core sectors.*

- Acceptance criteria [derived]: Technical understanding of PSA Singapore's operations and existing digital infrastructure across all core sectors is documented (see REQ-p1-sectors, REQ-p1-baseline-systems, REQ-p1-critical-flows).

### REQ-p1-sectors — 1.1 Research the 4 Operational Sectors
- Source: CodeSprint.md (§3, Phase 1, 1.1)
- Scope: Phase 1 step 1.1
- Description (verbatim):

> * **1.1. Research the 4 Operational Sectors:**

Sectors to research (verbatim list of the four sector headings):

> * **Berth & Marine Operations:**
> * **Container Yard & Internal Transport:**
> * **Gate & External Haulage Operations:**
> * **Multimodal Logistics & Supply Chain Adjacencies:**

- Acceptance criteria [derived]: Each of the four sectors is researched (full per-sector topic lists preserved verbatim in context.md, topic "The 4 Operational Sectors").

### REQ-p1-baseline-systems — 1.2 Map Existing PSA Singapore Digital Systems (The Baseline)
- Source: CodeSprint.md (§3, Phase 1, 1.2)
- Scope: Phase 1 step 1.2
- Description (verbatim):

> * **1.2. Map Existing PSA Singapore Digital Systems (The Baseline):** [scope: PSA → PSA Singapore]

Systems to map (verbatim list of the seven system headings):

> * **CITOS® (Computer Integrated Terminal Operations System):**
> * **PORTNET®:**
> * **OptETruck:**
> * **SmartBooking™ & iBOX™ (Intelligent Box Operation eXchange):**
> * **OptEModal:**
> * **CALISTA® & CALISTA P!NG™ (via CrimsonLogic / GeTS):**
> * **PSA BDP Enterprise Solutions:**

- Acceptance criteria [derived]: All seven baseline systems mapped (full verbatim system descriptions preserved in context.md, topic "The 7 Baseline Digital Systems").

### REQ-p1-critical-flows — 1.3 Map the Three Critical Flows for Each Sector
- Source: CodeSprint.md (§3, Phase 1, 1.3)
- Scope: Phase 1 step 1.3
- Description (verbatim):

> * **1.3. Map the Three Critical Flows for Each Sector:**
>   * **Physical Flow:** How containers, ships, cranes, and trucks physically move.
>   * **Information Flow:** What EDI messages, API calls, sensor alerts, and emails are sent at each step.
>   * **Decision Flow:** Who or what system decides what happens when schedules are met versus when delays occur.

- Acceptance criteria [derived]: Physical, Information, and Decision flows mapped for each of the four sectors.

---

### Phase 2 — Disruption Mining & Problem Bank Creation

### REQ-p2-disruption-mining — Phase 2: Disruption Mining & Problem Bank Creation
- Source: CodeSprint.md (§3, Phase 2)
- Scope: Phase 2 (goal + whole-phase mandate)
- Description (verbatim):

> *Goal: Identify high-friction operational failure points where current software and manual processes struggle.*

- Acceptance criteria [derived]: High-friction operational failure points identified; see sub-steps REQ-p2-change-scenarios, REQ-p2-failure-modes, REQ-p2-problem-bank.

### REQ-p2-change-scenarios — 2.1 Target "Something Changed" Scenarios
- Source: CodeSprint.md (§3, Phase 2, 2.1)
- Scope: Phase 2 step 2.1
- Description (verbatim):

> * **2.1. Target "Something Changed" Scenarios:**
>   * Focus on dynamic disruptions where static rules fail, such as:
>     * Asynchronous vessel arrival delays causing cascading berth and yard conflicts.
>     * Dangerous Goods (DG) or customs clearance holds detected late in the loading sequence.
>     * Equipment breakdowns (e.g., AGV path deadlocks or reefer power failures).
>     * Multi-party coordination failures (e.g., haulier misses gate slot, missing export documentation, missing feeder connections).

- Acceptance criteria [derived]: Dynamic "something changed" disruptions where static rules fail are targeted (examples above).

### REQ-p2-failure-modes — 2.2 Document Operational Failure Modes
- Source: CodeSprint.md (§3, Phase 2, 2.2)
- Scope: Phase 2 step 2.2
- Description (verbatim):

> * **2.2. Document Operational Failure Modes:**
>   * For each disruption found, identify:
>     * *Trigger Event:* What alert or state change starts the issue?
>     * *Current Workaround:* What manual, slow, or fragmented process (phone calls, emails, spreadsheets) is currently used to resolve it?
>     * *Business Consequence:* Demurrage fees, vessel idle time, extra yard crane moves (re-handles), missed delivery SLAs, or carbon waste.

- Acceptance criteria [derived]: Each disruption documented with Trigger Event, Current Workaround, and Business Consequence.

### REQ-p2-problem-bank — 2.3 Output a 10–15 Problem Bank
- Source: CodeSprint.md (§3, Phase 2, 2.3)
- Scope: Phase 2 step 2.3 (Phase 2 exit deliverable)
- Description (verbatim):

> * **2.3. Output a 10–15 Problem Bank:**
>   * Consolidate findings into a clean list of candidate problems spanning all 4 sectors.

- Acceptance criteria (verbatim): "A clean list of candidate problems spanning all 4 sectors" — sized 10–15 problems [derived sizing from step title "10–15 Problem Bank"].

---

### Phase 3 — Problem Evaluation, Litmus Testing & Final Selection

### REQ-p3-evaluation — Phase 3: Problem Evaluation, Litmus Testing & Final Selection
- Source: CodeSprint.md (§3, Phase 3)
- Scope: Phase 3 (goal + whole-phase mandate)
- Description (verbatim):

> *Goal: Select the single best problem for an Agentic AI solution and quantify its impact.*

- Acceptance criteria [derived]: A single best problem is selected and its impact quantified; see sub-steps REQ-p3-litmus-test, REQ-p3-autonomy-level, REQ-p3-master-charter.

### REQ-p3-litmus-test — 3.1 Apply the 5-Point Agentic AI Litmus Test to Each Problem
- Source: CodeSprint.md (§3, Phase 3, 3.1)
- Scope: Phase 3 step 3.1
- Description (verbatim):

> * **3.1. Apply the 5-Point Agentic AI Litmus Test to Each Problem:**

| Test Criteria | Requirement for Passing |
| :--- | :--- |
| **1. Non-Deterministic** | Cannot be solved by a simple database query, rule script, or basic linear optimizer. Requires situational reasoning over dynamic context. |
| **2. Multi-Tool Calling** | Needs to interact with at least 3 distinct systems or data sources (e.g., PORTNET, CITOS, Haulier TMS, Weather/AIS). |
| **3. Multi-Step Execution** | Requires a sequence: Ingest → Diagnose → Plan → Execute Tool A → Verify → Execute Tool B. |
| **4. Uncertainty Handling** | Involves incomplete data, conflicting inputs, or operational latency where an agent must make safe judgments. |
| **5. Measurable ROI** | The outcome directly reduces vessel dwell time, container re-handles, haulier wait times, or demurrage costs. |

- Acceptance criteria [derived]: Every candidate problem passes all five litmus-test criteria (each criterion requires the listed condition to hold).

### REQ-p3-autonomy-level — 3.2 Define the Target Autonomy Level
- Source: CodeSprint.md (§3, Phase 3, 3.2)
- Scope: Phase 3 step 3.2
- Description (verbatim):

> * **3.2. Define the Target Autonomy Level:**
>   * Categorize the solution into one of three levels:
>     * *Advisory (Copilot):* High physical risk; agent suggests plans, human manually triggers actions.
>     * *Human-in-the-Loop (HITL) Exception Solver (Recommended):* Medium risk; agent autonomously gathers data, runs recovery simulations, drafts API updates, and waits for a 1-click human confirmation before executing.
>     * *Supervised Autonomous:* Low risk; agent executes actions directly and notifies the human, escalating only when an error occurs.

- Acceptance criteria [derived]: Solution categorized into exactly one of the three autonomy levels; the source's recommended selection is HITL Exception Solver (see decisions.md D-2 — proposed, pending team confirmation).

### REQ-p3-master-charter — 3.3 Lock in ONE Master Problem Charter
- Source: CodeSprint.md (§3, Phase 3, 3.3)
- Scope: Phase 3 step 3.3 (Phase 3 exit deliverable)
- Description (verbatim):

> * **3.3. Lock in ONE Master Problem Charter:**
>   * Select the top-ranking problem.
>   * Define the target user persona (e.g., Terminal Duty Manager, ITT Coordinator, Haulier Dispatcher).
>   * Write the exact business impact equation (e.g., *Estimated Annual Savings = Avoided Vessel Delays × Hourly Port Cost + Avoided Yard Re-handles × Move Cost*).

- Acceptance criteria [derived]: One master problem charter exists with: top-ranking problem selected, target user persona defined, and exact business impact equation written.

---

## Requirement index (27)

- REQ-agentic-solution, REQ-input-handling, REQ-deliverable-deck, REQ-deliverable-video, REQ-deadline-submission
- REQ-cap-event-ingestion, REQ-cap-reasoning-planning, REQ-cap-tool-orchestration, REQ-cap-execution-trace, REQ-cap-hitl-controls, REQ-cap-error-recovery
- REQ-eval-design-execution, REQ-eval-innovation-originality, REQ-eval-scalability-responsible, REQ-eval-presentation-clarity
- REQ-p1-mapping, REQ-p1-sectors, REQ-p1-baseline-systems, REQ-p1-critical-flows
- REQ-p2-disruption-mining, REQ-p2-change-scenarios, REQ-p2-failure-modes, REQ-p2-problem-bank
- REQ-p3-evaluation, REQ-p3-litmus-test, REQ-p3-autonomy-level, REQ-p3-master-charter