# PSA Code Sprint — Agentic AI in Action

## What This Is

Deep research and problem evaluation workspace for the **PSA Code Sprint: Agentic AI in Action** competition. Scoped exclusively to Phases 1–3 of the competition workflow: (1) mapping PSA Singapore's operations and digital infrastructure, (2) mining disruptions and creating a problem bank, and (3) evaluating and selecting the single best problem for an Agentic AI solution.

## Core Value

Identify the single highest-impact, non-trivial problem within PSA Singapore's operational ecosystem that satisfies all five Agentic AI litmus-test criteria and produces quantified ROI — before the team commits to building anything.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Map all 4 operational sectors (Berth & Marine; Container Yard & Internal Transport; Gate & External Haulage; Multimodal Logistics)
- [ ] Map all 7 baseline digital systems (CITOS, PORTNET, OptETruck, SmartBooking & iBOX, OptEModal, CALISTA, PSA BDP)
- [ ] Map Physical, Information, and Decision flows for each sector
- [ ] Identify 10–15 candidate problems across all 4 sectors (Problem Bank)
- [ ] Document each problem's Trigger Event, Current Workaround, and Business Consequence
- [ ] Apply 5-Point Agentic AI Litmus Test to every candidate problem
- [ ] Select and charter one Master Problem with persona, autonomy level, and impact equation

### Out of Scope

- **Phases 4–6 (architecture, agent dev, submission assets)** — captured at projection stage only; this directory's roadmap does not schedule them
- **Technical implementation decisions** — deferred to the team's build workspace
- **Demo video and pitch deck creation** — Phase 6 work; not scheduled here

## Context

- **Competition:** PSA Code Sprint: Agentic AI in Action
- **Domain:** PSA Singapore port and supply chain operations
- **Deadline:** 4 September 2026 (hard submission gate)
- **4 Operational Sectors:** Berth & Marine; Container Yard & Internal Transport; Gate & External Haulage; Multimodal Logistics & Supply Chain Adjacencies
- **7 Baseline Systems:** CITOS, PORTNET, OptETruck, SmartBooking & iBOX, OptEModal, CALISTA & CALISTA P!NG, PSA BDP Enterprise Solutions
- **6 Mandatory Agent Capabilities:** Event Ingestion & Perception; Reasoning & Dynamic Planning; Tool & System Orchestration; State Tracking & Observable Execution Trace; Human-in-the-Loop Controls; Uncertainty & Error Recovery
- **4 Evaluation Pillars:** Agentic AI Design & Technical Execution; Innovation & Originality; Scalability & Responsible AI; Presentation & Clarity

## Constraints

- **Scope:** This roadmap covers only Phases 1–3 — Phases 4–6 are out of scope (projection stage only)
- **Schedule:** Submission deadline 2026-09-04; all Phase 1–3 work must finish with margin before this date
- **Autonomy Trap:** Higher autonomy is not automatically better; autonomy level must be use-case and risk calibrated
- **Evaluation Gates:** The four competition evaluation criteria act as acceptance gates for problem selection and solution framing
- **Non-Trivial Requirement:** Selected problem must pass Innovation & Originality criterion (not a simple chatbot or rule engine)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Scope: Phases 1–3 only | Project-owner binding instruction — deep research & problem evaluation directory | ✅ Complete |
| Autonomy level: HITL Exception Solver | HIGH financial risk ($15K–$29K/incident) + multi-party authority boundaries + cross-terminal data asymmetry | ✅ Confirmed (Phase 3) |
| Flagship problem: PB-12 ITT Coordination | 5 PSA systems, systemic CITOS disintegration gap, highest cluster leverage (7 sibling problems) | ✅ Locked (Phase 3) |
| Winning cluster: C2 Manual Multi-Party | Score 4.80/5.00 — highest agentic sweet spot, broadest coverage, most compelling demo | ✅ Selected (Phase 3) |

---

*Last updated: 2026-08-17 after initialization*
