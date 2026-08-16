# Container Yard & Internal Transport — PSA Singapore

**Status:** Research complete (Round 1)
**Last updated:** 2026-08-17
**Verification:** Multi-source cross-verified (PSA official, A*STAR, MPA, industry sources)

---

## Process Flow

```
QUAY CRANE DISCHARGE
    │
    ▼
TRANSFER PLATFORM (DTQC gantry trolley)
    │
    ▼
AGV / IGV PICKUP ──── Fleet Management System (5G-enabled, A*STAR/IHPC algorithms)
    │                   Navigation: BTG transponder (Phase 1) → IGV natural nav (Phase 2)
    │                   Electric power: ~50% CO2 reduction vs diesel prime movers
    ▼
YARD BLOCK ASSIGNMENT ──── CITOS® yard planning
    │                       Stack optimization: transhipment clustering, import/export separation
    │                       Minimize re-handles
    ▼
aRMG / aYGC STACKING ──── 208 aRMGs at Tuas Phase 1 (ZPMC)
    │                       6-high × 10-wide stacking
    │                       AI-driven control: optimal path, collision prevention
    ▼
┌─────────────────────────────────────────────────────┐
│              CONTAINER YARD ZONES                     │
├─────────────────────────────────────────────────────┤
│                                                       │
│  REEFER ZONE ──── 13,000+ power points               │
│  │   ARMS automated monitoring (10,000+ reefers)      │
│  │   Temperature excursion alerts                     │
│  │   Power continuity management                     │
│  │                                                   │
│  DG ZONE ──── Dedicated segregated storage            │
│  │   IMDG class separation                            │
│  │   QRA-mandated safety distances                    │
│  │   500K+ TEUs DG/year (~3% of throughput)          │
│  │                                                   │
│  EMPTY DEPOT ──── On-dock depots (FTZ)               │
│  │   M&R routing                                      │
│  │   iWX AI-powered container reuse marketplace      │
│  │   Repositioning flows                              │
│  │                                                   │
│  GENERAL YARD ──── Transhipment clustering            │
│      Import/export separation                         │
│      Minimize unproductive re-handles                 │
└─────────────────────────────────────────────────────┘
    │
    ▼
HORIZONTAL TRANSPORT ──── To vessel (for loading) / To gate (for pickup)
    │                      Or inter-terminal transfer (ITT) to Pasir Panjang
    ▼
OUTBOUND
```

---

## 1. AGV Fleet Management & Dynamic Routing

### 1.1 AGV Fleet at Tuas Port

PSA Singapore operates the world's largest fleet of automated guided vehicles (AGVs) at Tuas Port, the world's single largest fully automated container terminal.

**Fleet Composition:**
- **Phase 1**: 160 AGVs from VDL and ST Kinetics, plus 46 from ZPMC (manufactured in Malaysia)
- **Phase 2**: New Intelligent Guided Vehicles (IGVs) — first batch arrived January 2026
- **Target scale**: Expansion from 32 AGVs at Pasir Panjang to potentially **2,000+ vehicles** at full Tuas capacity

**AGV Characteristics:**
- **Type**: Electric, driverless vehicles (8-wheeler configuration)
- **Navigation**: Fixed ground-based BTG transponder system (Phase 1) — highly accurate, reliable, all-weather
- **Phase 2 evolution**: IGVs with natural navigation capabilities (no fixed ground infrastructure), similar to Chinese terminal implementations
- **Power**: Electric batteries — ~50% CO2 reduction compared to diesel prime movers
- **Connectivity**: 5G-enabled (Singtel partnership) — latency reduced from 4G levels to **10ms minimum** using 3.5GHz mid-band frequency

### 1.2 Fleet Management System (FMS)

The AGV Fleet Management System is the computational brain coordinating hundreds of vehicles simultaneously. Key development:

**PSA × A*STAR IHPC Collaboration** (signed 2022, Maritime Transformation Programme funded):
- **Goal**: Large-scale fleet management solution for AGVs at Tuas
- **A*STAR contribution**: Advanced high-performance computing technologies and algorithms for accelerated solutions
- **PSA contribution**: Algorithm design expertise, simulation platform, domain knowledge
- **Focus areas**:
  - Scalable design with multiple AGVs coordinating seamlessly
  - Operational safety assurance
  - Computational load management for growing fleet
  - Cost savings through reduced infrastructure and operational costs

**5G Network Benefits:**
- 50% latency reduction vs 4G (from ~20ms to 10ms)
- Enables tighter AGV spacing → more vehicles in same area → improved yard optimisation
- Supports real-time video feeds from crane cameras and telemetry data
- Private 5G network deployed at both Tuas Port and Pasir Panjang Terminal

**Tuas Living Lab (TLL):**
- Established as real-world testbed at Tuas Port Phase 2
- Began ecosystem trials Q2 2026, fully operational Q4 2026
- Tests IGVs (Autonomous Horizontal Transports) with new Fleet Management System
- Phase 2 ASC blocks oriented **parallel to quay** (vs perpendicular in Phase 1)
- Tendered for horizontal transport Fleet Management System

### 1.3 Dynamic Routing & Deadlock Resolution

AGV routing involves:
- **Path planning**: Real-time route computation from wharf to yard block and back
- **Traffic management**: Collision avoidance at intersections and narrow passages
- **Deadlock prevention**: Algorithms to prevent circular wait conditions in dense traffic
- **Priority scheduling**: Loading operations (wharf-bound) vs discharging operations (yard-bound)
- **Battery charging optimization**: Scheduling charging cycles to minimise fleet downtime

### 1.4 Known Friction Points

- **Transponder infrastructure costs**: Fixed ground-based navigation requires pavement installation; cannot be placed near concrete rebar
- **Scalability challenges**: Fleet growth from 32 to 2,000+ requires algorithmic scalability
- **Mixed traffic zones**: Interface between automated and manually-driven vehicles (terminal tractors, service vehicles)
- **Network reliability**: 5G connectivity dependency — any outage impacts fleet coordination
- **Weather sensitivity**: Heavy rain can affect sensor performance

---

## 2. aRMG / aYGC Job Sequencing & Yard Block Load Balancing

### 2.1 Automated Yard Crane Fleet

PSA has deployed **208 automated rail-mounted gantry cranes (aRMGs)** at Tuas Port Phase 1, completing a six-year delivery programme (2020-2026) from ZPMC.

**Phase 1 aRMGs:**
- Final shipment of 5 units delivered August 2026
- **Configuration**: Stack containers 6-high and 10-wide
- **Operation**: Fully automated, managed from centralised control room
- **Control system**: Siemens automation (electrical and automation systems)
- **Productivity gain**: >10% increase vs manual operation, plus safety improvements

**Phase 2 autonomous yard cranes:**
- **First deployment**: Fully autonomous ARMGC cranes at Tuas Port Phase 2 (April 2026)
- **Technology**: AI-driven control system — no human intervention required
- **Capabilities**: Optimises container stacking and retrieval, boosts yard productivity
- **Impact**: Additional 1.5 million TEUs annually, reduced operational costs

### 2.2 Job Sequencing

aRMG job sequencing determines the order of container movements within yard blocks:

**Discharging operations (vessel → yard):**
1. AGV arrives at yard block with discharged container
2. aRMG retrieves container from AGV buffer bracket
3. aRMG stacks container at assigned position (based on classification, destination, weight)
4. Optimise for: minimum travel distance, avoid re-handles, maintain stack stability

**Loading operations (yard → vessel):**
1. aRMG retrieves container from stack position
2. Places container on AGV buffer bracket
3. AGV transports to wharf for QC loading
4. Optimise for: sequence matching with vessel stowage plan, minimum re-handles

**Key constraints:**
- Container stacking height limit (6-high)
- Weight distribution (heavier containers lower)
- Class separation (DG, reefer, general cargo)
- Connection priority (transhipment with tight cut-offs)

### 2.3 Yard Block Load Balancing

CITOS® manages yard block assignment to prevent over-concentration:

- **Transhipment clustering**: Containers for the same feeder connection grouped in adjacent blocks
- **Import/export separation**: Different blocks for import (vessel → yard → gate) and export (gate → yard → vessel)
- **Dwell time awareness**: Containers nearing departure assigned to blocks closer to wharf
- **Block utilisation monitoring**: Real-time density tracking to prevent bottlenecks
- **Dynamic rebalancing**: When blocks approach capacity, overflow containers redirected

### 2.4 Next Generation Terminal Planning System

PSA's planning system integrates:
- **Data sources**: TOS (CITOS), PORTNET, Cargo Solutions, CALISTA, Data Exchanges
- **Embedded analytics**: ML, DL, and Reinforcement Learning
- **Capabilities**:
  - Predict container dwell and connectivity
  - Predict yard activity patterns
  - Optimise land usage through efficient stacking
  - Optimise resource productivity by spreading container traffic

---

## 3. Container Stacking Optimization

### 3.1 Stacking Strategies

PSA employs multiple stacking strategies based on container type and purpose:

**Transhipment clustering:**
- Containers bound for the same feeder vessel grouped together
- Reduces aRMG travel time during loading operations
- Minimises risk of missed connections

**Import/export separation:**
- Import containers (discharged from vessel) in dedicated blocks
- Export containers (arriving by truck) in separate blocks
- Prevents interference between inbound and outbound flows

**Re-handle minimisation:**
- Algorithm predicts which containers will be retrieved next
- High-priority containers placed on top or in accessible positions
- Weight-based stacking (heavier at bottom) balanced against retrieval order

### 3.2 Stack Profile Management

- **Container positions**: Tracked in real-time by CITOS® yard inventory system
- **Height monitoring**: Automated detection of stacking heights (6-high maximum)
- **Weight verification**: Automated weight check at gate and during stacking
- **Condition tracking**: Damage, cleanliness, and structural integrity status

### 3.3 Digital Twin Integration

Siemens automation includes digital twin capabilities:
- **Block management system**: Simulation of yard block productivity
- **Modular automation**: Performance testing before deployment
- **Physics model**: Crane metal expansion/contraction, container weight effects, optimal path computation

---

## 4. Reefer Telemetry Monitoring & Power Management

### 4.1 Reefer Infrastructure

PSA Singapore maintains **13,000+ reefer power points** across its terminals, supporting temperature-sensitive cargo through the entire port stay.

**Key facilities:**
- **Dedicated reefer yards**: Designated zones with power distribution infrastructure
- **Power connection management**: Plug/unplug scheduling, power continuity monitoring
- **40 reefer platforms**: Equipped with remote SMS alerting systems for power monitoring

### 4.2 Automated Reefer Monitoring System (ARMS)

Developed in 2018 by PSA's ICT Division, ARMS represents a step-change in reefer management:

- **Capacity**: Automatically monitors **10,000+ reefer containers** simultaneously
- **Intelligent decision-making**: Algorithms detect temperature excursions and trigger alerts
- **Auto-blocking mechanism**: Malfunctioning reefers automatically blocked from vessel loading
- **Early warning**: Reduces wastage by preventing faulty reefers from being loaded then unloaded
- **Award**: Gold Award at PSA Group Innovation Awards

### 4.3 Reefer Telemetry

Shipping lines (e.g., ONE) are deploying telematic devices on reefer fleets:
- **Real-time monitoring**: Temperature, humidity, door open/close events
- **Proactive decision-making**: Early detection of equipment issues
- **Customer visibility**: Shippers receive condition reports throughout port stay
- **Integration**: Telematic data feeds into ARMS for consolidated monitoring

### 4.4 Sustainable Reefer Operations

**Refrigerant gas recovery:**
- PSA is first in Southeast Asia to trial reclaimed refrigerant gas for reefers
- ONE was first shipping line to complete trials
- **Impact**: ~4,000kg CO2 saved per reefer (equivalent to driving a car for 1 year)
- Refrigerant gas recovered, cleaned, processed, certified, and re-used

### 4.5 Known Friction Points

- **Power outage response**: Any disruption to reefer power supply risks cargo damage
- **Temperature excursion cascading**: A single malfunctioning reefer can affect adjacent units
- **Repair coordination**: Scheduling repairs without disrupting yard operations
- **Agent communication**: Daily coordination with shipping line agents for reefer priorities
- **Sensitive cargo**: High-value reefer cargo (pharmaceuticals, fresh produce) requires zero-tolerance monitoring

---

## 5. Dangerous Goods (DG) Yard Storage Compliance

### 5.1 DG Volume and Classification

PSA handles **500,000+ TEUs of dangerous goods annually** (~3% of 37+ million TEU throughput). DG management follows IMDG Code with Singapore-specific enhancements under MPA DGPE Regulations 2005.

**IMO Classes handled:**
- Class 1: Explosives (restricted — specific berths and quantities)
- Class 2: Gases (flammable, non-flammable, toxic)
- Class 3: Flammable liquids
- Class 4: Flammable solids, spontaneously combustible, dangerous when wet
- Class 5: Oxidizers and organic peroxides
- Class 6: Toxic and infectious substances
- Class 7: Radioactive materials (jointly managed with NEA)
- Class 8: Corrosive substances
- Class 9: Miscellaneous dangerous goods

### 5.2 Dedicated DG Storage Areas

Post-Tianjin 2015 incident, Singapore significantly enhanced DG yard management:

**Physical segregation:**
- Dedicated storage yards for different DG classes
- Clearly demarcated with safety distances between incompatible classes
- IMDG Code physical segregation rules enforced
- QRA (Quantitative Risk Analysis) study required before any site approval

**PSA Group Classification:**
- PSA Group 1S, 2S, 3, etc. — terminal-specific classifications
- Each group has specific handling and storage requirements
- Enquiry directed to terminal operators (PSA or Jurong Port)

### 5.3 DG Declaration and Tracking

**Electronic declaration requirements:**
- Full electronic submissions via EDI
- Mandatory information: UN Number, IMO Class, container number, packaging type, packing group, gross weight, arrival ship details
- **12 hours before arrival**: Discharging/in-transit DG
- **24 hours before arrival**: Transit DG for discharging

**Tracking:**
- DG containers tracked throughout lifecycle: on-board ships → in DG yards → at terminals
- Seamless submission by shipping lines using EDI DG declaration

### 5.4 DG Inspection and Enforcement

**MPA inspections:**
- Spot checks on vessels at terminals
- Focus: Mis-declaration, non-declaration, stowage, segregation, placarding
- Physical inspection aided by remote technology (post-COVID)
- Common infringements: Improper/missing placarding, incompatible DG segregation

**PSAC oversight:**
- Terminal operator maintains DG handling oversight
- DG warehouse inspections conducted
- Emergency Response Team supported by qualified chemists

### 5.5 Berth-Specific DG Restrictions

Per MPA DGPE Regulations (Third Schedule), specific PSA berths have DG restrictions:

- **PSA berths B01, K20-K23**: Flammable gases in isotanks prohibited
- **PSA berths B01-B09, T01-T08, K14-K23**: Flammable liquids with Class 6.1 subsidiary risk in isotanks prohibited
- **Propylene Oxide**: Prohibited at PSA berths B01-B09, T01-T08, K09-K23
- **Class 1.1, 1.2, 1.3 (except 1.3G/H)**: Prohibited at conventional berths
- **First Schedule DG**: Maximum quantities vary by berth distance from terminal fence

### 5.6 Emergency Response

- **SOPs in place** for DG incidents on-board ships before arrival
- Incident reporting: UN Number, IMO Class, severity, Master's report, mitigating measures
- Port Master approval required for berthing with DG incidents
- Serious cases: Immediate response protocols activated

---

## 6. Empty Container Depot Management

### 6.1 Depot Network

PSA operates **on-dock depots** within the Free Trade Zone (FTZ) at its terminals:

- **Full range of standard depot services**: Cleaning, repair, inspection, storage
- **Customised services**: Available to meet specific container needs
- **FTZ advantage**: Containers received/shipped at short notice without customs clearance delays
- **Strategic positioning**: Co-located with terminal operations to minimise trucking distances

### 6.2 Intelligent Warehouse eXchange (iWX)

PSA's **iWX platform** represents AI-powered warehouse logistics innovation:

**Core capabilities:**
- **Container reuse prediction**: ML models analyse gate-in/gate-out data, container attributes, transporter details to predict when containers will be ready for reuse after unstuffing
- **Optimisation engine**: When reuse isn't feasible, recommends returning containers to nearest depot
- **Marketplace model**: Transparent container availability while safeguarding trade data
- **Stakeholder autonomy**: Shipping lines approve/reject reuse requests

**Integration:**
- Data from PSA's digital ecosystem (Portnet, SmartBooking)
- Lorry Timeslot Booking for delivery/collection scheduling
- Real-time visibility into container and cargo movements

**Impact:**
- Increased container reuse rates
- Reduced transportation costs and trucking distances
- Lower carbon emissions from fewer empty trips
- Automated ownership transfers and condition verification

### 6.3 Green Pilot: Keppel Distripark to On-Dock Depot

PSA and OOCL completed a pilot integrating container flow between Keppel Distripark (KD) and On-Dock Depot (ODD):
- **Result**: 93% reduction in kgCO2e per trip due to shorter distances
- Demonstrates feasibility of depot-terminal integration for sustainability

### 6.4 Maintenance & Repair (M&R) Routing

- **In-house depot ops and M&R system**: Under review, revamp, and enhancement
- **Automated scheduling**: System routes damaged containers to appropriate repair facilities
- **Condition verification**: Photo uploads for container condition assessment
- **Coordination**: With shipping line agents and repair vendors

---

## 7. Inter-Terminal Transfer (ITT) Balancing

### 7.1 Current ITT Operations

With PSA terminals spread across Pasir Panjang and Tuas, containers must be transferred between these clusters:

**Road transport:**
- Dedicated prime movers on designated routes
- Managed through gate systems and traffic management
- Subject to traffic conditions and road capacity

**Sea transport:**
- Feeder vessels between terminal clusters
- Currently manned vessels
- MPA/PSA EOI for autonomous inter-gateway feeders (800+ TEU capacity)

### 7.2 ITT Coordination

- **Connection management**: Ensuring transferred containers connect with onward vessels
- **Timing optimisation**: Synchronising road/sea transfers with vessel schedules
- **Inventory tracking**: Real-time visibility of containers in transit between terminals
- **Congestion management**: Balancing load across road and sea transfer modes

---

## Known Friction Points & Potential Disruptions

1. **AGV fleet scaling**: Growing from 200+ to 2,000+ vehicles requires massive algorithmic and infrastructure upgrades
2. **AGV-vehicle interface**: Mixed traffic zones between automated and manual vehicles create safety and efficiency challenges
3. **Reefer power failures**: Any disruption to reefer power supply risks high-value cargo damage
4. **DG mis-declaration**: Incomplete or inaccurate DG declarations create safety incidents and handling delays
5. **Yard congestion**: Peak periods can cause yard block saturation, increasing re-handles and reducing productivity
6. **5G network dependency**: Fleet operations depend on reliable 5G connectivity
7. **Empty container surplus/shortage**: Imbalances in empty container availability across depots
8. **Equipment breakdowns**: aRMG or AGV failures cascade into yard congestion and vessel delays
9. **Inter-terminal transfer delays**: Road congestion or feeder vessel delays impact container connections

---

## Sources

| Source | URL | Verified |
|--------|-----|----------|
| PSA/A*STAR AGV Fleet Management | https://www.singaporepsa.com/2022/03/02/psa-and-astar-collaborate-on-smart-scalable-solutions-for-managing-automated-guided-vehicle-agv-fleets-in-preparation-for-tuas-port/ | ✅ |
| CNA - PSA A*STAR AGV | https://www.channelnewsasia.com/singapore/psa-singapore-astar-develop-large-scale-fleet-management-solution-agvs-tuas-port-2531431 | ✅ |
| IMDA 5G PSA Trials | https://www.imda.gov.sg/-/media/imda/files/programme/5g-innovation-and-grant/imda-5g-use-case-findings_psa.pdf | ✅ |
| PSA Tuas Living Lab | https://www.worldcargonews.com/ports-terminals/2026/03/psa-setting-up-second-living-lab-for-singapore/ | ✅ |
| PSA IGV Tender | https://www.worldcargonews.com/news/2024/12/psa-holds-igv-tender/ | ✅ |
| PSA Autonomous Yard Cranes | https://ports.marinelink.com/ports/port/miami-beach/news/psa-singapore-pioneers-fully-autonomous-yard-cranes-at-tuas-port-phase-2 | ✅ |
| Final aRMGs Tuas Phase 1 | https://www.worldcargonews.com/automation/2026/08/final-armgs-arrive-at-tuas-port-phase-1/ | ✅ |
| PSA Port Ecosystem | https://www.singaporepsa.com/our-business/portecosystem/ | ✅ |
| PSA/ONE Reefer Refrigerant Recovery | https://www.singaporepsa.com/2022/05/10/psa-one-announce-successful-use-of-reclaimed-refrigerant-gas-from-reefer-containers-as-part-of-greening-supply-chains/ | ✅ |
| ONE Reefer Telematics | https://sg.one-line.com/news/one-accelerates-digital-transformation-journey-installation-telematic-devices-reefer-fleet | ✅ |
| Siemens Automation PSA | https://www.automationworld.com/products/motion/blog/13315949/the-worlds-transshipment-hub-automates-crane-operation | ✅ |
| Cisco Digital Infrastructure | https://news-blogs.cisco.com/apjc/2023/01/17/a-peek-into-the-digital-infrastructure-underneath-psas-port-of-the-future/ | ✅ |
| PSA OptETruck | https://www.singaporepsa.com/2023/07/26/psa-innovates-with-optetruck-a-digital-solution-for-singapores-haulier-sector-to-achieve-fleet-optimisation-and-a-greener-footprint/ | ✅ |
| PSA iWX Platform | https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/new-era-warehouse-logistics-psa-singapores-ai-powered-iwx-platform | ✅ |
| PSA/OOCL Green Pilot | https://www.singaporepsa.com/2022/06/23/psa-and-oocl-complete-green-pilot-trial-for-integrated-enhanced-container-flow-between-keppel-distripark-and-on-dock-depot/ | ✅ |
| MPA DG Declaration | https://www.mpa.gov.sg/port-marine-ops/operations/gas-free-hazardous-cargo-info/declaring-dangerous-goods | ✅ |
| UN ESCAP DG Best Practices | https://www.unescap.org/sites/default/d8files/event-documents/8.5%20Best%20Practices%20of%20Dangerous%20Goods%20%28DG%29%20management%20%28Singapore%29.pdf | ✅ |
| MPA DGPE Regulations | https://sso.agc.gov.sg/SL/MPASA196-RG7?DocDate=20250228 | ✅ |
