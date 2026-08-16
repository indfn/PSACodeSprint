### PSA Code Sprint: Context & Expectations

#### 1. The Core Objective & Theme
The competition, **PSA Code Sprint: Agentic AI in Action**, requires teams to identify a real problem within PSA's operational or supply chain ecosystem and engineer an **Agentic AI system** capable of reasoning, making decisions, and coordinating actions toward a defined objective.

The organizers explicitly highlight key technical expectations:
* **Inputs to handle:** State changes, operational alerts, event logs, process metrics, sensor anomalies, or cross-stakeholder requests.
* **Core Agent capabilities:**
  1. Parse unstructured/structured inputs to deduce intent/root cause.
  2. Formulate dynamic plans or recovery strategies.
  3. Orchestrate tools, internal APIs, and downstream systems.
  4. Handle uncertainty, ambiguous information, latency, and tool failures gracefully.
  5. Incorporate human review/escalation protocols with calibrated confidence thresholds.
  6. **Produce an observable Execution Trace** (displaying thoughts, tool calls, arguments, outputs, approvals, fallback routines, and error handling).
* **The "Autonomy Trap" warning:** *“Higher autonomy is not automatically better. Teams should select an appropriate level based on use case, operational risk, and available controls.”* (Advisory vs. Human-in-the-Loop vs. Autonomous).
#### 2. Key Deliverables & Format
* **Submission Deadline:** 4 September 2026.
* **10-Slide Presentation Deck:** Problem articulation, baseline vs. agentic delta, architecture, decision logic, safety/security guardrails, and quantified business impact.
* **10-Minute Demonstration Video:** Walkthrough of the running agent handling normal and edge-case inputs, showcasing the execution trace and UI/operator integration.
* **Evaluation Criteria:**
  1. *Agentic AI Design & Technical Execution* (ReAct/Plan-and-Solve mechanics, tool orchestration, state management, trace logging).
  2. *Innovation & Originality* (Tackling non-trivial port/logistics challenges beyond simple chatbots).
  3. *Scalability & Responsible AI* (Risk-calibrated human-in-the-loop, latency, security, safety guardrails).
  4. *Presentation & Clarity* (System architecture rigor, clear ROI/throughput impact math).

---
### 1. Definition of the Agentic Solution

For this competition, an **Agentic AI Solution** shouldn't be a simple chatbot or a linear rule engine but rather an intelligent operational system capable of autonomous reasoning, dynamic tool usage, and safe human interaction.

Final solution must demonstrate six core technical capabilities:

* **Event Ingestion & Perception:** Ingests operational inputs such as real-time event logs, sensor alerts, state changes, status updates, or operator requests.
* **Reasoning & Dynamic Planning:** Analyzes the situation to identify root causes, evaluates trade-offs, and formulates a multi-step plan of action without hardcoded scripts.
* **Tool & System Orchestration:** Interacts with external systems by calling mock APIs, querying databases, and triggering operational workflows (e.g., dispatching hauliers, rescheduling berths, checking reefer status).
* **State Tracking & Observable Execution Trace:** Maintains an internal state across multiple steps and outputs a clear, real-time log of its reasoning chain, tool inputs, tool outputs, human approvals, and errors.
* **Human-in-the-Loop (HITL) Controls:** Automatically assesses operational risk and pauses execution to request human verification or override when confidence is low or when high-risk actions are involved.
* **Uncertainty & Error Recovery:** Handles missing data, ambiguous information, or failed API calls gracefully by trying alternative actions or escalating safely rather than crashing.

---

### 2. Overarching Workflow

```
Phase 1: Broad PSA Operations & Systems Mapping
  ↓
Phase 2: Disruption Mining (Identify Current Frictions within PSA areas) & Problem Bank Creation
  ↓
Phase 3: Problem Evaluation, Litmus Testing (Where to apply Agentic Solution) & Final Selection
  ↓
Phase 4: Architecture Design & Synthetic Environment Setup
  ↓
Phase 5: Agent Development, Tool Integration & Failure Testing
  ↓
Phase 6: Submission Asset Creation (Demo Video & Pitch Deck)
```

---

### 3. Detailed Phase-by-Phase Workflows

---

#### Phase 1: Broad PSA Operations & Systems Mapping
*Goal: Build a clear technical understanding of PSA Singapore’s operations and existing digital infrastructure across all core sectors.*

* **1.1. Research the 4 Operational Sectors:**
* **Berth & Marine Operations:**
    * Vessel traffic management and arrival sequencing (MPA coordination, Straits of Malacca approach).
    * Dynamic berth allocation and quay optimization (vessel draft, tidal windows, length overall [LOA], crane split allocation).
    * Marine services synchronization (pilotage, tugboat dispatch, mooring/unmooring, bunkering, and crew/provisioning windows).
    * Quay Crane (QC / dual-trolley) loading and discharge sequencing.
    * Vessel stowage planning, stability/trim constraints, and hazardous cargo onboard segregation.
    * Transhipment connection scheduling (mother vessel to feeder vessel transfer windows and cut-off deadlines).
  * **Container Yard & Internal Transport:**
    * Automated Guided Vehicle (AGV) fleet management, dynamic routing, traffic deadlock resolution, and battery charging optimization.
    * Automated Rail Mounted Gantry (aRMG) / Automated Yard Crane (aYGC) job sequencing and yard block load balancing.
    * Container stacking optimization (transhipment clustering, import/export separation, minimizing unproductive re-handles).
    * Refrigerated container (reefer) telemetry monitoring, power connection management, temperature excursions, and alert triage.
    * Dangerous Goods (DG) yard storage compliance, International Maritime Dangerous Goods (IMDG) class physical segregation rules, and emergency containment protocols.
    * Empty container depot management, maintenance and repair (M&R) routing, and repositioning flows.
  * **Gate & External Haulage Operations:**
    * Automated Gate System (AGS), optical character recognition (OCR), weighbridge validation, and haulier mobile authentication.
    * Haulier booking and time-slot scheduling (OptETruck integration, dynamic slot quota adjustment).
    * External prime mover Truck Round Trip (TRT) time optimization and gate-to-yard buffer queue management.
    * Inter-Terminal Transfers (ITT) balancing (dedicated haulier and barge dispatching between Pasir Panjang Terminal and Tuas Mega Port).
    * Empty container return logistics, drop-and-hook operations, and demurrage/detention tracking.
  * **Multimodal Logistics & Supply Chain Adjacencies:**
    * Sea-to-air multimodal transfers (OptEModal orchestration between PSA terminals and Changi Airfreight Centre).
    * Port-adjacent warehousing and distribution (Supply Chain Hub @ Tuas [PSCH], Keppel Distripark, regional distribution centers).
    * Regulatory and customs compliance clearance (TradeNet, Singapore Customs, MPA, phytosanitary/security inspection holds).
    * End-to-end cargo visibility and milestone event tracking (CALISTA, BoxVoyant data ingestion).
    * Shipper/Forwarder exception handling (manifest discrepancies, late cargo release orders, bill of lading mismatches).

* **1.2. Map Existing PSA Digital Systems (The Baseline):**
  * **CITOS® (Computer Integrated Terminal Operations System):**
	  * PSA’s proprietary, mission-critical Terminal Operating System (TOS). Serves as the operational brain orchestrating real-time berth allocation, automated quay crane (QC) split scheduling, automated rail mounted gantry (aRMG) job sequencing, Automated Guided Vehicle (AGV) fleet dispatching, and vessel stowage stability calculations.
  * **PORTNET®:** 
	  * PSA’s nationwide B2B port community platform. Serves as the real-time digital circulatory system integrating shipping lines, freight forwarders, hauliers, financial institutions, and Singapore government agencies (MPA, Singapore Customs / TradeNet) for electronic delivery orders, container status tracking, customs clearances, and manifest reconciliation.
  * **OptETruck:** 
	  * PSA’s AI-powered cloud transport management system (TMS) for Singapore's container trucking ecosystem. Features automated job scheduling, dynamic route optimization, and cross-company asset pooling to eliminate empty truck runs and optimize terminal gate turn times.
  * **SmartBooking™ & iBOX™ (Intelligent Box Operation eXchange):** 
	  * PSA’s integrated depot-terminal digital exchange co-developed with the Container Depot and Logistics Association (Singapore) (CDAS). Connects off-dock container depots with PSA terminal gates to provide seamless appointment booking, gate queue visibility, and empty container repositioning.
  * **OptEModal:** 
	  * PSA’s sea-air intermodal transhipment management platform (co-developed with Cargo Community Network [CCN]). Integrates maritime terminal operations with Changi Airfreight Centre to execute sub-24-hour sea-to-air transhipments via AI-driven ETA predictions, proactive delay identification, and flight rebooking recommendations.
  * **CALISTA® & CALISTA P!NG™ (via CrimsonLogic / GeTS):** 
	  * PSA’s global supply chain orchestration platform. Bridges physical, regulatory (cross-border customs nodes), and financial supply chain flows, providing near-real-time milestone event telemetry and end-to-end cargo tracking across international trade corridors.
  * **PSA BDP Enterprise Solutions:** 
	  * PSA’s supply chain orchestration and control tower platform (unifying PSA Cargo Solutions and BDP International), handling specialized cargo flows, cold-chain integrity monitoring, and chemical/hazardous logistics tracking.

* **1.3. Map the Three Critical Flows for Each Sector:**
  * **Physical Flow:** How containers, ships, cranes, and trucks physically move.
  * **Information Flow:** What EDI messages, API calls, sensor alerts, and emails are sent at each step.
  * **Decision Flow:** Who or what system decides what happens when schedules are met versus when delays occur.

---

#### Phase 2: Disruption Mining & Problem Bank Creation
*Goal: Identify high-friction operational failure points where current software and manual processes struggle.*

* **2.1. Target "Something Changed" Scenarios:**
  * Focus on dynamic disruptions where static rules fail, such as:
    * Asynchronous vessel arrival delays causing cascading berth and yard conflicts.
    * Dangerous Goods (DG) or customs clearance holds detected late in the loading sequence.
    * Equipment breakdowns (e.g., AGV path deadlocks or reefer power failures).
    * Multi-party coordination failures (e.g., haulier misses gate slot, missing export documentation, missing feeder connections).

* **2.2. Document Operational Failure Modes:**
  * For each disruption found, identify:
    * *Trigger Event:* What alert or state change starts the issue?
    * *Current Workaround:* What manual, slow, or fragmented process (phone calls, emails, spreadsheets) is currently used to resolve it?
    * *Business Consequence:* Demurrage fees, vessel idle time, extra yard crane moves (re-handles), missed delivery SLAs, or carbon waste.

* **2.3. Output a 10–15 Problem Bank:**
  * Consolidate findings into a clean list of candidate problems spanning all 4 sectors.

---

#### Phase 3: Problem Evaluation, Litmus Testing & Final Selection
*Goal: Select the single best problem for an Agentic AI solution and quantify its impact.*

* **3.1. Apply the 5-Point Agentic AI Litmus Test to Each Problem:**

| Test Criteria | Requirement for Passing |
| :--- | :--- |
| **1. Non-Deterministic** | Cannot be solved by a simple database query, rule script, or basic linear optimizer. Requires situational reasoning over dynamic context. |
| **2. Multi-Tool Calling** | Needs to interact with at least 3 distinct systems or data sources (e.g., PORTNET, CITOS, Haulier TMS, Weather/AIS). |
| **3. Multi-Step Execution** | Requires a sequence: Ingest $\rightarrow$ Diagnose $\rightarrow$ Plan $\rightarrow$ Execute Tool A $\rightarrow$ Verify $\rightarrow$ Execute Tool B. |
| **4. Uncertainty Handling** | Involves incomplete data, conflicting inputs, or operational latency where an agent must make safe judgments. |
| **5. Measurable ROI** | The outcome directly reduces vessel dwell time, container re-handles, haulier wait times, or demurrage costs. |

* **3.2. Define the Target Autonomy Level:**
  * Categorize the solution into one of three levels:
    * *Advisory (Copilot):* High physical risk; agent suggests plans, human manually triggers actions.
    * *Human-in-the-Loop (HITL) Exception Solver (Recommended):* Medium risk; agent autonomously gathers data, runs recovery simulations, drafts API updates, and waits for a 1-click human confirmation before executing.
    * *Supervised Autonomous:* Low risk; agent executes actions directly and notifies the human, escalating only when an error occurs.

* **3.3. Lock in ONE Master Problem Charter:**
  * Select the top-ranking problem.
  * Define the target user persona (e.g., Terminal Duty Manager, ITT Coordinator, Haulier Dispatcher).
  * Write the exact business impact equation (e.g., *Estimated Annual Savings = Avoided Vessel Delays $\times$ Hourly Port Cost + Avoided Yard Re-handles $\times$ Move Cost*).

---

#### Phase 4: Architecture Design & Synthetic Environment Setup
*Goal: Design the agent’s reasoning engine and build the simulated port environment it will run on.*

* **4.1. Design the Agent State Machine & Tools:**
  * **Planner & Decision Core:** Define the agent workflow (State $\rightarrow$ Analyze $\rightarrow$ Plan $\rightarrow$ Tool Call $\rightarrow$ Validate $\rightarrow$ HITL Gate $\rightarrow$ Complete).
  * **Tool Schemas:** Define the exact functions the agent can call with structured inputs and outputs (e.g., `get_vessel_eta()`, `reschedule_yard_slot()`, `notify_haulier()`, `verify_imdg_clearance()`).
  * **State Memory:** Keep track of the current disruption context, steps taken so far, and intermediate results.

* **4.2. Build the Synthetic Port API Environment:**
  * Create mock data endpoints simulating the systems the agent needs to call:
    * *Mock PORTNET API:* Container manifests, vessel booking records, customs release statuses.
    * *Mock CITOS Yard/Berth DB:* Current crane queues, berth allocation windows, yard block capacities.
    * *Mock External Feeds:* Haulier fleet status, live AIS vessel coordinates, weather conditions.

* **4.3. Build the Event Generator & Trace Logging Schema:**
  * Build an event trigger engine to push simulated real-time disruption events into the agent.
  * Standardize the JSON structure for the **Execution Trace**, recording:
    * Timestamp, step name, agent reasoning ("Thought"), tool called, arguments passed, response received, risk score, and human approval status.

---

#### Phase 5: Agent Development, Tool Integration & Failure Testing
*Goal: Implement the agent, connect it to the synthetic environment, and verify its resilience under error conditions.*

* **5.1. Implement Core Agent Logic & Tool Execution:**
  * Connect the reasoning engine (e.g., using LangGraph, CrewAI, or a custom state graph) to the mock APIs.
  * Verify the agent can ingest an event, select the correct tools in order, and resolve a standard problem automatically.

* **5.2. Implement Human-in-the-Loop & Safety Guardrails:**
  * Add automated risk evaluation: If an action moves hazardous cargo, changes a vessel's departure by more than 2 hours, or exceeds a budget threshold, pause and prompt the user.
  * Add schema validation to ensure the agent cannot send malformed data to backend systems.

* **5.3. Execute the 4 Robustness Test Scenarios:**
  * **Scenario 1 (Nominal Path):** Standard disruption is parsed, resolved, and verified cleanly.
  * **Scenario 2 (Incomplete Data):** A required field (e.g., container weight or customs code) is missing. The agent must pause, reason about the gap, query a secondary tool, or ask the operator for clarification.
  * **Scenario 3 (Tool/API Failure):** A downstream API returns a `503 Error` or timeout. The agent detects the failure, logs it in the trace, uses a defined fallback routine, and alerts the operator.
  * **Scenario 4 (Safety Escalation):** An action triggers a high operational risk threshold. The agent halts and produces a structured review card for human sign-off.

---

#### Phase 6: Submission Asset Creation (Demo Video & Pitch Deck)
*Goal: Package the solution clearly and persuasively according to the competition’s evaluation rubric.*

* **6.1. Build a Front-End Demo Interface:**
  * Build an intuitive web dashboard (e.g., using Streamlit or React) with:
    * *Port Operations View:* Current status, disruption alerts, and resolved states.
    * *Execution Trace Drawer:* An expandable, real-time log showing the agent's thoughts, tool calls, payloads, and approvals step by step.
    * *Human-in-the-Loop Interaction Card:* The 1-click approval/modification interface for the operator.

* **6.2. Produce the 10-Slide Pitch Deck:**
  * *Slide 1:* Executive Summary & PSA Problem Definition.
  * *Slide 2:* The Disruption Gap (Why existing CITOS/PORTNET rule engines fall short).
  * *Slide 3:* The Agentic AI Solution & Value Proposition.
  * *Slide 4:* Autonomy Level & Human-in-the-Loop Risk Framework.
  * *Slide 5:* System Architecture Diagram (Agent Core, Tool Schemas, State Memory).
  * *Slide 6:* Execution Trace Mechanics & Multi-Tool Orchestration.
  * *Slide 7:* Safety, Data Validation Guardrails, and Fallback Handling.
  * *Slide 8:* Scalability & Technical Feasibility for Real-World PSA Deployment.
  * *Slide 9:* Quantified Business Impact & ROI Model ($/TEU, dwell time, ESG).
  * *Slide 10:* Summary & Future Roadmap.

* **6.3. Record the 10-Minute Demo Video:**
  * *Part 1 (0:00–2:00):* The Operational Problem & PSA Context.
  * *Part 2 (2:00–3:30):* High-Level Solution Architecture.
  * *Part 3 (3:30–7:30):* **Live System Walkthrough:**
    * Ingest a live disruption event.
    * Show the live execution trace and tool calling in action.
    * Demonstrate handling missing data or tool failure.
    * Demonstrate the Human-in-the-Loop approval gate.
  * *Part 4 (7:30–9:00):* Safety, Guardrails, and Scalability.
  * *Part 5 (9:00–10:00):* Business Impact Math and Closing.