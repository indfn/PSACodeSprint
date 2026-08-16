# Context Intel

Running notes keyed by topic. All content copied VERBATIM from `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (per project-owner instruction: copy-paste, do not regurgitate). Lightweight topic headers added around verbatim blocks.

---

## Topic 1 — Competition Overview (Context & Expectations)
Source: `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (§1. The Core Objective & Theme)

> The competition, **PSA Code Sprint: Agentic AI in Action**, requires teams to identify a real problem within PSA Singapore's operational or supply chain ecosystem and engineer an **Agentic AI system** capable of reasoning, making decisions, and coordinating actions toward a defined objective. [scope: PSA → PSA Singapore]

---

## Topic 2 — The 4 Operational Sectors
Source: `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (§3, Phase 1, 1.1)

> * **Berth & Marine Operations:**
>     * Vessel traffic management and arrival sequencing (MPA coordination, Straits of Malacca approach).
>     * Dynamic berth allocation and quay optimization (vessel draft, tidal windows, length overall [LOA], crane split allocation).
>     * Marine services synchronization (pilotage, tugboat dispatch, mooring/unmooring, bunkering, and crew/provisioning windows).
>     * Quay Crane (QC / dual-trolley) loading and discharge sequencing.
>     * Vessel stowage planning, stability/trim constraints, and hazardous cargo onboard segregation.
>     * Transhipment connection scheduling (mother vessel to feeder vessel transfer windows and cut-off deadlines).

>   * **Container Yard & Internal Transport:**
>     * Automated Guided Vehicle (AGV) fleet management, dynamic routing, traffic deadlock resolution, and battery charging optimization.
>     * Automated Rail Mounted Gantry (aRMG) / Automated Yard Crane (aYGC) job sequencing and yard block load balancing.
>     * Container stacking optimization (transhipment clustering, import/export separation, minimizing unproductive re-handles).
>     * Refrigerated container (reefer) telemetry monitoring, power connection management, temperature excursions, and alert triage.
>     * Dangerous Goods (DG) yard storage compliance, International Maritime Dangerous Goods (IMDG) class physical segregation rules, and emergency containment protocols.
>     * Empty container depot management, maintenance and repair (M&R) routing, and repositioning flows.

>   * **Gate & External Haulage Operations:**
>     * Automated Gate System (AGS), optical character recognition (OCR), weighbridge validation, and haulier mobile authentication.
>     * Haulier booking and time-slot scheduling (OptETruck integration, dynamic slot quota adjustment).
>     * External prime mover Truck Round Trip (TRT) time optimization and gate-to-yard buffer queue management.
>     * Inter-Terminal Transfers (ITT) balancing (dedicated haulier and barge dispatching between Pasir Panjang Terminal and Tuas Mega Port).
>     * Empty container return logistics, drop-and-hook operations, and demurrage/detention tracking.

>   * **Multimodal Logistics & Supply Chain Adjacencies:**
>     * Sea-to-air multimodal transfers (OptEModal orchestration between PSA Singapore terminals and Changi Airfreight Centre). [scope: PSA → PSA Singapore]
>     * Port-adjacent warehousing and distribution (Supply Chain Hub @ Tuas [PSCH], Keppel Distripark, regional distribution centers).
>     * Regulatory and customs compliance clearance (TradeNet, Singapore Customs, MPA, phytosanitary/security inspection holds).
>     * End-to-end cargo visibility and milestone event tracking (CALISTA, BoxVoyant data ingestion).
>     * Shipper/Forwarder exception handling (manifest discrepancies, late cargo release orders, bill of lading mismatches).

---

## Topic 3 — The 7 Baseline Digital Systems (Existing PSA Singapore Digital Infrastructure)
Source: `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (§3, Phase 1, 1.2)

>   * **CITOS® (Computer Integrated Terminal Operations System):**
> 	  * PSA Singapore's proprietary, mission-critical Terminal Operating System (TOS). Serves as the operational brain orchestrating real-time berth allocation, automated quay crane (QC) split scheduling, automated rail mounted gantry (aRMG) job sequencing, Automated Guided Vehicle (AGV) fleet dispatching, and vessel stowage stability calculations. [scope: PSA → PSA Singapore]

>   * **PORTNET®:**
> 	  * PSA Singapore's nationwide B2B port community platform. Serves as the real-time digital circulatory system integrating shipping lines, freight forwarders, hauliers, financial institutions, and Singapore government agencies (MPA, Singapore Customs / TradeNet) for electronic delivery orders, container status tracking, customs clearances, and manifest reconciliation. [scope: PSA → PSA Singapore]

>   * **OptETruck:**
> 	  * PSA Singapore's AI-powered cloud transport management system (TMS) for Singapore's container trucking ecosystem. Features automated job scheduling, dynamic route optimization, and cross-company asset pooling to eliminate empty truck runs and optimize terminal gate turn times. [scope: PSA → PSA Singapore]

>   * **SmartBooking™ & iBOX™ (Intelligent Box Operation eXchange):**
> 	  * PSA Singapore's integrated depot-terminal digital exchange co-developed with the Container Depot and Logistics Association (Singapore) (CDAS). Connects off-dock container depots with PSA Singapore terminal gates to provide seamless appointment booking, gate queue visibility, and empty container repositioning. [scope: PSA → PSA Singapore]

>   * **OptEModal:**
> 	  * PSA Singapore's sea-air intermodal transhipment management platform (co-developed with Cargo Community Network [CCN]). Integrates maritime terminal operations with Changi Airfreight Centre to execute sub-24-hour sea-to-air transhipments via AI-driven ETA predictions, proactive delay identification, and flight rebooking recommendations. [scope: PSA → PSA Singapore]

>   * **CALISTA® & CALISTA P!NG™ (via CrimsonLogic / GeTS):**
> 	  * PSA Singapore's global supply chain orchestration platform. Bridges physical, regulatory (cross-border customs nodes), and financial supply chain flows, providing near-real-time milestone event telemetry and end-to-end cargo tracking across international trade corridors. [scope: PSA → PSA Singapore]

>   * **PSA BDP Enterprise Solutions:**
> 	  * PSA Singapore's supply chain orchestration and control tower platform (unifying PSA Cargo Solutions and BDP International), handling specialized cargo flows, cold-chain integrity monitoring, and chemical/hazardous logistics tracking. [scope: PSA → PSA Singapore]

---

## Topic 4 — The Three Critical Flows (per Sector)
Source: `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (§3, Phase 1, 1.3)

>   * **Physical Flow:** How containers, ships, cranes, and trucks physically move.
>   * **Information Flow:** What EDI messages, API calls, sensor alerts, and emails are sent at each step.
>   * **Decision Flow:** Who or what system decides what happens when schedules are met versus when delays occur.

---

## Index (4 topics)

- Topic 1: Competition Overview (1 verbatim block)
- Topic 2: The 4 Operational Sectors (4 verbatim sector blocks — Berth & Marine; Container Yard & Internal Transport; Gate & External Haulage; Multimodal Logistics & Supply Chain Adjacencies)
- Topic 3: The 7 Baseline Digital Systems (7 verbatim system blocks — CITOS, PORTNET, OptETruck, SmartBooking & iBOX, OptEModal, CALISTA & CALISTA P!NG, PSA BDP Enterprise Solutions)
- Topic 4: The Three Critical Flows (1 verbatim block — Physical / Information / Decision)