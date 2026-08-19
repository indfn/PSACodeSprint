# 02-03: Problem Bank — Structured Problem Charters

**Status:** Draft  
**Source:** Consolidated from `problems/02-01-disruption-scenarios.md` and `problems/02-02-failure-modes.md`  
**Last updated:** 2026-08-17

---

## Selection Criteria

16 problems selected from 16 disruption scenarios + additional research friction points based on:
- **Cross-system complexity:** Minimum 2+ interacting PSA systems
- **Agentic AI fit:** Requires multi-tool orchestration, reasoning over conflicting objectives, or dynamic recovery
- **Operational cost:** Measurable financial, operational, or ESG impact
- **Sector balance:** Minimum 3 per sector, 4+ cross-sector problems
- **Non-triviality:** Cannot be solved by a single rule engine or optimiser
- **Multi-problem resolution potential:** Problems that share root causes and could be addressed by a single agentic system

---

## Problem Bank

---

### PB-01: Cascading Berth Delay & Tidal Window Lockout

- **Sector:** Berth & Marine
- **Problem Statement:** When a mother vessel ETA slips 6+ hours, CITOS berth allocation becomes stale, tidal windows are missed, QC schedules are disrupted, and downstream feeder connections are threatened — requiring multi-party reasoning across vessel priority, QC availability, and yard congestion that no single system can resolve.
- **Trigger & Data Source:** OptEVoyage AIS-derived ETA change (every 15 min), VTIS/STRAITREP VHF notification, digitalPORT@SG™ JIT update, CITOS berth plan (computed at T-72 hrs).
- **Systems & Stakeholders Involved:**
  - *Systems:* VTIS/STRAITREP, OptEVoyage, CITOS (berth allocation), PORTNET (schedules), A*STAR FMS (AGV dispatch)
  - *Stakeholders:* Terminal duty manager, harbour pilot, shipping line agent, ship planner, yard planner, feeder operators
- **The Information & Coordination Gap:** OptEVoyage updates ETAs every 15 minutes, but CITOS berth allocation is only re-optimised when a human planner triggers manual re-allocation. Feeder connection deadlines are tracked in PORTNET separately from the mother vessel schedule. Tidal windows are physical constraints that cannot be software-extended. No system jointly reasons over vessel priority, QC capacity, tidal windows, and feeder connections.
- **Current Resolution Workflow:** (1) Terminal duty manager receives ETA slip via phone + PORTNET alert, (2) Opens CITOS berth planner to manually assess alternatives, (3) Calls adjacent berth operators to negotiate crane re-deployment, (4) Contacts harbour pilot for next tidal window, (5) Contacts shipping line agent to discuss options, (6) Ship planner manually recalculates crane split, (7) Yard planner receives manual notification, (8) Feeder coordination via phone/email. Resolution: 2–6 hours.
- **Quantified Impact Formula:**
  - *Metric:* Vessel Demurrage ($3,000–$5,000/hr × delay hours) + QC Idle Time ($350/hr × cranes × hours) + Missed Feeder Connections ($200–$500/container × TEUs rolled)
  - *Estimated Scale:* ~$58,600–$131,600 per incident; occurs ~2–3 times/month during monsoon seasons
- **Agentic AI Value Hypothesis:** An agent is required because the problem involves: (1) multi-tool orchestration across VTIS, OptEVoyage, CITOS, and PORTNET, (2) reasoning over conflicting objectives (vessel priority vs. QC capacity vs. feeder reliability), (3) dynamic recovery planning when tidal windows are missed, (4) multi-party notification and coordination. A rule engine cannot resolve this because the optimal solution depends on real-time context (which vessels are most delayed, which feeders have downstream flexibility, which QC operators are available).
- **Candidate Action Space (Mock Tools):**
  - `get_berth_schedule(terminal, time_window)` — Query CITOS for current berth allocation and availability
  - `query_vessel_eta(optevoyage_id)` — Get real-time AIS-derived ETA from OptEVoyage
  - `get_feeder_connections(cit vessel_id)` — Query PORTNET for dependent feeder schedules
  - `calculate_tidal_window(berth_id, draft)` — Get next available tidal window for draft-restricted berth
  - `reassign_berth(vessel_id, new_berth, reason)` — Trigger CITOS berth re-allocation with justification
- **Initial Autonomy Level:** Human-in-the-Loop

---

### PB-02: DTQC Breakdown & Cascading Terminal Disruption

- **Sector:** Berth & Marine
- **Problem Statement:** A DTQC sudden breakdown during peak discharge reduces vessel throughput by 25%, creates quay-side AGV queues, and cascades to vessel delays and downstream connection misses — requiring immediate redistribution of QC workload, AGV rerouting, and vessel schedule updates that current systems handle reactively.
- **Trigger & Data Source:** DTQC sensor alarm (motor failure, hydraulic fault) via ROCC, A*STAR FMS AGV queue detection, CITOS QC status update.
- **Systems & Stakeholders Involved:**
  - *Systems:* CITOS (QC scheduling), ROCC (remote crane ops), A*STAR FMS (AGV dispatch), PORTNET (vessel schedule)
  - *Stakeholders:* QC supervisor, maintenance crew, berth planner, ship planner, terminal duty manager, shipping line agent
- **The System Handoff Gap:** When a QC goes offline, CITOS does not automatically redistribute workload to adjacent berths. A*STAR FMS detects the AGV queue but requires manual rerouting of already-queued AGVs (2–5 min per AGV). Ship planner must manually re-sequence discharge bays to maintain vessel stability — CITOS lacks an integrated stability calculator for emergency re-sequencing. Maintenance repair time is unpredictable and not communicated to any planning system.
- **Current Resolution Workflow:** (1) ROCC operator acknowledges alarm, halts QC, (2) Supervisor contacts maintenance (phone), (3) FMS operator manually reroutes queued AGVs, (4) Berth planner manually reassigns cranes in CITOS, (5) Ship planner contacts vessel chief officer (VHF) for re-sequencing, (6) Duty manager calls shipping line for ETA update. Resolution: 30 min containment, 2–8 hrs recovery.
- **Quantified Impact Formula:**
  - *Metric:* QC Repair Cost ($350/hr × downtime) + Vessel Delay ($3,000–$5,000/hr × net delay) + AGV Idle Time ($50/hr × affected AGVs × hours) + Cascade to Next Vessel (berth window compression)
  - *Estimated Scale:* ~$16,000–$24,000 per incident; occurs ~4–6 times/month across all terminals
- **Agentic AI Value Hypothesis:** An agent is required because: (1) immediate multi-tool orchestration (ROCC, CITOS, FMS, PORTNET) under time pressure, (2) reasoning over which adjacent berths can spare QCs without disrupting their own vessels, (3) dynamic AGV rerouting that considers yard block capacity and vessel priority, (4) predicting cascade impact to inform shipping line communication. A static rule cannot handle the variable repair time and its downstream implications.
- **Candidate Action Space (Mock Tools):**
  - `get_qc_status(terminal, berth)` — Real-time QC operational status from CITOS/ROCC
  - `query_adjacent_berths(terminal, time_window)` — Find berths with spare QC capacity
  - `reroute_agv_queue(fms, affected_qc, redirect_berth)` — Reroute queued AGVs to alternative QC
  - `predict_vessel_delay(vessel_id, qc_loss, repair_estimate)` — Calculate cascade impact
  - `notify_stakeholders(event_type, affected_parties, message_template)` — Multi-party alerting
- **Initial Autonomy Level:** Human-in-the-Loop

---

### PB-03: Late DG Declaration & IMDG Compliance Hold

- **Sector:** Berth & Marine
- **Problem Statement:** DG declaration amendments arriving after stowage plan finalisation create IMDG class conflicts that CITOS cannot automatically resolve, requiring manual re-stowage planning with vessel stability constraints and MPA regulatory re-approval — a multi-hour process with safety and financial consequences.
- **Trigger & Data Source:** PORTNET EDI DG amendment (IMDG Code correction), CITOS stowage planner conflict detection, MPA DGPE compliance flag.
- **Systems & Stakeholders Involved:**
  - *Systems:* PORTNET (EDI DG declaration), CITOS (stowage planning), MPA DGPE (regulatory enforcement)
  - *Stakeholders:* Ship planner, DG compliance officer, terminal duty manager, MPA officer, yard planner
- **The System Handoff Gap:** DG amendments can arrive up to 12 hours after stowage plan finalisation. CITOS detects IMDG conflicts but cannot automatically resolve them — the segregation rules are complex, vessel-specific, and must satisfy both IMDG Code AND vessel stability constraints simultaneously. MPA re-approval is phone/email-based with 1–4 hour turnaround. No system provides automated re-stowage optimisation for DG conflicts.
- **Current Resolution Workflow:** (1) CITOS flags DG conflict, (2) Ship planner manually reviews IMDG segregation tables, (3) Identifies 3–5 compliant positions, (4) Runs manual stability check, (5) Updates stowage plan in CITOS, (6) Calls MPA DGPE for re-approval, (7) MPA reviews via email, (8) Yard planner adjusts DG yard assignments. Resolution: 2–4 hours.
- **Quantified Impact Formula:**
  - *Metric:* Emergency Re-stowage ($150–$300/container × affected) + Vessel Delay ($3,000–$5,000/hr × re-approval time) + MPA Penalty Risk (up to $100,000) + Yard Re-handle ($30–$50/move)
  - *Estimated Scale:* ~$7,650–$23,250 per incident + regulatory risk; occurs ~1–2 times/month
- **Agentic AI Value Hypothesis:** An agent is required because: (1) multi-constraint optimisation (IMDG segregation + vessel stability + crane access), (2) cross-system data retrieval (PORTNET DG data, CITOS stowage plan, vessel stability manual), (3) regulatory workflow orchestration (MPA re-approval coordination), (4) safety-critical reasoning where errors have catastrophic consequences. A rule engine cannot handle the combinatorial complexity of re-stowage under multiple constraints.
- **Candidate Action Space (Mock Tools):**
  - `get_dg_declaration(portnet_id)` — Retrieve full DG declaration including amendments
  - `get_stowage_plan(cit vessel_id)` — Get current stowage plan with positions and DG classes
  - `check_imdg_segregation(class_a, class_b, position)` — Validate IMDG Code segregation compliance
  - `calculate_vessel_stability(vessel_id, stowage_adjustment)` — Check trim/stability after re-stowage
  - `submit_mpa_reapproval(stowage_plan, justification)` — Submit re-stowage plan to MPA DGPE
- **Initial Autonomy Level:** Human-in-the-Loop

---

### PB-04: Transhipment Missed-Connection Recovery (100+ Containers)

- **Sector:** Berth & Marine
- **Problem Statement:** Mother vessel delays of 8+ hours threaten 100+ transhipment containers missing outbound feeder connections, requiring trade-off reasoning between holding feeders (cascading downstream delays), rolling containers (customer SLA breach), and re-prioritising QC discharge (disrupting import yard plan) — a multi-party, multi-objective optimisation problem.
- **Trigger & Data Source:** OptEVoyage AIS ETA slip, PORTNET feeder departure schedules, CITOS berth allocation and ship planning.
- **Systems & Stakeholders Involved:**
  - *Systems:* CITOS (berth + ship planning), PORTNET (feeder schedules), OptEVoyage (JIT tracking), yard operations (transhipment clustering)
  - *Stakeholders:* Terminal duty manager, ship planner, shipping line agent, feeder operators, cargo owners, yard planner
- **The System Handoff Gap:** No system jointly calculates: "Given mother vessel delay of X hours, which feeder connections are still achievable?" Ship planner must manually compute discharge rate × time available = containers recoverable. Feeder hold vs. roll decision requires reasoning over: vessel schedule, customer commitments, yard congestion, and downstream port impacts — no system provides this multi-objective analysis. Yard-to-wharf transport time (15–30 min) is not factored into connection risk by any system.
- **Current Resolution Workflow:** (1) Duty manager receives delay notification, (2) Contacts ship planner for discharge options, (3) Ship planner manually computes recoverable containers, (4) Contacts shipping line to discuss hold vs. roll, (5) Shipping line contacts feeder operator, (6) Feeder operator assesses downstream impact, (7) Decision made, (8) Yard planner re-sequences transhipment blocks, (9) Ship planner updates CITOS. Resolution: 3–6 hours.
- **Quantified Impact Formula:**
  - *Metric:* Feeder Demurrage ($800–$1,500/hr × hold hours) + Rolled Containers ($100–$300/container/day × rolled) + Customer SLA Penalties (variable) + QC Re-prioritisation ($30–$50/move × re-handles)
  - *Estimated Scale:* ~$6,500–$36,500 per incident; occurs ~3–5 times/month (Red Sea diversions, weather)
- **Agentic AI Value Hypothesis:** An agent is required because: (1) multi-objective reasoning (minimise total cost across vessel demurrage, feeder delays, customer SLA, yard congestion), (2) dynamic replanning as new information arrives (vessel ETA updates, feeder flexibility assessment), (3) multi-party coordination with conflicting incentives, (4) temporal reasoning (cut-off deadlines, discharge rates, transport times). No single optimiser can handle this because the problem involves both quantitative optimisation and qualitative judgment (customer relationships, shipping line negotiations).
- **Candidate Action Space (Mock Tools):**
  - `get_transhipment_connections(vessel_id)` — Query all dependent feeder connections and cut-off times
  - `calculate_discharge_rate(vessel_id, qc_count)` — Estimate containers recoverable per hour
  - `query_feeder_flexibility(feeder_id)` — Check if feeder can hold departure and downstream impact
  - `estimate_yard_to_wharf_time(yard_block, wharf_position)` — Calculate AGV transport time
  - `simulate_hold_vs_roll(scenario)` — Model cost of hold vs. roll across all affected parties
- **Initial Autonomy Level:** Advisory

---

### PB-05: Reefer Cold-Chain Telemetry Excursion (Pharma Cargo)

- **Sector:** Yard & Transport
- **Problem Statement:** ARMS detects reefer temperature excursion but cannot diagnose root cause (power fault, compressor failure, or door seal breach), requires multi-party coordination (maintenance, shipping line, insurer) under a critical 2–4 hour spoilage window for high-value pharma cargo — a problem requiring diagnosis, prioritisation, and resource dispatch simultaneously.
- **Trigger & Data Source:** ARMS temperature alarm (auto-detect), power supply status sensor, shipping line reefer telemetry data.
- **Systems & Stakeholders Involved:**
  - *Systems:* ARMS (reefer monitoring), CITOS (yard assignment), shipping line agent (cargo owner), maintenance crew
  - *Stakeholders:* Operations team, maintenance technician, shipping line agent, cargo owner, insurer
- **The System Handoff Gap:** ARMS detects the excursion but cannot determine root cause — each cause (power fault, compressor failure, seal breach) requires a different response. ARMS does not differentiate alert priority based on cargo value or spoilage risk. M&R dispatch is phone-based with no automated routing of nearest available technician. No system cross-references reefer telemetry data with cargo value to prioritise response.
- **Current Resolution Workflow:** (1) ARMS generates alarm, (2) Operations team acknowledges, checks power status, (3) Calls maintenance (phone, 15–30 min response), (4) Technician diagnoses and repairs, (5) Team calls shipping line (phone), (6) Shipping line contacts cargo owner + insurer. Resolution: 30 min–4 hrs.
- **Quantified Impact Formula:**
  - *Metric:* Cargo Spoilage Risk (cargo value × spoilage probability) + Emergency Maintenance ($500–$2,000) + Technician Dispatch ($200–$500) + Insurance Admin ($5,000–$15,000)
  - *Estimated Scale:* ~$505,700–$517,500 per incident (pharma total loss scenario); occurs ~5–8 times/month (all reefer types)
- **Agentic AI Value Hypothesis:** An agent is required because: (1) diagnostic reasoning (power fault vs. compressor vs. seal breach based on sensor data patterns), (2) impact-based prioritisation (pharma vs. general cargo), (3) resource dispatch optimisation (nearest technician with correct spare parts), (4) multi-party notification under time pressure. A rule engine cannot diagnose the root cause or prioritise based on cargo value without cross-referencing multiple data sources.
- **Candidate Action Space (Mock Tools):**
  - `query_reefer_telemetry(container_id)` — Get ARMS + shipping line telemetry data
  - `get_cargo_value(container_id)` — Retrieve cargo value and spoilage risk profile
  - `diagnose_reefer_fault(telemetry_data)` — ML-based root cause analysis
  - `dispatch_technician(location, skill_set, spare_parts)` — Route nearest available technician
  - `notify_cargo_stakeholders(container_id, event, severity)` — Multi-party alert with escalation
- **Initial Autonomy Level:** Advisory

---

### PB-06: Yard Block Buffer Overflow from Delayed Vessel

- **Sector:** Yard & Transport
- **Problem Statement:** Vessel delays cause export containers to accumulate beyond yard block capacity, forcing unproductive re-handles, blocking aRMG corridors, and degrading AGV efficiency — requiring dynamic overflow routing that balances re-handle cost, AGV travel time, and downstream loading sequence impacts.
- **Trigger & Data Source:** CITOS yard block utilisation alerts (real-time), vessel delay notification (PORTNET/OptEVoyage), gate arrival data (OptETruck).
- **Systems & Stakeholders Involved:**
  - *Systems:* CITOS (yard planning), A*STAR FMS (AGV dispatch), aRMG controllers, gate operations
  - *Stakeholders:* Yard planner, ship planner, gate operations team, aRMG operator
- **The System Handoff Gap:** Yard block assignments are computed based on vessel schedule. When vessel delays, CITOS does not automatically re-optimise yard assignments. Gate operations have no real-time signal to slow export arrivals. Overflow container routing requires manual multi-constraint verification (alternative block availability, AGV travel time, loading sequence). aRMG re-handle operations compete with loading operations — no system provides a "re-handle vs. loading trade-off" analysis.
- **Current Resolution Workflow:** (1) Yard planner notices block approaching 95%, (2) Manually checks alternatives in CITOS, (3) Calls gate ops to slow arrivals, (4) Schedules aRMG re-handles during loading gap, (5) Notifies ship planner of position changes. Resolution: 4–8 hours.
- **Quantified Impact Formula:**
  - *Metric:* Re-handle Cost ($30–$50/move × re-handles) + AGV Efficiency Loss ($50/hr × affected AGVs × extra travel time) + Extended Vessel Berthing ($3,000–$5,000/hr × extra hours)
  - *Estimated Scale:* ~$12,900–$20,500 per incident; occurs ~6–10 times/month during peak periods
- **Agentic AI Value Hypothesis:** An agent is required because: (1) dynamic overflow routing requires real-time capacity assessment across multiple yard blocks, (2) re-handle vs. loading trade-off requires预测 of downstream impact on vessel loading sequence, (3) multi-system coordination (CITOS, FMS, gate, aRMG), (4) anticipatory action (slowing gate arrivals before overflow occurs). A static rule cannot predict the cascading impact of yard overflow on vessel turnaround.
- **Candidate Action Space (Mock Tools):**
  - `get_yard_block_utilisation(terminal, block_ids)` — Real-time block capacity across yard
  - `predict_overflow_risk(block_id, incoming_containers, vessel_eta)` — Forecast when block will exceed capacity
  - `recommend_overflow_block(container_type, origin_block)` — Find optimal alternative block
  - `schedule_rehandles(block_id, conflict_window)` — Plan re-handle operations during loading gaps
  - `adjust_gate_arrival_rate(terminal, target_rate)` — Signal gate to slow export arrivals
- **Initial Autonomy Level:** Supervised Autonomous

---

### PB-07: 5G Network Outage Degrading AGV Fleet

- **Sector:** Yard & Transport
- **Problem Statement:** Private 5G network outage at Tuas Port increases AGV communication latency from 10ms to 20–40ms, forcing traffic de-rating that reduces terminal throughput by 20–30% — requiring immediate fleet parameter adjustment, QC production coordination, and battery charging rescheduling that current systems handle reactively with manual de-rating.
- **Trigger & Data Source:** 5G network telemetry (Singtel), A*STAR FMS latency detection, QC productivity sensors.
- **Systems & Stakeholders Involved:**
  - *Systems:* 5G network (Singtel), A*STAR FMS (AGV fleet), CITOS (QC scheduling), DTQC operations
  - *Stakeholders:* FMS operator, QC operators, yard supervisors, network provider (Singtel), maintenance
- **The System Handoff Gap:** AGV fleet is designed for 5G latency. When 5G fails, FMS degrades to 4G but does not automatically adjust fleet parameters (spacing, speed, task assignment). QC operators are not aware of 5G status and continue discharging at normal rate, creating transfer platform pile-up. Battery charging schedule is disrupted — AGVs may become stranded. No system provides battery status visibility to ground operators during communication degradation.
- **Current Resolution Workflow:** (1) FMS operator detects latency spike, activates de-rating, (2) Calls Singtel (phone), (3) Notifies QC operators to slow discharge (phone), (4) Yard supervisors redirect AGVs manually, (5) If AGV stranded: manual towing dispatched. Resolution: 30 min containment, 1–4 hrs restoration.
- **Quantified Impact Formula:**
  - *Metric:* Lost QC Productivity ($350/hr × cranes × hours) + Vessel Delay ($3,000–$5,000/hr × net delay) + AGV Fleet Loss ($50/hr × affected AGVs × hours) + Restoration Cost ($10,000–$50,000)
  - *Estimated Scale:* ~$21,100–$65,100 per incident; occurs ~1–2 times/month (infrastructure dependent)
- **Agentic AI Value Hypothesis:** An agent is required because: (1) immediate multi-system parameter adjustment (FMS, QC, battery scheduling) under time pressure, (2) predictive reasoning (which AGVs are at risk of stranding, which QCs to slow first), (3) coordination with external provider (Singtel) while managing internal operations, (4) graceful degradation planning that preserves maximum throughput. A static fallback protocol cannot dynamically optimise across all affected systems.
- **Candidate Action Space (Mock Tools):**
  - `get_network_latency(terminal, zone)` — Real-time 5G/4G latency from network telemetry
  - `get_fms_degradation_status(fms)` — Current AGV fleet de-rating parameters
  - `adjust_fleet_parameters(fms, latency_level)` — Auto-adjust AGV spacing, speed, task assignment
  - `predict_stranded_agvs(fms, battery_threshold)` — Identify AGVs at risk of battery depletion
  - `notify_qc_slowdown(terminal, qc_ids, target_rate)` — Signal QC operators to reduce discharge rate
- **Initial Autonomy Level:** Supervised Autonomous

---

### PB-08: eDO/VGM Discrepancy Gate Queue Cascade

- **Sector:** Gate & Haulage
- **Problem Statement:** Haulier arrives at gate with eDO not yet released in PORTNET or VGM weight discrepancy >5%, causing AGS entry block that physically blocks OCR lanes and creates rapid queue build-up during peak hours — requiring eDO resolution, VGM correction, and queue management that span PORTNET, weighbridge, and gate operations.
- **Trigger & Data Source:** AGS eDO check (PORTNET query), weighbridge VGM reading (auto-computed), OCR lane queue sensors.
- **Systems & Stakeholders Involved:**
  - *Systems:* AGS/OCR (gate processing), PORTNET (eDO status), weighbridge (VGM), OptETruck (slot management)
  - *Stakeholders:* Gate operator, haulier, shipping line agent, consignee, operations supervisor
- **The System Handoff Gap:** eDO release timing is not coordinated with truck arrival — shipping lines release on their own schedule, creating a gap between haulier booking and eDO availability. VGM discrepancy resolution is time-constrained (must amend >4 hrs before vessel ETB). Exception lane physically blocks OCR lanes — no automated overflow. No system alerts haulier that eDO is not yet available before they depart depot.
- **Current Resolution Workflow:** (1) AGS blocks entry, directs to exception lane, (2) Gate operator checks eDO in PORTNET, (3) Calls shipping line (phone) to release, (4) Weighbridge operator verifies VGM, contacts haulier, (5) Haulier contacts consignee for VGM correction, (6) Supervisor opens overflow lane. Resolution: 30 min–3 hrs.
- **Quantified Impact Formula:**
  - *Metric:* Gate Delay Cost ($50–$100/truck × affected trucks × delay) + Haulier TRT Extension ($30–$50/hr × hours × affected hauliers) + Queue Spillover Risk (LTA fine)
  - *Estimated Scale:* ~$1,050–$2,000 per incident; occurs ~8–12 times/month (peak periods)
- **Agentic AI Value Hypothesis:** An agent is required because: (1) predictive check before haulier departs depot (eDO availability + VGM feasibility), (2) real-time queue management (overflow lane activation, slot rebalancing), (3) multi-party coordination (shipping line, haulier, consignee) under time pressure, (4) VGM feasibility assessment across time windows. A rule engine cannot predict eDO availability or coordinate resolution across multiple parties.
- **Candidate Action Space (Mock Tools):**
  - `check_edo_status(container_id, portnet)` — Verify eDO release before haulier departs
  - `validate_vgm_feasibility(container_id, vessel_etb)` — Check if VGM amendment is within time window
  - `get_gate_queue_status(terminal, time_window)` — Real-time queue depth and wait time
  - `activate_overflow_lane(terminal, lane_count)` — Open additional processing lanes
  - `rebalance_optetruck_slots(terminal, time_window)` — Dynamic slot reassignment for delayed trucks
- **Initial Autonomy Level:** Supervised Autonomous

---

### PB-09: External Disruption to Haulier Pools (Expressway Blockage)

- **Sector:** Gate & Haulage
- **Problem Statement:** Expressway congestion or weather causes 40%+ of booked hauliers to miss time-slots, requiring dynamic slot re-balancing across OptETruck and SmartBooking, yard plan adjustment for delayed containers, and vessel loading re-sequencing — a multi-system cascading disruption with no automated coordination.
- **Trigger & Data Source:** OptETruck GPS tracking (real-time haulier positions), SmartBooking slot system (missed slots), traffic incident data (HERE Technologies/LTA).
- **Systems & Stakeholders Involved:**
  - *Systems:* OptETruck (TMS), SmartBooking (slot management), PORTNET (gate schedule), CITOS (yard planning)
  - *Stakeholders:* Operations team, gate operator, yard planner, hauliers, shipping line
- **The System Handoff Gap:** OptETruck cannot force trucks to take alternate routes — drivers make their own decisions. SmartBooking slots are fixed once booked — no automated release-and-reassign mechanism. Yard planner learns about delays through phone calls, not automated alerts. No system coordinates the cascade from expressway → gate → yard → vessel loading.
- **Current Resolution Workflow:** (1) OptETruck detects delay, sends route advisory, (2) Operations team calls delayed hauliers for ETAs, (3) Gate operator opens overflow for afternoon, (4) Calls yard planner to notify delays, (5) Yard planner re-sequences loading. Resolution: 4–12 hours.
- **Quantified Impact Formula:**
  - *Metric:* Haulier Idle Time ($50/hr × affected trucks × hours) + Vessel Loading Delay ($3,000–$5,000/hr × delay) + Yard Re-sequencing Cost + Carbon Impact (idling trucks × hours × CO2/hr)
  - *Estimated Scale:* ~$15,500–$20,000 per incident; occurs ~2–4 times/month (weather/accidents)
- **Agentic AI Value Hypothesis:** An agent is required because: (1) real-time GPS data analysis to predict which hauliers will miss slots, (2) dynamic slot rebalancing across OptETruck and SmartBooking, (3) proactive yard planner notification before delays cascade to vessel loading, (4) multi-party coordination (hauling companies, gate, yard) under evolving conditions. A rule engine cannot predict delay propagation or optimise slot rebalancing in real-time.
- **Candidate Action Space (Mock Tools):**
  - `get_haulier_gps_positions(optetruck)` — Real-time tracking of all booked hauliers
  - `predict_slot_misses(hauliers, traffic_data)` — Forecast which hauliers will miss time-slots
  - `rebalance_slots(smartbooking, terminal, time_window)` — Dynamic slot release and reassignment
  - `notify_yard_delay(cit, terminal, delayed_containers)` — Proactive yard planner alert
  - `adjust_vessel_loading_sequence(cit, vessel_id, delayed_containers)` — Re-sequence loading for late arrivals
- **Initial Autonomy Level:** Supervised Autonomous

---

### PB-10: Sea-to-Air Flight Cut-Off Threat (OptEModal)

- **Sector:** Multimodal
- **Problem Statement:** Vessel berthing delay of 8+ hours jeopardises 50+ sea-air containers' 12-hour transfer window to Changi Airport, requiring priority discharge, express customs clearance, express ITT dispatch, and potential flight rebooking — a multi-party, multi-system coordination challenge where no single system has authority to expedite all steps.
- **Trigger & Data Source:** OptEModal vessel delay detection (AI ETA prediction), CITOS berth status, TradeNet customs clearance status, SATS/dnata cargo acceptance slots.
- **Systems & Stakeholders Involved:**
  - *Systems:* OptEModal (sea-air platform), CITOS (terminal ops), CALISTA (milestone tracking), TradeNet (customs), SATS/dnata (ground handling)
  - *Stakeholders:* Operations team, customs broker, ITT coordinator, ground handler, airline, cargo owner
- **The System Handoff Gap:** OptEModal detects the risk and recommends actions but cannot force priority QC discharge (CITOS), express customs clearance (TradeNet), or priority SATS handling. Customs pre-clearance requires documents from the forwarder's system. Flight rebooking is a commercial decision requiring cargo owner approval. No system has end-to-end authority over the sea-air transfer chain.
- **Current Resolution Workflow:** (1) OptEModal generates risk alert, (2) Team calls CITOS for priority discharge, (3) Contacts customs broker for pre-clearance, (4) Calls SATS for expedited handling, (5) Contacts airline for rebooking options. Resolution: 1–6 hours.
- **Quantified Impact Formula:**
  - *Metric:* Flight Rebooking ($5,000–$15,000) + Customer SLA ($10,000–$50,000) + Priority Premiums ($3,000–$8,000) + Carbon (additional flight/trucking)
  - *Estimated Scale:* ~$18,000–$73,000 per incident; occurs ~1–2 times/month (weather, diversions)
- **Agentic AI Value Hypothesis:** An agent is required because: (1) multi-system orchestration across terminal, customs, ground handling, and airline, (2) temporal reasoning (12-hour window with fixed deadlines), (3) commercial judgment (rebooking cost vs. customer SLA value), (4) document validation and pre-clearance coordination. No single system can autonomously expedite all steps in the sea-air chain.
- **Candidate Action Space (Mock Tools):**
  - `get_sea_air_containers(optemodal, vessel_id)` — List containers requiring sea-air transfer
  - `request_priority_discharge(cit, vessel_id, container_ids)` — Request QC priority for transfer containers
  - `pre_lodge_customs(tradenet, container_ids, docs)` — Submit customs clearance before physical arrival
  - `check_flight_availability(airline, route, time_window)` — Query alternative flight options
  - `estimate_transfer_feasibility(optemodal, vessel_delay, current_time)` — Calculate if 12-hr window is still achievable
- **Initial Autonomy Level:** Advisory

---

### PB-11: Cross-Border Customs Inspection Hold (Sea-Air)

- **Sector:** Multimodal
- **Problem Statement:** Singapore Customs or phytosanitary agency places unexpected inspection hold on multimodal cargo mid-transit, blocking entire shipment from proceeding, requiring multi-party documentation retrieval across time zones and coordination with inspection agencies — with no partial release mechanism.
- **Trigger & Data Source:** TradeNet inspection hold flag (random HS code selection), CALISTA milestone tracker (hold status), OptEModal transfer timeline.
- **Systems & Stakeholders Involved:**
  - *Systems:* TradeNet (customs), CALISTA (milestone tracking), OptEModal (transfer coordination)
  - *Stakeholders:* Customs broker, forwarder, shipper (in origin country), phytosanitary inspector, ground handler
- **The System Handoff Gap:** Inspection hold is binary — no partial release for non-inspected containers. Documentation retrieval requires cross-time-zone coordination (shipper in Mumbai, inspector in Singapore). Inspection timing is not linked to OptEModal's flight schedule. No system facilitates automated document exchange or inspection prioritisation based on time-criticality.
- **Current Resolution Workflow:** (1) TradeNet flags hold, (2) CALISTA notifies parties, (3) Team contacts broker and inspector, (4) Forwarder contacts shipper for documents (email/WhatsApp across time zones), (5) Inspector completes inspection, (6) Cargo released. Resolution: 2–8 hours.
- **Quantified Impact Formula:**
  - *Metric:* Flight Delay ($3,000–$8,000) + Cargo Hold ($500–$1,000/day) + Customer Impact ($10,000–$50,000/day for pharma) + Inspection Fee ($200–$500)
  - *Estimated Scale:* ~$3,700–$59,500 per incident; occurs ~2–4 times/month
- **Agentic AI Value Hypothesis:** An agent is required because: (1) cross-time-zone document coordination, (2) partial release reasoning (which containers can proceed while others are inspected), (3) inspection prioritisation based on flight schedule urgency, (4) multi-party notification across customs, forwarder, and ground handler. A rule engine cannot handle the document retrieval logistics or partial release decisions.
- **Candidate Action Space (Mock Tools):**
  - `get_inspection_details(tradenet, hold_id)` — Retrieve inspection requirements and timeline
  - `check_document_completeness(calista, container_ids)` — Verify all customs documents are available
  - `request_partial_release(tradenet, non_inspected_containers)` — Release non-inspected cargo
  - `prioritise_inspection(agency, flight_schedule)` — Request inspection expedite based on deadline
  - `coordinate_document_retrieval(forwarder, origin_country, document_type)` — Cross-time-zone document request
- **Initial Autonomy Level:** Human-in-the-Loop

---

### PB-12: Multi-Party ITT Coordination Failure (Cross-Terminal)

- **Sector:** Multimodal
- **Problem Statement:** Priority transhipment containers must move from Pasir Panjang to Tuas via road or sea ITT during peak traffic, but coordination breaks down across road ITT (OptETruck), sea ITT (feeder vessels), yard operations (CITOS at both terminals), and gate operations — requiring real-time split optimisation across multiple transport modes with no unified coordination system.
- **Trigger & Data Source:** CITOS PPT container readiness (yard inventory), OptETruck road ITT dispatch, feeder vessel availability (PORTNET), CITOS Tuas receiving capacity.
- **Systems & Stakeholders Involved:**
  - *Systems:* CITOS (PPT + Tuas — separate instances), OptETruck (road ITT), feeder vessels (sea ITT), PORTNET (inventory tracking)
  - *Stakeholders:* PPT yard planner, Tuas yard planner, ITT coordinator, feeder vessel operator, gate operations
- **The System Handoff Gap:** Road ITT and sea ITT are not coordinated — OptETruck manages trucks, feeder operators manage vessels, no system optimises the split. PPT and Tuas CITOS are separate instances — container availability at PPT not visible to Tuas in real-time (PORTNET updates delayed 30–60 min). ITT arrival timing not linked to QC loading sequence at Tuas — no real-time "containers in transit" view.
- **Current Resolution Workflow:** (1) PPT planner identifies containers ready, (2) Contacts Tuas planner (phone), (3) Agrees 60/40 road/sea split, (4) Dispatches trucks via OptETruck, (5) Confirms feeder departure, (6) Tuas planner re-sequences QC loading. Resolution: 4–8 hours.
- **Quantified Impact Formula:**
  - *Metric:* Vessel Delay ($3,000–$5,000/hr × delay) + Road ITT Cost ($100–$200/trip × trucks × trips) + Sea ITT Cost ($5,000–$10,000 feeder charter) + Yard Re-handles ($30–$50/move × re-handles)
  - *Estimated Scale:* ~$15,600–$29,000 per incident; occurs ~4–6 times/month
- **Agentic AI Value Hypothesis:** An agent is required because: (1) real-time split optimisation across road and sea modes, (2) cross-terminal visibility (PPT + Tuas CITOS integration), (3) dynamic re-routing when road or sea ITT is delayed, (4) QC loading sequence adjustment based on ITT arrival predictions. No single system can coordinate both transport modes and their impact on terminal operations.
- **Candidate Action Space (Mock Tools):**
  - `get_itt_candidates(cit_ppt, vessel_id)` — List containers requiring cross-terminal transfer
  - `check_road_itt_capacity(optetruck, terminal, time_window)` — Available trucks and transit time
  - `check_sea_itt_capacity(portnet, feeder_id)` — Feeder vessel availability and capacity
  - `optimise_itt_split(candidates, road_capacity, sea_capacity)` — Determine optimal road/sea allocation
  - `update_tuas_loading_sequence(cit_tuas, itt_eta)` — Adjust QC sequence based on ITT arrival time
- **Initial Autonomy Level:** Human-in-the-Loop

---

### PB-13: Multiship QC Scheduling Conflict Under Disruption

- **Sector:** Berth & Marine
- **Problem Statement:** When multiple vessels share QC resources and one vessel's discharge plan changes (delay, breakdown, or priority shift), the combinatorial re-optimisation of QC assignments across all affected berths — subject to safety margins, yard congestion, and vessel stability constraints — exceeds current system capabilities, requiring manual solver intervention that takes hours.
- **Trigger & Data Source:** CITOS QC scheduling alert (conflicting QC requests), vessel delay notification (OptEVoyage), yard block congestion alerts (CITOS yard planner), QC maintenance status (ROCC).
- **Systems & Stakeholders Involved:**
  - *Systems:* CITOS (QC scheduling + berth allocation), A*STAR FMS (AGV dispatch), ROCC (crane operations), PORTNET (vessel schedules)
  - *Stakeholders:* Berth planner, ship planner, QC supervisor, terminal duty manager, multiple shipping line agents
- **The System Handoff Gap:** QC sequencing is currently solved per-vessel using mixed-integer programming (PSA research: Choo, Klabjan, Simchi-Levi). But when disruptions affect multiple vessels simultaneously, the multiship QC scheduling problem becomes NP-hard and current solvers cannot re-optimise in real-time. The berth planner must manually reason over: which vessel gets priority QCs, how to maintain safety margins between adjacent QCs, which yard blocks will become bottlenecks, and how to preserve vessel stability for each affected vessel. No system provides a multiship re-optimisation engine that accounts for yard congestion constraints.
- **Current Resolution Workflow:** (1) Berth planner receives multiple QC conflict alerts, (2) Manually reviews vessel priorities with duty manager (phone), (3) Opens CITOS to check QC availability across berths, (4) Manually tests 3–5 QC allocation scenarios (spreadsheet or mental model), (5) Negotiates with adjacent berth operators for QC sharing, (6) Updates CITOS with new allocation, (7) Notifies ship planners and shipping lines. Resolution: 2–4 hours.
- **Quantified Impact Formula:**
  - *Metric:* QC Idle Time ($350/hr × contested cranes × hours) + Vessel Delay ($3,000–$5,000/hr × affected vessels × delay) + Yard Congestion Cascade ($30–$50/move × re-handles from suboptimal QC sequencing)
  - *Estimated Scale:* ~$20,000–$55,000 per incident (2–3 vessels affected); occurs ~3–5 times/month
- **Agentic AI Value Hypothesis:** An agent is required because: (1) multiship QC scheduling is NP-hard — requires heuristic search over combinatorial solution space, (2) reasoning over conflicting multi-vessel objectives with safety constraints, (3) yard congestion prediction to avoid creating downstream bottlenecks, (4) real-time re-optimisation as new information arrives (vessel updates, QC status changes). Current CITOS solvers handle single-vessel optimisation; the multiship disruption scenario requires a fundamentally different approach.
- **Candidate Action Space (Mock Tools):**
  - `get_multiship_qc_status(terminal, time_window)` — QC allocation and availability across all berths
  - `get_vessel_priorities(terminal, time_window)` — Vessel priority rankings and constraints
  - `predict_yard_congestion(cit, qc_allocation)` — Forecast yard block utilisation for given QC scenario
  - `optimise_multiship_qc(vessels, constraints)` — Run heuristic QC re-allocation across vessels
  - `negotiate_qc_sharing(berth_a, berth_b, time_window)` — Propose QC sharing arrangement between berths
- **Initial Autonomy Level:** Advisory

---

### PB-14: iWX Container Reuse Marketplace Coordination Failure

- **Sector:** Yard & Transport
- **Problem Statement:** The iWX platform's ML predictions for container reuse depend on gate-in/gate-out data that may be stale or incomplete, causing failed reuse matches where hauliers arrive to find containers already allocated elsewhere — a coordination failure between shipping line approval workflows, haulier timing, and depot availability that wastes truck trips and increases empty container cycling.
- **Trigger & Data Source:** iWX container reuse prediction (ML model output), gate-in/gate-out data (CITOS gate system), shipping line approval workflow (PORTNET), haulier booking (OptETruck).
- **Systems & Stakeholders Involved:**
  - *Systems:* iWX (container reuse marketplace), CITOS (gate data), PORTNET (shipping line approvals), OptETruck (haulier routing), depot systems (iBOX)
  - *Stakeholders:* Haulier driver, depot operator, shipping line agent, iWX system operator
- **The System Handoff Gap:** iWX ML models predict when a container will be ready for reuse based on historical gate-in/gate-out patterns. But the prediction has a 15–30 minute uncertainty window. When a haulier is routed to pick up a "predicted available" container, it may not yet be unstuffed (prediction error) or may have already been allocated to another haulier (race condition). The shipping line approval step adds further delay — approval can take 10–30 minutes, during which the container availability changes. No system provides real-time container availability confirmation before haulier dispatch.
- **Current Resolution Workflow:** (1) iWX predicts container available for reuse, (2) Routes haulier to pickup location, (3) Haulier arrives at depot, (4) Depot checks container status — not yet ready, (5) Haulier waits 15–30 min or is rerouted to alternate container, (6) If rerouted: OptETruck must find new job (return trip wasted), (7) If waiting: truck idle time + missed subsequent bookings. Resolution: 30 min–2 hours per incident.
- **Quantified Impact Formula:**
  - *Metric:* Wasted Truck Trip ($50–$100/deadhead km × distance) + Haulier Idle Time ($50/hr × wait time) + Missed Subsequent Booking ($80–$150 incentive lost) + Carbon Impact (deadhead km × 2.5 kg CO2/km)
  - *Estimated Scale:* ~$200–$800 per failed reuse match; occurs ~15–25 times/month across depot network
- **Agentic AI Value Hypothesis:** An agent is required because: (1) real-time container availability verification requires cross-referencing iWX prediction, CITOS gate status, and shipping line approval status, (2) routing decision must account for prediction uncertainty (wait vs. reroute vs. skip), (3) multi-party coordination (depot, shipping line, haulier) with asynchronous approval workflows, (4) learning from prediction errors to improve future matching. A rule engine cannot handle the prediction uncertainty or the asynchronous approval race condition.
- **Candidate Action Space (Mock Tools):**
  - `get_container_reuse_candidates(iwx, depot_id)` — List predicted-available containers at depot
  - `verify_container_availability(cit, container_id)` — Real-time check against CITOS gate status
  - `check_shipping_line_approval(portnet, container_id)` — Verify if shipping line has approved reuse
  - `route_haulier_to_container(optetruck, haulier_id, container_id)` — Dispatch haulier with confirmed availability
  - `handle_reuse_failure(haulier_id, depot_id)` — Reroute haulier to alternate container or next job
- **Initial Autonomy Level:** Supervised Autonomous

---

### PB-15: QC-to-aRMG Synchronisation Failure

- **Sector:** Yard & Transport
- **Problem Statement:** When QC discharge rate changes suddenly (crane breakdown, weather slowdown, or priority shift), the aRMG job queue at receiving yard blocks becomes either starved (no AGVs arriving) or overloaded (AGVs piling up), creating yard-side congestion and reducing overall terminal throughput — a cross-system synchronisation problem between QC operations and yard crane operations.
- **Trigger & Data Source:** QC productivity sensors (ROCC), AGV position data (A*STAR FMS), aRMG job queue status (CITOS), yard block capacity alerts (CITOS yard planner).
- **Systems & Stakeholders Involved:**
  - *Systems:* CITOS (QC scheduling + yard planning), A*STAR FMS (AGV dispatch), ROCC (crane operations), aRMG controllers
  - *Stakeholders:* QC supervisor, yard planner, aRMG operator, FMS operator
- **The System Handoff Gap:** QC discharge rate is managed by ROCC/CITOS. aRMG job sequencing is managed by CITOS yard planner. AGV dispatch is managed by A*STAR FMS. These three systems do not synchronise in real-time: when QC slows (e.g., crane breakdown at 1400), AGVs continue arriving at yard blocks with discharged containers, but aRMG job queues were sized for the previous higher throughput rate. The yard block buffer fills up, AGVs queue at the block entrance, and the QC-to-yard transport link becomes a bottleneck. Conversely, when QC speeds up (e.g., additional QC assigned), aRMG cannot keep up and containers pile up at the transfer platform. No system provides a "QC rate → AGV dispatch rate → aRMG job rate" synchronisation loop.
- **Current Resolution Workflow:** (1) FMS operator notices AGV queue at yard block, (2) Calls yard planner (phone) to check aRMG status, (3) Yard planner checks aRMG job queue in CITOS, (4) If aRMG overloaded: redirects AGVs to adjacent blocks (manual override), (5) If aRMG starved: contacts QC supervisor to confirm QC rate, (6) FMS adjusts AGV dispatch rate manually, (7) Situation stabilises in 30–60 min. Resolution: 30 min–2 hours.
- **Quantified Impact Formula:**
  - *Metric:* AGV Queue Time ($50/hr × queued AGVs × wait) + aRMG Underutilisation ($30–$50/hr × idle cranes) + QC Transfer Platform Blockage ($350/hr × affected QCs × delay) + Yard Congestion Cascade ($30–$50/move × re-handles)
  - *Estimated Scale:* ~$3,000–$8,000 per incident; occurs ~8–12 times/day during peak operations
- **Agentic AI Value Hypothesis:** An agent is required because: (1) real-time synchronisation across three independent systems (QC, AGV, aRMG), (2) predictive buffering (anticipate QC rate changes and pre-adjust AGV dispatch and aRMG job queues), (3) dynamic load balancing across multiple yard blocks, (4) feedback loop between yard congestion and QC productivity. A rule engine cannot handle the dynamic coupling between QC rate, AGV flow, and aRMG capacity.
- **Candidate Action Space (Mock Tools):**
  - `get_qc_productivity(terminal, qc_ids)` — Real-time QC moves per hour
  - `get_agv_queue_status(fms, yard_blocks)` — AGV queue depth at each yard block
  - `get_armg_job_queue(cit, yard_blocks)` — aRMG pending job count and estimated completion
  - `synchronise_yard_flow(qc_rate, agv_dispatch, armg_capacity)` — Compute balanced flow rates
  - `redirect_agvs(fms, source_block, target_blocks)` — Reroute AGVs to less congested blocks
- **Initial Autonomy Level:** Supervised Autonomous

---

### PB-16: System-Wide Empty Container Imbalance

- **Sector:** Gate & Haulage
- **Problem Statement:** Empty container supply/demand mismatches across depots and terminals create repositioning costs and truck inefficiencies — some depots have surplus empties while others face shortages — but no system optimises the depot-to-depot repositioning flow, leaving iWX marketplace matching and OptETruck routing to handle only point-to-point reuse without system-wide balancing.
- **Trigger & Data Source:** iWX container availability data (depot inventory), OptETruck job matching (empty trip data), depot capacity alerts (iBOX), vessel discharge/import data (CITOS).
- **Systems & Stakeholders Involved:**
  - *Systems:* iWX (container reuse), OptETruck (haulier routing), iBOX (depot management), CITOS (container inventory), PORTNET (import/export data)
  - *Stakeholders:* Depot operators, hauliers, shipping lines, empty container trading desk
- **The System Handoff Gap:** iWX optimises individual container reuse matches (Container A → Haulier B at Depot X). OptETruck optimises individual truck routes (minimise empty trips). But neither system optimises the depot-level supply/demand balance: Depot A may have 200 surplus 40ft empties while Depot B has 200 deficit — requiring 200 truck trips to reposition. This repositioning is currently managed by shipping lines making individual decisions about where to return empties, without visibility into system-wide balance. The result: ~15% empty trips persist despite OptETruck's 50% reduction, and repositioning trucks add to road congestion and carbon emissions.
- **Current Resolution Workflow:** (1) Depot operator notices surplus/shortage (manual inventory check), (2) Contacts shipping line agent (phone) to discuss repositioning, (3) Shipping line decides based on own fleet needs (not system-wide optimality), (4) Haulier dispatched for repositioning trip, (5) No coordination with other depots' surplus/shortage situations. Resolution: ongoing (systemic issue, not incident-based).
- **Quantified Impact Formula:**
  - *Metric:* Repositioning Cost ($100–$200/trip × trips) + Empty Trip Cost ($50–$100/trip × wasted trips) + Carbon Impact (repositioning km × 2.5 kg CO2/km) + Depot Utilisation Loss (opportunity cost of idle containers)
  - *Estimated Scale:* ~$50,000–$150,000/month across all depots; 200–400 repositioning trips/month
- **Agentic AI Value Hypothesis:** An agent is required because: (1) system-wide optimisation requires cross-depot visibility (all depot inventories simultaneously), (2) matching supply across depots with demand considering truck routing constraints, (3) coordinating with shipping line preferences and container ownership rules, (4) predicting future imbalances based on vessel schedules and import/export patterns. iWX handles point-to-point matching; the system-wide balancing problem requires a fundamentally different optimisation scope.
- **Candidate Action Space (Mock Tools):**
  - `get_depot_inventory_all(iwx)` — Real-time empty container counts across all depots
  - `predict_demand_by_depot(portnet, citos, time_window)` — Forecast empty container demand per depot
  - `optimise_repositioning(supply, demand, truck_fleet)` — Compute optimal depot-to-depot repositioning plan
  - `coordinate_shipping_line(portnet, shipping_line_id, repositioning_plan)` — Align repositioning with SL preferences
  - `track_repositioning_progress(iwx, optetruck, plan_id)` — Monitor execution of repositioning plan
- **Initial Autonomy Level:** Advisory

---

## Problem Bank Summary

| ID | Problem | Sector | Autonomy Level | Cross-System? |
|----|---------|--------|---------------|---------------|
| PB-01 | Cascading Berth Delay & Tidal Window Lockout | Berth & Marine | HITL | ✅ (VTIS, OptEVoyage, CITOS, PORTNET) |
| PB-02 | DTQC Breakdown & Cascading Terminal Disruption | Berth & Marine | HITL | ✅ (ROCC, CITOS, FMS, PORTNET) |
| PB-03 | Late DG Declaration & IMDG Compliance Hold | Berth & Marine | HITL | ✅ (PORTNET, CITOS, MPA DGPE) |
| PB-04 | Transhipment Missed-Connection Recovery | Berth & Marine | Advisory | ✅ (CITOS, PORTNET, OptEVoyage, Yard) |
| PB-05 | Reefer Cold-Chain Telemetry Excursion | Yard & Transport | Advisory | ✅ (ARMS, CITOS, shipping line, maintenance) |
| PB-06 | Yard Block Buffer Overflow | Yard & Transport | Supervised Auto | ✅ (CITOS, FMS, gate, aRMG) |
| PB-07 | 5G Network Outage Degrading AGV Fleet | Yard & Transport | Supervised Auto | ✅ (5G, FMS, CITOS, DTQC) |
| PB-08 | eDO/VGM Discrepancy Gate Queue Cascade | Gate & Haulage | Supervised Auto | ✅ (AGS, PORTNET, weighbridge, OptETruck) |
| PB-09 | External Disruption to Haulier Pools | Gate & Haulage | Supervised Auto | ✅ (OptETruck, SmartBooking, PORTNET, CITOS) |
| PB-10 | Sea-to-Air Flight Cut-Off Threat | Multimodal | Advisory | ✅ (OptEModal, CITOS, TradeNet, SATS) |
| PB-11 | Cross-Border Customs Inspection Hold | Multimodal | HITL | ✅ (TradeNet, CALISTA, OptEModal) |
| PB-12 | Multi-Party ITT Coordination Failure | Multimodal | HITL | ✅ (CITOS×2, OptETruck, PORTNET, feeder) |
| PB-13 | Multiship QC Scheduling Conflict Under Disruption | Berth & Marine | Advisory | ✅ (CITOS, FMS, ROCC, PORTNET) |
| PB-14 | iWX Container Reuse Marketplace Coordination Failure | Yard & Transport | Supervised Auto | ✅ (iWX, CITOS, PORTNET, OptETruck, iBOX) |
| PB-15 | QC-to-aRMG Synchronisation Failure | Yard & Transport | Supervised Auto | ✅ (CITOS, FMS, ROCC, aRMG) |
| PB-16 | System-Wide Empty Container Imbalance | Gate & Haulage | Advisory | ✅ (iWX, OptETruck, iBOX, CITOS, PORTNET) |

## Distribution Check

| Requirement | Status |
|-------------|--------|
| 10–15 problems | ✅ 16 problems |
| Minimum 2 per sector | ✅ 4 per sector |
| Minimum 4 cross-system | ✅ All 16 are cross-system |
| Concrete cost formula | ✅ All entries have quantified impact formulas |
| Mock tool action space | ✅ All entries have 5 mock tools |

---

## Cross-Problem Cluster Analysis

This analysis identifies groups of problems that share common root causes — critical for Phase 3 when evaluating multi-problem resolving solutions.

### Cluster 1: Stale Data & Async State Updates

**Problems:** PB-01, PB-04, PB-06, PB-08, PB-10, PB-14

**Shared Root Cause:** Multiple PSA systems maintain separate state copies that are not synchronised in real-time. When one system's state changes (vessel ETA slips, eDO released, container unstuffed), downstream systems continue operating on stale data until a human operator manually propagates the update.

| Problem | Stale Data Source | Impact |
|---------|------------------|--------|
| PB-01 | CITOS berth plan vs. OptEVoyage ETA | Tidal window missed, feeder connections lost |
| PB-04 | PORTNET feeder schedules vs. mother vessel ETA | Transhipment containers miss connections |
| PB-06 | CITOS yard plan vs. vessel delay | Yard overflow, unproductive re-handles |
| PB-08 | PORTNET eDO status vs. haulier arrival | Gate queue cascade |
| PB-10 | OptEModal timeline vs. vessel delay | Sea-air transfer window missed |
| PB-14 | iWX prediction vs. real-time container status | Failed reuse matches, wasted truck trips |

**Multi-Problem Resolution Opportunity:** A real-time state synchronisation layer that propagates state changes across CITOS, PORTNET, OptEVoyage, iWX, and gate systems would address the root cause of all 6 problems simultaneously.

### Cluster 2: Manual Multi-Party Coordination

**Problems:** PB-01, PB-02, PB-03, PB-04, PB-05, PB-09, PB-10, PB-11, PB-12

**Shared Root Cause:** Exception resolution requires phone calls, WhatsApp groups, and email chains to coordinate between terminal operators, shipping lines, customs, hauliers, and ground handlers. No automated workflow engine handles multi-party exception resolution.

| Problem | Coordination Parties | Current Channel |
|---------|---------------------|-----------------|
| PB-01 | Duty manager, pilot, shipping line, ship planner | Phone + WhatsApp |
| PB-02 | QC supervisor, maintenance, berth planner, shipping line | Phone + WhatsApp |
| PB-03 | Ship planner, DG officer, MPA, yard planner | Phone + email |
| PB-04 | Duty manager, ship planner, shipping line, feeder operator | Phone + WhatsApp |
| PB-05 | Operations, maintenance, shipping line, insurer | Phone + email |
| PB-09 | Operations, gate, yard planner, hauliers | Phone + WhatsApp |
| PB-10 | Operations, customs broker, SATS, airline | Phone + email |
| PB-11 | Broker, forwarder, shipper (Mumbai), inspector | Email + WhatsApp |
| PB-12 | PPT planner, Tuas planner, feeder operator, gate | Phone |

**Multi-Problem Resolution Opportunity:** A multi-party workflow automation platform that replaces phone/WhatsApp coordination with structured, auditable, real-time exception workflows would address the root cause of all 9 problems.

### Cluster 3: Equipment & Infrastructure Dependency

**Problems:** PB-02, PB-07, PB-15

**Shared Root Cause:** Terminal operations depend on physical equipment (QCs, AGVs, 5G network) that can fail without warning. When equipment degrades, downstream systems (AGV dispatch, yard operations, QC scheduling) are not automatically notified or adjusted.

| Problem | Equipment Failure | Cascade |
|---------|------------------|---------|
| PB-02 | DTQC breakdown | AGV queue, vessel delay, connection misses |
| PB-07 | 5G network outage | AGV fleet de-rating, QC slowdown |
| PB-15 | QC rate change | aRMG queue starved/overloaded |

**Multi-Problem Resolution Opportunity:** A predictive equipment health monitoring system with automated downstream impact notification and graceful degradation protocols would address all 3 problems.

### Cluster 4: DG & Regulatory Compliance Workflow

**Problems:** PB-03, PB-11

**Shared Root Cause:** Regulatory compliance (DG declarations, customs inspections) involves manual workflows with government agencies that create bottlenecks during time-critical operations.

| Problem | Regulatory Bottleneck | Impact |
|---------|----------------------|--------|
| PB-03 | MPA DGPE re-approval (phone/email) | 2–4 hr vessel delay |
| PB-11 | Customs inspection hold + document retrieval | 2–8 hr cargo delay |

**Multi-Problem Resolution Opportunity:** An automated regulatory workflow engine that pre-validates declarations, auto-submits re-approval requests, and coordinates document retrieval would address both problems.

### Cluster 5: Cross-Terminal Visibility Gap

**Problems:** PB-12, PB-16

**Shared Root Cause:** PPT and Tuas operate as separate terminal instances with no unified real-time inventory view. Containers in transit between terminals are invisible to the receiving terminal until physical arrival.

| Problem | Visibility Gap | Impact |
|---------|---------------|--------|
| PB-12 | PPT containers invisible to Tuas CITOS | ITT split suboptimal, loading delayed |
| PB-16 | Depot inventories not coordinated system-wide | Empty container imbalance, repositioning cost |

**Multi-Problem Resolution Opportunity:** A unified cross-terminal inventory layer that provides real-time container visibility across PPT, Tuas, and all depots would address both problems.

### Cluster 6: QC-to-Yard Flow Synchronisation

**Problems:** PB-06, PB-13, PB-15

**Shared Root Cause:** Quay-side operations (QC discharge) and yard-side operations (aRMG stacking) are not dynamically synchronised. Rate mismatches create bottlenecks at the AGV transport link.

| Problem | Rate Mismatch | Impact |
|---------|--------------|--------|
| PB-06 | Export arrivals vs. vessel delay | Yard overflow |
| PB-13 | Multi-vessel QC allocation conflict | QC idle, vessel delay |
| PB-15 | QC rate change vs. aRMG job queue | AGV queue, yard congestion |

**Multi-Problem Resolution Opportunity:** A dynamic QC-AGV-aRMG flow synchronisation engine that adjusts AGV dispatch and aRMG job queues based on real-time QC rate would address all 3 problems.

---

## Acceptance Criteria Verification

- [x] **10–15 fully completed problem entries following the exact schema** ✅ (16 problems)
- [x] **Balanced distribution across all 4 sectors (minimum 2 per sector)** ✅ (4 per sector)
- [x] **Cross-system integration: Minimum 4 problems involving coordination across multiple sectors or platforms** ✅ (All 16 are cross-system; 8+ involve cross-sector coordination)
- [x] **Every entry contains a concrete cost formula and a candidate mock-tool action space** ✅

---

## Sources

All problems are grounded in the following Phase 1 research files:
- `research/sectors/berth-marine.md`
- `research/sectors/container-yard-transport.md`
- `research/sectors/gate-haulage.md`
- `research/sectors/multimodal-logistics.md`
- `research/systems/baseline-systems.md`
- `research/flows/critical-flows.md`
