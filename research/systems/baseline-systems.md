# Baseline Digital Systems — PSA Singapore

**Status:** Research complete (Round 2 — Deep Research)
**Last updated:** 2026-08-17
**Verification:** Multi-source cross-verified (PSA official, World Bank, industry sources, technical docs)

---

## System Architecture Overview

PSA Singapore's digital ecosystem spans three layers:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REGULATORY / GOVERNMENT LAYER                    │
│  digitalPORT@SG™ (MPA) ──── TradeNet (Singapore Customs)           │
│  VTMS/STRAITREP ──── MPA Maritime Security                         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                    PORT COMMUNITY LAYER                              │
│  PORTNET® ──────── 15,000+ users, 350M transactions/yr             │
│  CALISTA™ ──────── Supply chain orchestration (physical/reg/financial)│
│  CALISTA P!NG™ ──── Milestone event tracking                        │
└────────┬──────────────────────┬──────────────────────┬──────────────┘
         │                      │                      │
┌────────▼────────┐  ┌─────────▼─────────┐  ┌────────▼──────────────┐
│  TERMINAL OPS   │  │  LANDSIDE OPS     │  │  MULTIMODAL OPS       │
│  CITOS®         │  │  OptETruck        │  │  OptEModal            │
│  ┌─ Berth Plan  │  │  ┌─ Job Scheduling│  │  ┌─ Sea-Air Tracking  │
│  ├─ QC Scheduling│  │  ├─ Route Optim.  │  │  ├─ AI ETA Predictions│
│  ├─ Yard Plan   │  │  ├─ Asset Pooling │  │  ├─ Delay Detection   │
│  ├─ AGV Dispatch│  │  └─ Empty Trip    │  │  └─ Flight Recommend. │
│  ├─ Ship Plan   │  │     Reduction     │  │                       │
│  └─ Gate Auto.  │  │  SmartBooking™    │  │  PSA BDP Enterprise   │
│                  │  │  ┌─ Depot Booking │  │  ┌─ Control Tower     │
│  ROCC           │  │  ├─ Queue Vis.    │  │  ├─ Smart Suite®      │
│  (Remote Crane) │  │  └─ Haulier Comm. │  │  ├─ Risk Monitor      │
│                  │  │  iBOX™            │  │  ├─ Cold Chain        │
│                  │  │  ┌─ Depot Mgmt   │  │  └─ Chemical/DG       │
│                  │  │  └─ Container    │  │                       │
│                  │  │     Exchange     │  │                       │
└─────────────────┘  └──────────────────┘  └───────────────────────┘
         │                      │                      │
┌────────▼──────────────────────▼──────────────────────▼──────────────┐
│                    DATA / INTEGRATION LAYER                          │
│  50+ APIs ──── 5G/IoT ──── AI/ML Models ──── Blockchain (OTB)     │
│  Singapore Maritime Data Hub (SG-MDH) ──── digitalOCEANS™           │
│  SGTraDex ──── Snowflake Data Platform                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. CITOS® — Computer Integrated Terminal Operations System

**Type:** Terminal Operating System (TOS)
**Role:** "Brain" of terminal operations — coordinates and integrates all port assets
**Launched:** 1988 (developed 1988, operationalized 1988–1990 following PORTNET's 1984 inception; continuously upgraded)
**Developer:** PSA in-house (proprietary)

### Core Capabilities

**Berth Allocation Subsystem:**
- Assigns berths based on vessel draft, tidal windows, LOA, crane split allocation
- Optimises quay space utilisation across 56 berths
- Integrates with PORTNET for vessel arrival data
- Considers vessel priority, schedule constraints, and equipment availability

**Quay Crane (QC) Scheduling:**
- Allocates and sequences cranes per vessel
- Dual-trolley QC coordination for Tuas Port
- Remote Crane Operations & Control (ROCC) — operators control up to 6 cranes from a central control room
- Real-time productivity monitoring

**Yard Planning Expert Subsystem:**
- Sorts containers for optimum yard space utilisation
- Minimises unproductive re-handles
- Transhipment clustering, import/export separation
- Logical stacking (not random) for faster retrievals

**AGV Fleet Management:**
- Dispatches AGVs between quay and yard
- Dynamic routing with traffic deadlock resolution
- Battery charging optimisation
- Integrates with A*STAR FMS (at Tuas)

**Ship Planning Subsystem:**
- Positions containers inside each vessel
- Allocates and sequences cranes for loading/unloading
- Stability/trim constraints
- Hazardous cargo onboard segregation
- Stowage plan generation

**Gate Automation Subsystem:**
- Records container arrival, lists weight
- Assigns location or directs delivery
- Processing time: 25-45 seconds per truck
- OCR integration for truck/container identification

**Resource Allocation Subsystem:**
- Manages operational staff deployment
- Forecasts resource requirements
- Produces deployment plans
- Real-time adjustment during operations

### Data Inputs/Outputs

| Input Source | Data Type |
|-------------|-----------|
| PORTNET | Vessel schedules, bay plans, EDI messages |
| Ship agents | Stowage instructions, cargo manifests |
| Equipment sensors | QC status, AGV position, yard crane status |
| Gate systems | Truck arrivals, container weights, OCR data |
| MPA/VTMS | Vessel traffic, approach sequences |

| Output Destination | Data Type |
|-------------------|-----------|
| Equipment operators | Real-time work instructions (wireless) |
| PORTNET | Berthing schedule, container status |
| Gate systems | Assignment locations, delivery instructions |
| Yard cranes | Stacking sequences, retrieval orders |

### Quantum Computing & AI Integration (IBM Partnership)

In September 2020, PSA partnered with IBM Research to explore quantum computing for port optimisation:

**Use Cases Under Investigation:**
- Real-time berth allocation using dynamic arrival/departure data
- Container yard stacking balancing stability, retrieval speed, and equipment limits
- Crane movement routing minimising idle time and energy use

**Technical Approach:**
- Built on IBM Qiskit framework (open-source quantum SDK)
- Uses QAOA (Quantum Approximate Optimization Algorithm) and VQE (Variational Quantum Eigensolver)
- Quantum Volume 64 benchmark devices for simulation
- Hybrid classical-quantum workflows — quantum simulators run parallel to existing AI engines
- Performance benchmarked on: container handling time/TEU, crane idle-to-activity ratio, vessel dwell time at berth

**Strategic Status:**
- PSA Group CEO Tan Chong Meng (April 2021): quantum is "on the passive horizon, not on the active horizon"
- Goal: build quantum-ready architecture deployable when commercial quantum acceleration becomes viable
- Target: Tuas Port as first terminal with integrated quantum optimization layers
- Related: Singapore's National Quantum-Safe Network (NQSN) initiative for quantum security in strategic sectors

### Known Limitations
- Proprietary system — limited external documentation
- Legacy architecture (evolved since 1984) — may have integration constraints
- Optimisation algorithms may not fully account for cross-terminal coordination (Pasir Panjang ↔ Tuas)
- Cross-terminal data latency (estimated 30–60 min for inventory synchronisation between PPT and Tuas CITOS instances via PORTNET batch messaging) is an architectural inference from PSA's terminal-partitioned operations — exact replication timing is not publicly documented for this proprietary system
- Re-optimisation under disruption (equipment failure, weather) may rely on planner simplification
- Quantum experiments still in simulation phase — not yet deployed in production

### Integration Map
- **Upstream:** PORTNET (vessel data), MPA VTMS (traffic data)
- **Downstream:** Gate systems, ROCC, equipment controllers
- **Lateral:** OptETruck (gate data), SmartBooking (container status)

---

## 2. PORTNET®

**Type:** B2B Port Community Platform (PCS)
**Role:** "Circulatory system" — manages all business-to-business information flows
**Launched:** 1984 (world's first nationwide B2B port community solution)
**Operator:** Portnet.com Pte Ltd (PSA subsidiary)

### Core Capabilities

**Scale & Reach:**
- **15,000+ users** across the logistics ecosystem
- **350 million transactions annually** on port, shipping, and logistics processes
- **200+ shipping lines** connected
- **600+ ports** across 120+ countries
- **550+ shipping companies** using the platform
- **Mandatory** for all shipping lines and logistics companies operating in Singapore

**Key Features:**
- **Vessel Operations:** Online ordering of port services (berthing, pilotage, tugs, water, bunkers)
- **Cargo Tracking:** Real-time container status (arrival, discharge, reefer temperature)
- **DG Services:** Dangerous goods enquiry and compliance
- **Ship Planning Data:** Bay plans, stowage instructions
- **Information Services:** Vessel schedule, berthing schedule, gate schedule, performance reports
- **Financial Functions:** Online billing, FEDI (Financial EDI), re-billing facilitation

**PORTNET® Mobile:**
- Real-time status gathering on mobile devices
- Alert report functions
- Anywhere, anytime terminal operations management

**EDI & API Layer:**
- **50+ APIs** launched (2022) for haulier system integration
- EDIFACT, XML, and API communication protocols
- EDI messaging with all major shipping lines
- **100,000+ containers** handled via APIs since 2021 launch

**Integration with MPA Systems:**
- Integrating with MPA's next-generation VTMS
- digitalPORT@SG™ integration for regulatory clearances
- Singapore Customs / TradeNet connectivity

### Technical Architecture

**Stack:**
- Java Enterprise Edition (JEE) environment
- Oracle WebLogic Application Server, JDK 1.6
- Apache Web server with VPN
- Centralized database management system (real-time access)
- Web-based portal (user-friendly, multi-lingual, modern UI)

**Data Collection Technologies:**
- Electronic Data Interchange (EDI) — EDIFACT, XML, JSON formats
- Radio-Frequency Identification (RFID)
- Automatic Identification System (AIS) for vessel tracking
- 50+ APIs for haulier system integration

**Communication Protocols:** EDIFACT, XML, API
**Security:** PCI DSS compliant, GDPR compliant, 2FA, DPO appointed (PDPA)
**Scalability:** Designed for increasing volume and complexity
**Cloud Ready:** Faster deployment, higher scalability

**Second-Generation PCS Features:**
- Service-oriented and open-source technology
- Interoperability with IoT, blockchain, 5G, big data
- Port4.0 initiatives
- 66+ proven and effective core Port Community processes

### Stakeholder Coverage

| Stakeholder | Usage |
|------------|-------|
| Shipping lines | Vessel schedules, cargo manifests, EDI |
| Freight forwarders | Documentation, customs clearance |
| Hauliers | Gate appointments, job orders, container status |
| Government agencies | Regulatory submissions, customs, MPA |
| Terminal operators | Berthing schedules, cargo handling |
| Cargo owners | Track and trace, reefer monitoring |

### Data Flow Patterns
1. **Vessel arrival:** Shipping line submits pre-arrival declaration → PORTNET routes to MPA/Customs
2. **Berth application:** Via PORTNET → CITOS processes → berth assigned
3. **Container tracking:** Real-time status updates from CITOS → PORTNET → stakeholders
4. **Gate operations:** Haulier submits pre-gate info via API → gate system validates
5. **Financial:** PORTNET charges → online viewing → FEDI integration

### Known Limitations
- Transaction-based pricing model (despite being mandatory)
- Some legacy EDI standards still in use alongside modern APIs
- Integration complexity with 17+ government agencies
- Data standardisation challenges across different stakeholder systems

### Awards & Recognition
- National Infocomm Award 2006 (Singapore)
- Computerworld Honors Laureate 2002 (USA)
- IDC Future Enterprise Awards 2021 (Asia Pacific)
- Logistics Solution of the Year — Seatrade Maritime Awards 2023

---

## 3. OptETruck

**Type:** AI-powered Transport Management System (TMS)
**Role:** Optimise container trucking operations across Singapore
**Launched:** 2023 (with Enterprise Singapore support)
**Developer:** PSA in-house (proprietary cloud-based)

### Core Capabilities

**Automated Scheduling:**
- Real-time resource-matching algorithm
- Predictive modelling to maximise resource utilisation
- Job matching and recommendation engine
- Location-based job allocation (proximity to driver)

**Asset Pooling:**
- Cross-company resource sharing
- Fleet optimisation across multiple hauliers
- Shared trips between logistics facilities
- Neutral platform accessible to SME hauliers

**Route Optimisation:**
- Powered by HERE Tour Planning and Location Services
- Real-time route optimisation
- Fastest route recommendations
- Reduced transit and waiting times

**Empty Trip Reduction:**
- **50%+ reduction** in empty truck runs demonstrated
- Annual reduction of **10 million kg CO2 emissions**
- Equivalent to planting **300,000 trees per year**
- Matching inbound/outbound loads

**Coverage:**
- On track to onboard **50%+ of container trucks** entering/exiting ports
- Multiple haulier companies already onboarded
- Cloud-based — accessible to SMEs with limited digital capabilities

### Integration Points
- **PORTNET:** Job data, container status, port documentation
- **SmartBooking/iBOX:** Depot booking, truck visibility
- **HERE Technologies:** Tour planning, location services, route optimisation
- **CITOS:** Gate data, container movement events

### Key Metrics
| Metric | Value |
|--------|-------|
| Empty trip reduction | 50%+ |
| CO2 reduction (annual) | 10 million kg |
| Trees equivalent | 300,000/year |
| Target truck coverage | 50%+ of port trucks |
| Award | Digital Achievers Award 2023 |

### Known Limitations
- Adoption still growing — not yet 100% haulier coverage
- Dependency on HERE Technologies for routing intelligence
- Asset pooling requires trust between competing hauliers
- Limited integration with cross-border trucking (Malaysia)

---

## 4. SmartBooking™ & iBOX™

**Type:** Integrated logistics platform + Depot management solution
**Role:** Connect terminals, depots, hauliers, and logistics facilities
**Launched:** February 2021 (jointly with CDAS)
**Developer:** PSA in-house

### SmartBooking™ — Core Capabilities

**One-Stop Booking Platform:**
- Integrated booking for container depots, terminals, hauliers, logistics facilities
- End-to-end logistics flow visibility
- Vessel schedules, container movement events, planned activities
- Job pooling and trip planning
- Resource availability tracking

**Supported by:**
- Enterprise Singapore (ESG)
- Infocomm Media Development Authority (IMDA)
- Smart Nation and Digital Government Office (SNDGO)
- Part of National AI Strategy

### iBOX™ — Core Capabilities

**Next-Generation Depot Management:**
- Digitally connects port with container depots across Singapore
- Integrated with SmartBooking for seamless data exchange
- Better truck visibility between logistics facilities and depots
- Container tracking and management

**CDAS Integration:**
- Container Depot and Logistics Association (Singapore) advisory role
- eCTS (electronic Container Trucking System) compatibility
- CMS (Container Management System) integration
- TRIP (Transport Integration Platform) alignment

### Intelligent Logistics Ecosystem

Together, SmartBooking + iBOX + OptETruck form an **Intelligent Logistics Ecosystem**:
```
Terminal (CITOS) ←→ SmartBooking ←→ iBOX ←→ Depots
                              ↕
                         OptETruck ←→ Hauliers
                              ↕
                         PORTNET ←→ All Stakeholders
```

### Awards
- IDC Future Enterprise Awards 2021 — "Best in Future of Industry Ecosystems" (Singapore)

### Known Limitations
- Depot adoption varies — smaller depots may lag
- Real-time data quality depends on depot input accuracy
- Integration with non-PSA depot systems may be incomplete

---

## 5. OptEModal

**Type:** Sea-air intermodal shipment management platform
**Role:** Bridge maritime and air cargo sectors for seamless mode transfers
**Launched:** August 2025
**Developer:** PSA + Cargo Community Network (CCN) co-created

### Core Capabilities

**Digital Corridor:**
- Integrates real-time data across PSA terminals, ground handlers, airline partners
- Seamless cargo movement between vessel and aircraft within **24 hours** of arrival
- Multi-party visibility across entire supply chain

**AI-Powered Features:**
- **ETA predictions:** Machine learning for accurate arrival forecasting
- **Proactive delay identification:** Automatic disruption detection
- **Smart flight recommendations:** AI-driven optimal connecting flight suggestions
- **Risk management:** Manage potential risks during mode transfers

**Target Industries:**
- Electronics (high-value, time-sensitive)
- Healthcare (pharmaceuticals, medical devices)
- E-commerce (fast-moving consumer goods)

**Stakeholders:**
- PSA terminals (maritime side)
- SATS and dnata ground handlers (airside)
- Airline partners
- Freight forwarders and shippers

### Integration Points
- **PSA suite:** CITOS, PORTNET data feeds
- **CCN:** Flight schedules, bookings, status tracking
- **Changi Airfreight Centre:** SATS/dnata systems
- **CALISTA:** Cargo tracking and compliance

### Known Limitations
- Recently launched (August 2025) — still early stage
- Limited to Singapore hub operations initially
- Air cargo handling capacity constraints at peak
- Cross-border regulatory harmonisation needed for full corridor

---

## 6. CALISTA™ & CALISTA P!NG™

**Type:** Global supply chain orchestration platform
**Role:** Integrate physical, regulatory, and financial flows of trade
**Launched:** April 2018
**Developer:** PSA + GeTS (Global eTrade Services, subsidiary of CrimsonLogic)
**Investment:** ~US$15 million (Phase 1)

### CALISTA™ — Core Capabilities

**Three-Pronged Approach:**
1. **Physical flow:** Container tracking, cargo movement management
2. **Regulatory flow:** Cross-border customs compliance, documentation
3. **Financial flow:** Trade financing, payments, insurance

**Scale:**
- **4,000+ parties** linked through PSA and GeTS ecosystems
- **25+ Customs nodes** globally connected (via GeTS)
- **1,000+ transactions** processed (early stage, growing)
- Coverage across **60+ economies**

**CALISTA Intelligent Agent (IA):**
- AI-driven supply chain decision support
- Route options, free trade agreements, import/export rules
- Freight recommendations based on budget and timelines
- Cargo status updates with recommended next steps
- Uses Open Trade Blockchain (OTB) for verifiable documents
- Available on desktop and mobile
- Early adopters: BINAL Asia Pacific, CWT Logistics, Elite International Logistics, PIL Logistics

**CALISTA Platform Modules:**

| Module | Capability |
|--------|-----------|
| CALISTA Intelligent Advisory (CIA) | Navigate trade processes in 180+ countries, HS/tariff codes, preferential duties |
| CALISTA Regulatory Filing | Fulfil regulatory requirements through 60+ Customs nodes, intelligent data extraction |
| CALISTA Post Clearance | Post-clearance audit readiness, record management, analytics, flexi-alerts |
| CALISTA Book & Track | Access 6,000+ global LSPs for ocean/air/rail/freight, carbon footprint calculator |
| CALISTA Finance | Invoice financing, factoring, working capital, 22-currency payments |
| CALISTA IOR | Importer of Records services |
| CALISTA BPO | Business Process Outsourcing (Singapore only) |

**Deployment Options:**
- **Plug & Play:** Sign up and access services through CALISTA platform
- **API Integration:** Maintain own UI, integrate via API
- **White Labelling:** Company branding on CALISTA UI

**Scale (updated):**
- **60+ Customs nodes** globally connected
- **90 ocean carriers & NVOCCs** connected
- **175,000+ connected parties** globally
- **24 million transactions annually** (via GeTS)
- **5 continents** with B2B and G2B expertise

**Financial Suite (launched Dec 2019):**
- Cross-border payments in **22 currencies**
- **5+ trade financing products** with 72-hour approval
- **40+ insurance products** and advisory services
- Partners: DBS, ICBC, Standard Chartered, UOB, Thunes, Rapyd

**CALISTA Inventory Financing (CIF):**
- Integrated with SGTraDex (Singapore Trade Data Exchange)
- Oil storage financing digitalisation
- Real-time trade finance data transfer
- Auditable log of records

### CALISTA P!NG™ — Core Capabilities

**Milestone Event Tracking:**
- Near-real-time visibility of key cargo event milestones
- Via Singapore trade corridor
- Free access offered during supply chain disruptions

**Key Events Tracked:**
- Estimated/Actual arrival and departure times
- Container loaded/discharged times
- Container gate in/out times

### Partnerships
- **MTI:** Ministry of Trade and Industry
- **EDB:** Economic Development Board
- **NTP:** National Trade Platform
- **DBS Bank:** Financial and banking technology
- **Singapore Customs:** TradeNet integration

### Known Limitations
- Still scaling — 4,000 parties is modest vs. total ecosystem
- Financial suite adoption requires bank partnership expansion
- Cross-border regulatory harmonisation remains challenging
- Blockchain (OTB) adoption still nascent

---

## 7. PSA BDP Enterprise Solutions

**Type:** Global supply chain, transportation, and logistics solutions provider
**Role:** Cargo Solutions arm of PSA International — end-to-end supply chain orchestration
**Formed:** April 2023 (combination of PSA Cargo Solutions + BDP International)
**Headquarters:** Philadelphia, USA
**Scale:** 152 offices globally, 6,900 employees, ~US$2 billion revenue

### Core Capabilities

**Service Portfolio:**
- Lead Logistics (LLP) and Fourth-Party Logistics (4PL) solutions
- Ocean, air, rail, and road transportation
- Barge services and complementary port services
- Origin management and export freight forwarding
- Import customs clearance and regulatory compliance
- Contract logistics and project logistics
- Warehousing and consolidation

**Industry Verticals:**
- Chemicals (hazmat classes 1-9, 60 years experience, 8 of top 10 global chemical manufacturers)
- Retail & Consumer
- Life Sciences & Healthcare
- Electric Vehicle & Industrial

### Smart Suite® — Digital Products

**Smart Navigator:**
- Real-time supply chain visibility
- Predictive ETA tracking
- Alerting and exception management
- Customised dashboards

**Risk Monitor:**
- 50+ supply chain disruption types monitored
- Weather events, port congestion, vessel events
- Geo-political events, security breaches
- Proactive risk assessment and mitigation

**Smart Classify:**
- Digital product classification tool
- HTN code validation, ECCN classification
- Machine learning from CALISTA Intelligent Advisory
- In-app communication and document sharing

**PSA BDP Temp Guard:**
- Temperature-sensitive shipment control
- Cold chain integrity monitoring
- Real-time temperature alerts

**Data Platform:**
- Snowflake-based data infrastructure
- End-to-end data solution (storage → analytics → AI/ML)
- 40% cost reduction in data ingestion/sharing
- Streamlit + Cortex AI for rapid use case development

### Integration with PSA Ecosystem
- **PORTNET:** Port operations data
- **CALISTA:** Trade compliance and financial flows
- **Roambee:** Real-time sensor intelligence (70% better ETA, 90%+ cold chain compliance)
- **BoxVoyant:** End-to-end cargo visibility

### Known Limitations
- Global operation — complexity across 152 offices
- Chemical logistics requires specialised compliance (IMDG, ADR, etc.)
- Integration of two legacy organisations (PSA Cargo Solutions + BDP)
- Smart Suite proprietary — limited third-party integration documentation

---

## Cross-System Integration Map

| System | Connects To | Integration Type |
|--------|------------|-----------------|
| CITOS | PORTNET, OptETruck, Gate systems, ROCC, equipment | Real-time data, EDI |
| PORTNET | CITOS, TradeNet, CALISTA, digitalPORT@SG, 50+ APIs | EDI, API, web services |
| OptETruck | PORTNET, SmartBooking, HERE Technologies | API, cloud |
| SmartBooking | iBOX, OptETruck, PORTNET, CITOS | API, data exchange |
| iBOX | SmartBooking, depot systems | API, data exchange |
| OptEModal | CITOS, PORTNET, CCN, Changi systems | API, real-time data |
| CALISTA | PORTNET, TradeNet, GeTS, SGTraDex, DBS/ICBC | API, blockchain |
| PSA BDP | PORTNET, CALISTA, Roambee, BoxVoyant, Snowflake | API, data platform |
| digitalPORT@SG | MPA VTMS, ICA, NEA, PORTNET, CITOS | API, web portal |
| TradeNet | PORTNET, CALISTA, Singapore Customs | EDI |

---

## Known System-Level Gaps

1. **Cross-terminal optimisation:** CITOS primarily operates per-terminal; cross-terminal (Pasir Panjang ↔ Tuas) coordination may rely on manual processes
2. **Real-time replanning:** Current systems may not support rapid replanning when disruptions cascade (equipment failure → schedule changes → truck re-routing)
3. **Empty container matching:** While OptETruck reduces empty trips, system-wide empty container balance across depots and terminals is not fully automated
4. **Data silos:** Despite integration efforts, some data may not flow seamlessly between all systems in real-time
5. **Legacy architecture:** CITOS (1984) and PORTNET (1984) have evolved over 40+ years — may have architectural constraints vs. modern microservices
6. **AI adoption:** Most AI capabilities are bolt-on (OptETruck, OptEModal) rather than deeply embedded in core TOS

---

## Sources

| Source | URL | Verified |
|--------|-----|----------|
| CITOS/PORTNET Overview (CIO) | https://www.cio.com/article/270577/infrastructure-leveraging-it-at-the-port-of-singapore.html | ✅ |
| CITOS Case Study (Scribd) | https://www.scribd.com/document/612945384/CASE-STUDY-PSA-Cruising-with-Information-System | ✅ |
| PORTNET Official | https://www.portnet.com/home | ✅ |
| World Bank PORTNET Case Study | https://documents1.worldbank.org/curated/en/099100324110022973/pdf/P176587-04998e7f-0d3c-4419-b209-61d8497e34d7.pdf | ✅ |
| OptETruck PSA Launch | https://www.singaporepsa.com/2023/07/26/psa-innovates-with-optetruck-a-digital-solution-for-singapores-haulier-sector-to-achieve-fleet-optimisation-and-a-greener-footprint/ | ✅ |
| OptETruck + HERE Technologies | https://www.here.com/about/press-releases/PSA-collaborates-with-HERE-to-optimize-truck-operations-in-Singapore | ✅ |
| OptETruck World Port Sustainability | https://sustainableworldports.org/project/psa-singapore-optetruck | ✅ |
| SmartBooking Launch | https://www.singaporepsa.com/2021/02/24/psa-cdas-partner-up-to-launch-smartbooking-a-one-stop-digital-solution-platform-for-the-supply-chain-community/ | ✅ |
| SmartBooking + iBOX Award | https://www.globalpsa.com/psa-singapore-wins-award-for-its-intelligent-logistics-ecosystem/ | ✅ |
| OptEModal PSA Launch | https://www.singaporepsa.com/2025/08/05/psa-singapore-and-cargo-community-network-launch-optemodal-to-boost-sea-air-connectivity-through-a-one-stop-digital-platform/ | ✅ |
| OptEModal Global PSA | https://www.globalpsa.com/psa-singapore-and-cargo-community-network-launch-optemodal-to-boost-sea-air-connectivity-through-a-one-stop-digital-platform/ | ✅ |
| CALISTA PSA/GeTS | https://www.globalpsa.com/psa-and-gets-team-up-to-develop-calista | ✅ |
| CALISTA Financial Suite (GTR) | https://www.gtreview.com/news/digital-trade/global-etrade-services-launches-financing-tools-on-its-supply-chain-platform | ✅ |
| CALISTA Inventory Financing | https://hr.asia/media-outreach/gets-launches-calista-inventory-financing-platform-integrated-with-sgtradex-to-digitalize-and-streamline-singapores-oil-storage-financing/ | ✅ |
| PSA BDP Rebrand (Seatrade) | https://www.seatrade-maritime.com/ports-logistics/psa-combines-cargo-solutions-and-bdp-in-rebrand | ✅ |
| PSA BDP Products (Logistics Manager) | https://logistics-manager.com/psa-cargo-solutions-and-bdp-international-form-new-brand-to-deliver-enhanced-end-to-end-supply-chain-solutions/ | ✅ |
| PSA BDP Smart Classify | https://psabdp.com/news/bdp-international-announces-smart-classify-the-new-digital-product-classification-tool | ✅ |
| PSA BDP Risk Monitor | https://www.globalpsa.com/psa-bdp-launches-risk-monitor-a-digital-product-solution-for-enhanced-risk-monitoring | ✅ |
| PSA BDP Snowflake | https://www.snowflake.com/en/customers/all-customers/video/psa-bdp | ✅ |
| digitalPORT@SG MPA | https://www.mpa.gov.sg/finance-e-services/digitalport%40sg | ✅ |
| digitalPORT@SG About | https://digitalport.mpa.gov.sg/about | ✅ |
| Digital Port Ecosystem | https://sustainableworldports.org/project/mpa-singapore-digital-port-ecosystem | ✅ |
| Singapore Port Digitalisation | https://mltechsoft.com/blog/singapore-port-digitalisation-ship-managers/ | ✅ |
| PSA 50+ APIs Launch | https://www.singaporepsa.com/2022/07/25/psa-singapore-launches-initiatives-to-drive-digital-transformation-within-the-local-haulage-industry/ | ✅ |
| CITOS/PORTNET NUS Paper | https://web2-bschool.nus.edu.sg/wp-content/uploads/media_rp/publications/dpsN51422159833.pdf | ✅ |
