# Gate & External Haulage Operations — PSA Singapore

**Status:** Research complete (Round 1)
**Last updated:** 2026-08-17
**Verification:** Multi-source cross-verified (PSA official, MPA, industry sources)

---

## Process Flow

```
HAULIER PRE-GATE (8 hrs before ETB)
    │   SmartBooking™ / iBOX™ integration
    │   Job assignment via OptETruck
    ▼
ARRIVAL AT GATE
    │
    ├─── VEHICLE IDENTIFICATION
    │    ├── IU reader → TACS database check
    │    ├── OCR → license plate recognition
    │    ├── OCR → container number recognition
    │    └── Driver authentication (PSA Pass + fingerprint OR barcode + PIN)
    │
    ├─── SECURITY CHECKS
    │    ├── CCTV surveillance / drone monitoring
    │    ├── Weighbridge validation (VGM compliance)
    │    └── Seal verification (manual checkpoint)
    │
    ├─── DOCUMENTATION
    │    ├── ESN (Equipment Status Notification)
    │    ├── VGM declaration (SM1 or SM2 method)
    │    └── Customs clearance (TradeNet integration)
    │
    ▼
FLOW-THROUGH GATE (FTG) ──── 25 seconds processing
    │   Capacity: 700 trucks/peak hour, 9,000 trucks/day
    ▼
YARD NAVIGATION ──── Mobile phone messaging (replacing RFID tags)
    │   Container pickup/delivery location assignment
    ▼
YARD OPERATIONS
    │   ├── Export: Container delivered to yard block
    │   └── Import: Container retrieved from yard block
    ▼
GATE EXIT ──── OCR verification of container, vehicle
    │
    ▼
HAULIER POST-GATE
    │   Demurrage/detention tracking
    │   Empty container return logistics
    │   Depot drop-off (if applicable)
    ▼
OUTBOUND
```

---

## 1. Automated Gate System (AGS), OCR & Weighbridge Validation

### 1.1 Gate Infrastructure

PSA operates multiple vehicular gates across its terminals, with the **Flow-Through Gate (FTG)** system representing the industry benchmark for gate processing efficiency.

**FTG Performance Benchmarks:**
- **Processing time**: 25 seconds per container truck
- **Peak capacity**: 700 trucks per peak hour
- **Daily throughput**: 9,000 trucks per day
- **Technology**: AI-powered OCR, drone surveillance, integrated smart sensors

**Tuas Port Gate System** (commissioned March 2026):
- State-of-the-art automated gate system
- AI-powered optical character recognition (OCR)
- Drone surveillance for container inspection
- Integrated smart sensors for truck entry/exit management
- Designed for minimal manual intervention and reduced truck turnaround times

### 1.2 Three-Component Identification

A basic Gate Automation System (GAS) identifies three critical components:

**1. Driver Identification System (DIS):**
- PSA Pass (smartcard) tap at reader
- Under biometric mode: fingerprint authentication (enrolled forefinger)
- LED indicator: Green (grant) / Red (reject)
- Alternative: PSA Temporary Pass (TP) barcode scan
- Security personnel intervene for exceptions

**2. License Plate Identification System (LPIS):**
- CCTV cameras capture images from multiple angles
- OCR technology identifies and records license plates
- Real-time check against TACS (Terminal Access Control System) database
- Pre-registered vehicles granted automatic access

**3. Container Number Recognition System (CNRS):**
- OCR cameras capture container numbers from multiple positions
- Sophisticated backend algorithms handle:
  - Different container number locations
  - Two 20-foot containers on single truck chassis
  - Weather-related image quality issues
- Container number verified against booking records

### 1.3 Weighbridge & VGM Compliance

**Verified Gross Mass (VGM) process:**
1. Haulier proceeds to container lane / Self-Service Terminal (SST)
2. PSA weighbridge auto-computes cargo weight
3. System derives prime mover & trailer weight from cargo weight and container tare weight
4. VGM compared against declared weight
5. If VGM exceeds ±5% of PSA gate-derived weight:
   - Haulier can still proceed to offload container in yard
   - Must re-advise VGM in PORTNET
   - Re-advising must occur >4 hours before vessel ETB
   - After <4 hours: system blocks haulier amendment; PSA charges $10/container for last-minute updates

**VGM Cut-off Times:**
- Pre-gate container: 8 hours before vessel ETB
- Re-advise VGM: >4 hours before vessel ETB (after gate-in)
- Carrier can reject loading if VGM not updated in time

### 1.4 Tuas Port Advanced Gate Features

The newly commissioned gate at Tuas includes:
- **AI-powered OCR**: Enhanced accuracy for container and license plate recognition
- **Drone surveillance**: Aerial container inspection for damage and seal verification
- **Smart sensors**: Integrated vehicle positioning and container weight verification
- **Driver identification**: Biometric authentication (fingerprint) at vehicular gates
- **CCTV checks**: Supervisors monitor containers entering restricted areas

---

## 2. Haulier Booking & Time-Slot Scheduling

### 2.1 OptETruck Platform

**OptETruck** is PSA's proprietary AI-powered cloud transport management system (TMS) for Singapore's container trucking ecosystem.

**Core Features:**
- **Automated scheduling**: AI-based real-time resource-matching algorithm and predictive modelling
- **Asset pooling**: Enables hauliers and partners to share resources across companies
- **Route optimisation**: Powered by HERE Tour Planning and Location Services
- **Job allocation**: Based on driver location, required delivery date, ETA, incentive, shortest distance
- **Movement planner**: Interoperable with CTR, Haulio, and MDT systems

**Integration Ecosystem:**
- OptETruck + SmartBooking™ + iBOX™ = Intelligent Logistics Ecosystem
- Digitally connects container terminals, depots, hauliers, and logistics facilities

**Performance Results:**
- **Empty trip reduction**: 50% reduction (from 30-35% empty to ~15%)
- **CO2 reduction**: ~10 million kg annually (equivalent to planting 300,000 trees)
- **Adoption**: 400+ trucks (20% of Singapore haulage market) as of early 2025
- **Target**: Onboard >50% of container trucks entering/exiting PSA terminals

**OptETruck Features Detail:**

| Feature | Capability |
|---------|-----------|
| Automated Scheduling | AI recommendation based on delivery date, ETA, incentive, distance |
| Asset Pooling | Cross-company resource sharing, full auto dispatch |
| Movement Planner | Interoperability with CTR, Haulio, MDT |
| Trip Incentive | Auto calculation of trip incentives |
| Job Types | Import, Export, DPRE, ESN, PREGATE, Single/block TT Flexibook |
| Deployment | MVP developed in 2 months using agile methodology |

### 2.2 SmartBooking™ & iBOX™

**SmartBooking™:**
- One-stop online service platform connecting supply chain stakeholders
- Provides visibility of entire logistics flow
- Access to vessel schedules, container movement events, planned activities
- Enables asset optimisation and resource pooling

**iBOX™ (Intelligent Box Operation eXchange):**
- Depot management solution digitally connecting port with container depots
- Integrated with SmartBooking for seamless data exchange
- Enables truck visibility between logistics facilities and container depots
- Co-developed with CDAS (Container Depot and Logistics Association Singapore)

### 2.3 Haulier API Ecosystem

PSA launched **50+ APIs** (2021-2022) enabling digital integration:
- Hauliers' in-house systems digitally connected with PORTNET
- Automated port documentation (replacing manual processes)
- 100,000+ containers handled via APIs since 2021
- Real-time information sharing for enhanced planning

### 2.4 Lorry Timeslot Booking

**Keppel Distripark implementation** (launched April 2025):
- Mandatory timeslot booking for vehicles entering KD
- Administrative fee for vehicles entering without booking (from June 2025)
- Designed to streamline lorry scheduling, improve turnaround times

---

## 3. External Prime Mover TRT Time Optimisation

### 3.1 Truck Round Trip (TRT) Components

A typical external haulier truck round trip involves:

1. **Depot pickup**: Empty container collection from depot
2. **Gate-in**: Truck enters PSA terminal with empty container (for export stuffing) or arrives with full container
3. **Yard operation**: Container delivered to/retrieved from yard block
4. **Gate-out**: Truck exits terminal
5. **Depot drop-off**: Empty container returned to depot or full container delivered to consignee
6. **Return**: Truck returns to depot or proceeds to next job

### 3.2 TRT Optimisation Strategies

**OptETruck-driven optimisation:**
- **Job matching**: AI assigns return jobs based on truck location
- **Reduced empty runs**: From ~35% empty to ~15% through automated scheduling
- **Proximity-based assignment**: Jobs allocated to drivers near their current location
- **Asset pooling**: Cross-company truck sharing to fill empty slots

**Gate-level optimisation:**
- **FTG processing**: 25 seconds per truck (vs minutes at manual gates)
- **Pre-gate registration**: Containers pre-gated 8 hours before ETB
- **Digital documentation**: API-based port documentation eliminates manual paperwork

### 3.3 Gate-to-Yard Buffer Queue Management

- **Queue monitoring**: Real-time tracking of truck queues at gate and in yard
- **Dynamic slot adjustment**: OptETruck adjusts time-slot availability based on congestion
- **Yard navigation**: Mobile phone messaging directs drivers to correct yard block
- **Buffer zones**: Designated waiting areas to prevent yard congestion

---

## 4. Inter-Terminal Transfer (ITT) Balancing

### 4.1 Current ITT Operations

With PSA terminals spread across Pasir Panjang and Tuas, containers must be transferred between clusters:

**Road ITT:**
- Dedicated prime movers on designated routes
- Subject to traffic conditions and road capacity
- Managed through gate systems and traffic management

**Sea ITT (Feeder Vessels):**
- Currently manned feeder vessels between terminal clusters
- Moving containers between Pasir Panjang and Tuas
- MPA/PSA EOI for autonomous inter-gateway feeders (800+ TEU capacity, deployment target 2029)

### 4.2 ITT Coordination

- **Connection management**: Ensuring transferred containers connect with onward vessels
- **Timing optimisation**: Synchronising road/sea transfers with vessel schedules
- **Inventory tracking**: Real-time visibility of containers in transit
- **Congestion management**: Balancing load across road and sea transfer modes

### 4.3 Autonomous Inter-Gateway Feeder (aIGF) — Future State

MPA/PSA EOI (April 2026) targets:
- **Vessel capacity**: ≥800 TEU
- **Autonomy modes**: Remote-controlled with crew, supervised autonomous, reduced-crew
- **Remote operations centre**: Real-time monitoring and intervention
- **Energy**: Fully electric or net-zero fuel compatible from 2030
- **Routing**: High-frequency transits between PPT, Tuas Port, and Jurong Island Terminal
- **Operational deployment**: Target 2029

---

## 5. Empty Container Return Logistics

### 5.1 Empty Container Lifecycle

```
EXPORT WORKFLOW:
Depot (empty pickup) → Gate-in → Yard (stuffing) → Gate-out → Vessel loading

IMPORT WORKFLOW:
Vessel discharge → Yard (unstuffing) → Gate-out → Depot (empty return)

REPOSITIONING:
Depot A → (truck/barge) → Depot B (balancing supply/demand)
```

### 5.2 Demurrage & Detention Tracking

**Demurrage charges:**
- Levied by carrier when container not collected from port within free days
- Triggered after container discharged from vessel
- Incentivises prompt collection

**Detention charges:**
- Levied when containers not returned to depot within free days
- Terms differ between import and export workflows
- Incentivises prompt empty return

**CDAS/DHE charges:**
- Pre-booking charge for depot container collection/return
- Hauliers must pre-book timing with depot
- Some depots charge CMS (Container Management System) fees

### 5.3 Empty Container Repositioning (MT Repositioning)

**PSA Depot Services:**
- Full range of standard depot services at on-dock depots (within FTZ)
- Customised services available
- Leverages transhipment hub position for short-notice empty container movements
- Eliminates bottlenecks and saves trucking costs

**iWX Platform (Intelligent Warehouse eXchange):**
- AI-powered container reuse prediction
- ML models analyse gate-in/gate-out data, container attributes, transporter details
- Recommends suitable containers for reuse among stakeholders
- When reuse not feasible, recommends returning to nearest depot
- Automated ownership transfers and condition verification

**PSA/OOCL Green Pilot:**
- Integrated container flow between Keppel Distripark and On-Dock Depot
- **Result**: 93% reduction in kgCO2e per trip
- Demonstrates shorter-distance empty container management

### 5.4 Barge Service for Empty Repositioning

PSA and ONE launched barge service at Jurong Island Terminal:
- Container-on-barge reduces up to 30% GHG per TEU vs truck operations
- Used for empty container transport to Jurong Island
- One-stop logistics service for Jurong Island customers

---

## 6. Customs & Regulatory Compliance

### 6.1 Transhipment Procedures

For containerised cargo involving inter-gateway movement:

**Permit requirements:**
- Transhipment Agent must obtain Customs transhipment permit before arranging movement
- Agent can be freight forwarder, NVOCC, or shipping agent
- Goods sealed at entry checkpoint
- Must reach exit checkpoint within 24 hours

**FTZ procedures:**
- Produce goods and permit at FTZ "In" Gate for Customs clearance
- Produce goods and permit at FTZ "Out" Gate for clearance
- Partial clearance allowed (same permit for multiple partial clearances)

### 6.2 Non-Compliance Penalties

| Offence | First Conviction | Subsequent |
|---------|-----------------|------------|
| Import/export without permit | Fine ≤$100K or 3× goods value (whichever greater), or imprisonment ≤2 years, or both | Fine ≤$200K or 4× goods value, or imprisonment ≤3 years, or both |
| Transfer strategic goods without permit | Fine ≤$100K or 3× goods value, or imprisonment ≤2 years, or both | Fine ≤$200K or 4× goods value, or imprisonment ≤3 years, or both |

---

## Known Friction Points & Potential Disruptions

1. **Gate congestion**: Peak periods cause truck queues, extending TRT times
2. **OCR accuracy**: Weather conditions (heavy rain, fog) can reduce recognition accuracy
3. **VGM non-compliance**: Late or inaccurate VGM declarations delay vessel loading
4. **Empty container imbalances**: Supply/demand mismatches across depots create repositioning costs
5. **Demurrage/detention disputes**: Disagreements over free days and charge applicability
6. **Driver authentication delays**: Biometric system failures or pass issues create gate bottlenecks
7. **Cross-terminal coordination**: Timing synchronisation between road and sea ITT is complex
8. **Customs clearance delays**: Documentation errors or inspections cause FTZ gate hold-ups
9. **OptETruck adoption gaps**: Smaller hauliers may resist digital adoption

---

## Sources

| Source | URL | Verified |
|--------|-----|----------|
| PSA Tuas Automated Gate | https://ports.marinelink.com/ports/port/san-francisco/news/port-of-singapore-unveils-advanced-automated-gate-system-at-tuas-port | ✅ |
| PSA Port Users FAQs | https://www.singaporepsa.com/wp-content/uploads/2025/09/Port-Users-FAQs-V1.22.pdf | ✅ |
| PSA Passes & Permits | https://www.singaporepsa.com/resources/port-users/passes-and-permits/ | ✅ |
| PSA OptETruck Launch | https://www.singaporepsa.com/2023/07/26/psa-innovates-with-optetruck-a-digital-solution-for-singapores-haulier-sector-to-achieve-fleet-optimisation-and-a-greener-footprint/ | ✅ |
| HERE/PSA OptETruck | https://www.here.com/about/press-releases/PSA-collaborates-with-HERE-to-optimize-truck-operations-in-Singapore | ✅ |
| Computer Weekly - OptETruck | https://www.computerweekly.com/news/366572238/How-PSA-is-reducing-empty-trips-for-trucking-firms | ✅ |
| Sustainable World Ports - OptETruck | https://sustainableworldports.org/project/psa-singapore-optetruck/ | ✅ |
| PSA APIs for Hauliers | https://www.singaporepsa.com/2022/07/25/psa-singapore-launches-initiatives-to-drive-digital-transformation-within-the-local-haulage-industry/ | ✅ |
| PSA SmartBooking/iBOX | https://www.singaporepsa.com/2021/02/24/psa-cdas-partner-up-to-launch-smartbooking-a-one-stop-digital-solution-platform-for-the-supply-chain-community/ | ✅ |
| PSA/OOCL Green Pilot | https://www.singaporepsa.com/2022/06/23/psa-and-oocl-complete-green-pilot-trial-for-integrated-enhanced-container-flow-between-keppel-distripark-and-on-dock-depot/ | ✅ |
| MPA/PSA aIGF EOI | https://www.mpa.gov.sg/api/media/344ba444-da86-4db7-a56e-284b8b34a7f7/mpa-psa-expression-of-interest-to-design-and-develop-aigf.pdf | ✅ |
| Singapore Customs Transhipment | https://www.customs.gov.sg/doing-business/transhipment-operations/transhipment-procedures/transhipment-procedures-overview/ | ✅ |
| Port Technology - Efficient Gate | https://www.porttechnology.org/wp-content/uploads/2019/05/CHAO.pdf | ✅ |
| PSA VGM Procedures | https://www.emiratesline.com/wp-content/uploads/2024/03/0047-Singapore-Local-VGM-Notice.pdf | ✅ |
| PSA Careers - Gate Operations | https://psacareers.singaporepsa.com/en/job/493739/operations-supervisor-gate-operations | ✅ |
| PSA/ONE Barge Service | https://www.singaporepsa.com/2021/12/02/psa-one-launch-environmentally-friendly-barge-service-at-jurong-island-terminal/ | ✅ |
| Lorry Timeslot Booking | https://penanshin.com/newsletter-implementation-of-lorry-timeslot-booking-solution-at-keppel-distripark/ | ✅ |
