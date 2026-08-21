# Berth & Marine Operations — PSA Singapore

**Status:** Research complete (Round 1)
**Last updated:** 2026-08-17
**Verification:** Multi-source cross-verified (PSA official, MPA official, industry sources)

---

## Process Flow

```
VESSEL APPROACH (Straits of Malacca)
    │
    ▼
VTIS/STRAITREP REPORTING ──── MPA Singapore VTS (Sectors 7-9)
    │
    ▼
ARRIVAL NOTIFICATION (12-24 hrs pre-arrival via digitalPORT@SG™)
    │
    ▼
JIT PLATFORM ──── 72-hr berth allocation notification
    │                │
    │   ┌────────────┘
    │   ▼
    │  ANCHORAGE (if early/delayed — active anchorage management)
    │   │
    │   ▼
    ▼
BOARDING GROUND ──── Pilot boarding (8 grounds: PEBGA/B/C, PSBG, PWBGA/B, PJSB, PGBG)
    │                   PSA Marine pilots (97.6% within 30 min of SRT)
    ▼
TUG DISPATCH ──── 2-3 tugs per vessel (based on LOA/draft/berth type)
    │               PSA Marine fleet: 38+ tugs (3,350-5,360 HP)
    ▼
BERTH ALLOCATION ──── CITOS® dynamic berth assignment
    │                   (vessel draft, tidal windows, LOA, crane split)
    ▼
QUAY CRANE OPERATIONS ──── DTQCs at Tuas (dual-trolley)
    │                       Standard QCs at Pasir Panjang
    │                       24-row reach, 23m deep-water draft
    ▼
STOWAGE PLANNING ──── Vessel stability/trim, DG segregation
    │                   Ship planner + CITOS® integration
    ▼
DISCHARGE / LOADING ──── QC sequencing → AGV/aRMG coordination
    │
    ▼
MARINE SERVICES (concurrent) ──── Bunkering, crew change, provisioning
    │
    ▼
DEPARTURE ──── Pilotage out → VTIS departure report
```

---

## 1. Vessel Traffic Management & Arrival Sequencing

### 1.1 VTIS and STRAITREP Framework

The Singapore Strait and port waters are among the busiest in the world, requiring an advanced Vessel Traffic Information System (VTIS) operated by the Maritime and Port Authority of Singapore (MPA). The STRAITREP system covers the Straits of Malacca and Singapore between longitudes 100°40'E and 104°23'E, divided into nine sectors. Singapore VTS manages Sectors 7-9.

Vessels required to report include:
- All vessels ≥300 GT
- Vessels ≥50 metres in length
- Towing/pushing vessels with combined GT ≥300 or length ≥50m
- Any vessel carrying hazardous cargo
- All passenger vessels fitted with VHF

Reporting is interactive VHF voice communication. The system provides real-time traffic information, identifies conflicting movements, and broadcasts safety-critical data. Singapore VTS operates with 11 VHF radio communication sets, 4 real-time X-band radar display consoles, and 4 VHF direction finders, supported by remote radar stations at locations including Pulau Angsa, Bukit Jugra, Cape Rachado, and Sultan Shoal Lighthouse.

MPA is developing a **Next Generation Vessel Traffic Management System (NGVTMS)** to replace the existing VTIS. The NGVTMS uses AI, data analytics, and machine learning to identify traffic hotspots and predict potential collisions. It is being deployed in three phases: Innovation Programme (2018-2021), Prototyping (2023-2024), and System Implementation (2024-2027).

### 1.2 Just-In-Time (JIT) Arrival Coordination

The digitalPORT@SG™ JIT Planning and Coordination Platform, fully implemented since October 2023 for PSA terminals and Jurong Port, represents a paradigm shift in vessel arrival management. The platform provides:

- **72-hour berth allocation notification**: MPA notifies Singapore-bound vessels of their berth allocation 72 hours in advance. Vessels are expected to adjust arrival timing accordingly.
- **Live ETB updates**: Any changes to Estimated Time of Berthing (ETB) are communicated through the JIT system as live notifications.
- **Anchorage management**: For delays not attributable to the vessel, MPA provides anchorage space if communicated within 12 hours (vessels from the west) or 6 hours (vessels from the east) before ETB.
- **Concurrent services**: The 72-hour window allows bunkering, crew change, provisioning, and inspections to be planned concurrently with cargo operations.

**PSA's OptEVoyage** is the carrier-facing digital solution that synchronises real-time ship-to-port data exchange to enable JIT arrivals. As of April 2024, 6 shipping lines are onboard with 99 services under trial. In 2023, OptEVoyage achieved inferred bunker savings of 52,551 metric tons and CO2 emission savings of 163,832 metric tons.

### 1.3 Pre-Arrival Notification Requirements

Vessel agents must notify MPA:
- **12 hours minimum** before arrival (vessels from nearby ports with <12 hours steaming)
- **24 hours minimum** for vessels carrying hazardous/noxious substances in bulk
- General Declaration within **24 hours** of arrival via digitalPORT@SG™

The Confirmation of Arrival report to VTIS via VHF must include: vessel name, call sign, present position, crew count (passenger vessels), ETA at first destination or pilot boarding ground, and vessel height.

---

## 2. Dynamic Berth Allocation & Quay Optimization

### 2.1 Terminal Infrastructure

PSA Singapore operates **56 berths** across multiple terminals as one seamless integrated facility:

| Terminal | Location | Berths | Capacity | Key Features |
|----------|----------|--------|----------|--------------|
| City Terminals (Tanjong Pagar, Keppel, Brani) | Southern Singapore | Multiple | Legacy | Being migrated to Tuas by 2027 |
| Pasir Panjang Terminals (PPT) | Western Singapore | 37 | 34M TEUs/yr | Deep-water, 23m draft, 24-row QC reach |
| Tuas Port Phase 1 | Tuas Western | 21 | 20M TEUs/yr | Fully automated, DTQCs, AGVs |
| Tuas Port (Full) | Tuas Western | 66 | 65M TEUs/yr | Target completion: 2040s |
| Jurong Island Terminal | Jurong Island | 2 | 400 TEUs/day | Barge service, chemicals sector |
| Sembawang Wharves | Northern Singapore | Multiple | Break-bulk | Heavy equipment, steel, cables |
| PPAT | Pasir Panjang | 3 | 20,000 car lots | Vehicle transhipment hub |

### 2.2 Berth Allocation Process

Berth allocation is managed through **CITOS®** (Computer Integrated Terminal Operations System), PSA's proprietary Terminal Operating System. The allocation considers:

- **Vessel draft and tidal windows**: Deep-water berths (23m) at PPT and Tuas accommodate the world's largest container vessels
- **Downstream tidal lockout risk**: Regional feeder destinations (Port Klang shallow berths, Chittagong, Yangon) operate on strict high-tide navigation windows. A 1-hour feeder departure delay from Singapore can cause a 10–12 hour anchorage lockout at destination — the delay is non-linear, not additive.
- **Length Overall (LOA)**: Determines berth compatibility
- **Crane split allocation**: Number of quay cranes assigned per vessel based on cargo volume and laytime
- **Equipment availability**: AGV fleet status, aRMG/aYGC job queue
- **Yard congestion**: Container stacking density and re-handle risk
- **Transhipment connections**: Feeder vessel schedules and cut-off deadlines

### 2.3 Quay Crane Operations

**At Tuas Port**: Double Trolley Quay Cranes (DTQCs) represent the latest generation of ship-to-shore equipment. The dual-trolley arrangement creates a buffer between ship-to-shore and landside movements:
- **Main trolley**: Moves containers between vessel and transfer platform
- **Gantry trolley**: Moves containers between transfer platform and AGV/buffer
- This separation optimises throughput in highly automated terminals

ZPMC recently delivered a new visual system for DTQCs at a Singapore terminal, combining the Intelligent AGV Positioning System (IAPS) and Visual Dynamic Landing System (VDLS), replacing older laser-based technology with AI-powered object detection.

**At Pasir Panjang**: Standard quay cranes with 24-row reach, being retrofitted with AI-enabled autonomous technology through PSA's partnership with Aidrivers (contract awarded 2024). This includes 3D Chassis Alignment System and real-time 3D Ship Profiling System.

### 2.4 Quay Crane Sequencing

QC sequencing determines the order of discharging and loading jobs to minimise vessel stay duration. Key constraints include:
- Vessel load profile and bay configuration
- Berthing time and available laytime
- Safety margin between adjacent QCs (minimum distance)
- Yard block congestion (preventing overly-accessed storage blocks)
- Vessel stability/trim requirements (centre of gravity must remain within specified range)

PSA's research (Choo, Klabjan, Simchi-Levi) addresses multiship QC sequencing with yard congestion constraints using mixed-integer programming and Lagrangian relaxation, enabling large-scale problems to be solved in reasonable computational time.

---

## 3. Marine Services Synchronization

### 3.1 Pilotage Services

PSA Marine Pte Ltd provides pilotage services to **180,000+ vessels annually** in the Port of Singapore. Key operational metrics (June 2026):

| Metric | Value |
|--------|-------|
| MPA KPI | 90% within 30 min of Service Required Time (SRT) |
| PSA Marine actual | **97.6% within 30 min of SRT** |
| Monthly piloted jobs | ~14,138 |
| Daily range | 427-532 jobs |
| Short-notice orders (<6 hrs) | 41.45% |
| Vessels not ready after pilot onboard | 998 vessels / 333 hours |

**Boarding Grounds**: 8 designated boarding grounds — PEBGA, PEBGB, PEBGC (Eastern), PSBG (Southern), PWBGA, PWBGB (Western), PJSB (East Johor Strait), PGBG (Gusong). Vessels arrive at 15-minute slots, with each ground receiving up to 3 vessels per slot.

**Pilotage Exemptions**: Based on vessel size and operator experience:
- <300 GT: Blanket exemption
- 300-2,000 GT: Exemption with VHF capability and local experience
- 2,000-5,000 GT: Exemption with 6 arrivals in past 12 months
- 5,000-10,000 GT (marine projects): Frequent movement exemption
- >10,000 GT: Pilotage required

### 3.2 Towage Services

Tug assignment follows MPA guidelines based on vessel size, berth type, and operation:

| Vessel LOA | Piloted (Basins/Rivers) | Piloted (Anchoring/Channeling) |
|------------|------------------------|-------------------------------|
| Up to 60m | 1S (2×370kW) | 2S (1 towing + 1 assist) |
| 61-100m | 2S (4×370kW) | 2S |
| 101-122m | 2S (4×370kW) | 2S → 3S at berthing point |
| >122m | Per pilotage guidelines | Per pilotage guidelines |

PSA Marine operates **38+ tugs** ranging from 3,350 to 5,360 HP, with bollard pull of 35-70 metric tons. Tug types include Rampart, Tractor, Pusher, and Z-tug configurations. Service level: **98.8% within 15 minutes** of SRT (2023 average).

### 3.3 Bunkering & Simultaneous Operations

Singapore supports bunkering operations concurrent with cargo handling. In May 2024, PSA achieved the **first simultaneous methanol bunkering and cargo operation (SIMOPS)** at Tuas Port:
- Conducted with X-Press Feeders using PSA's DTQCs and AGVs
- Completed in 4 hours
- Methanol delivered via mass flow metering (MFM) system
- Demonstrates readiness for commercial-scale methanol, ammonia, and hydrogen bunkering

---

## 4. Vessel Stowage Planning

### 4.1 Stowage Constraints

Vessel stowage planning must satisfy multiple simultaneous constraints:

- **Stability and trim**: Centre of gravity must remain within specified range (typically ±2 bay lengths)
- **Hazardous cargo segregation**: IMDG Code compliance for container stowage positions
- **Bay-by-bay precedence**: Deck containers discharged before hold containers; hold containers loaded before deck containers
- **Crane access**: Stowage positions must be reachable by assigned QCs without interference
- **Discharge/loading sequencing**: Containers for the same destination or connection should be accessible

### 4.2 Dangerous Goods Management

Singapore handles approximately 3% of its 37+ million TEU throughput as DG containers. DG management follows IMDG Code requirements with Singapore-specific additions:

- **Full electronic declaration**: All DG must be declared with UN Number, IMO Class, container number, packaging type, packing group, gross weight
- **Declaration timelines**: 12 hours before arrival (discharging/in-transit DG); 24 hours before arrival for transit DG
- **Dedicated DG yards**: Post-Tianjin 2015, PSA established dedicated segregated storage areas for different DG classes with safety distances
- **Quantitative Risk Analysis (QRA)**: Required before any site is approved for DG storage and handling
- **Inspections**: MPA conducts spot checks on vessels at terminals; PSAC maintains oversight of DG handling at terminals
- **Class 7 (Radioactive)**: Jointly managed with National Environment Agency (NEA)

### 4.3 Ship Planner Role

Ship planners at PSA collaborate with internal and external stakeholders to:
- Achieve optimal cargo distribution for vessel stability
- Facilitate swift vessel turnaround
- Ensure seamless connectivity in PSA Singapore's network
- Plan shift-to-shift ship planning requirements
- Coordinate with shipping lines on stowage preferences and constraints

---

## 5. Transhipment Connection Scheduling

### 5.1 Transhipment Architecture

As the **world's largest container transhipment hub**, Singapore processes a massive volume of transhipment cargo — containers transferred between mother vessels and feeder vessels. PSA's terminals operate as one integrated facility, enabling seamless connections.

**Inter-Gateway Transfers (IGT)**: Containers are moved between PSA's two main geographical clusters (Pasir Panjang Terminals and Tuas Port) via:
- **Road transport**: Prime movers on dedicated routes
- **Sea transport**: Feeder vessels between terminals

MPA and PSA launched an **Expression of Interest (EOI) in April 2026** for autonomous inter-gateway container feeder vessel operations, targeting:
- Design and development of autonomous feeder vessels capable of handling ≥800 TEU
- Multiple autonomy modes: remote-controlled with crew onboard, supervised autonomous, reduced-crew
- **Note:** All current ITT operations (2026) use manned feeder vessels. Autonomous feeder deployment is a 2029 target — scenarios in this research assume current-state manned operations unless explicitly marked as future-state.
- Remote operations centre for real-time monitoring
- Operational deployment by 2029

### 5.2 Connection Scheduling

Transhipment connection scheduling involves:
- **Mother vessel cut-off deadlines**: Time by which transhipment containers must be onloaded
- **Feeder vessel arrival windows**: Coordinated with mother vessel berthing and crane operations
- **Container dwell management**: Ensuring transhipment containers reach the correct yard position before feeder loading
- **Connection risk assessment**: Probability of missing connections based on vessel delays, crane productivity, and yard-to-wharf transport time

### 5.3 Feeder Network

Singapore's feeder network connects to regional ports across Southeast Asia, South Asia, and beyond. Feeder vessels typically range from 200-800 TEU capacity and operate on regular schedules. The JIT platform helps coordinate feeder arrivals to minimise anchorage waiting time.

---

## Known Friction Points & Potential Disruptions

Based on research, the following operational friction points are documented in Berth & Marine Operations:

1. **Vessel arrival timing mismatch**: Despite JIT, vessels arriving early or late create anchorage congestion and berth underutilisation
2. **Tidal window constraints**: Draft-restricted berths have limited windows for deep-draft vessels
3. **Crane breakdowns**: QC failures cascade into vessel delays and connection misses
4. **DG declaration errors**: Mis-declared or undeclared DG creates safety incidents and handling delays
5. **Pilot/tug availability**: Peak periods can strain marine services capacity
6. **Inter-terminal transfer delays**: IGT between Pasir Panjang and Tuas adds complexity and transit time
7. **Multi-stakeholder coordination**: Ship agents, shipping lines, terminal operators, and government agencies must synchronise — breakdowns create bottlenecks
8. **Weather disruptions**: Monsoon seasons and tropical storms affect vessel approaches and pilotage operations

---

## Sources

| Source | URL | Verified |
|--------|-----|----------|
| PSA Singapore - Port | https://www.singaporepsa.com/our-business/port/ | ✅ |
| MPA - Port of the Future | https://www.mpa.gov.sg/maritime-singapore/port-of-the-future | ✅ |
| MPA - VTIS/STRAITREP | https://www.mpa.gov.sg/port-marine-ops/operations/vessel-traffic-information-system | ✅ |
| MPA - Pilotage Guidelines | https://www.mpa.gov.sg/port-marine-ops/marine-services/pilotage-and-towage/pilotage-guidelines | ✅ |
| PSA Marine - Pilotage | https://www.psamarine.com/service/pilotage/ | ✅ |
| MPA - digitalPORT@SG™ | https://www.mpa.gov.sg/finance-e-services/digitalport@sg | ✅ |
| PSA Singapore - OptEVoyage | https://sustainableworldports.org/project/psa-singapore-optevoyage/ | ✅ |
| MPA/PSA EOI - Autonomous Feeder | https://www.mpa.gov.sg/media-centre/details/mpa-and-psa-singapore-seek-proposals-for-autonomous-shipping-to-modernise-port-operations | ✅ |
| PSA AI for Port Applications | https://www.maritimeinstitute.sg/wp-content/uploads/2023/06/PSA_Dr-Satya-Murthy_AI-for-Port-Applications.pdf | ✅ |
| Singapore Port Information 2026 | https://file.go.gov.sg/spi2026may1.pdf | ✅ |
| MPA - DG Declaration | https://www.mpa.gov.sg/port-marine-ops/operations/gas-free-hazardous-cargo-info/declaring-dangerous-goods | ✅ |
| PSA Singapore - Tuas Port | https://www.singaporepsa.com/our-business/port/ | ✅ |
| Marine Technology Review - Autonomous Feeders | https://maritimetechnologyreview.com/2026/04/22/autonomous-container-feeders-to-ply-singapore-routes/ | ✅ |
| Business Times - Singapore Autonomous Shipping | https://www.businesstimes.com.sg/singapore/singapore-invites-proposals-autonomous-shipping-kicks-maritime-startup-competition | ✅ |
| PSA LinkedIn - DTQCs | https://www.linkedin.com/posts/singaporepsa_portraitsofpsa-activity-7471033591276384256-zFTx | ✅ |
| PSA/MDPI - QC Scheduling | https://www.mdpi.com/2071-1050/12/1/24 | ✅ |
| Gard - JIT Platform | https://gard.no/insights/singapores-just-in-time-planning-and-coordination-platform/ | ✅ |
| CMA CGM/PSA OptE-Arrive | https://www.singaporepsa.com/2022/05/11/cma-cgm-and-psa-to-expand-collaboration-with-new-digital-solutions-to-reduce-carbon-footprint/ | ✅ |
