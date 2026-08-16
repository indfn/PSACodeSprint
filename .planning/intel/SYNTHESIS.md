# Synthesis Summary

Entry point for `gsd-roadmapper` and downstream consumers. Produced by `gsd-doc-synthesizer` from classified docs in `.planning/intel/classifications/`.

Generated: 2026-08-17 (MODE: new; PRECEDENCE: ADR > SPEC > PRD > DOC)

## Docs consumed

- 1 doc synthesized: 1 × PRD
  - `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (classification `codesprint-md.json`, type PRD, confidence high, locked: false)
- Sources with precedence override: none
- UNKNOWN low-confidence docs: 0
- Cross-ref cycles: 0 (no cross_refs exist; cycle detection clean)

## Scope note (project-owner binding)

This directory's .planning/ roadmap covers IN-DEPTH DEEP RESEARCH and PROBLEM EVALUATION only — CodeSprint.md Phases 1, 2, and 3. Phases 4–6 (architecture, agent development, submission assets) are OUT OF SCOPE, captured at projection stage only (constraints.md C-02). Do NOT schedule Phase 4–6 work in ROADMAP.md.

## Decisions (decisions.md)

- Locked decisions: 0 (no ADRs in ingest set)
- Proposed decisions: 2
  - D-1 (proposed): Roadmap scope Phases 1–3 only — source: project-owner binding instruction
  - D-2 (proposed): Target autonomy level = HITL Exception Solver (Recommended) — source: CodeSprint.md §3.2; pending team confirmation at Phase 3

## Requirements (requirements.md)

- Total: 27 (REQ-ids below)
- Competition-level: REQ-agentic-solution, REQ-input-handling, REQ-deliverable-deck, REQ-deliverable-video, REQ-deadline-submission
- Six agentic capabilities: REQ-cap-event-ingestion, REQ-cap-reasoning-planning, REQ-cap-tool-orchestration, REQ-cap-execution-trace, REQ-cap-hitl-controls, REQ-cap-error-recovery
- Evaluation criteria: REQ-eval-design-execution, REQ-eval-innovation-originality, REQ-eval-scalability-responsible, REQ-eval-presentation-clarity
- Phase 1: REQ-p1-mapping, REQ-p1-sectors, REQ-p1-baseline-systems, REQ-p1-critical-flows
- Phase 2: REQ-p2-disruption-mining, REQ-p2-change-scenarios, REQ-p2-failure-modes, REQ-p2-problem-bank
- Phase 3: REQ-p3-evaluation, REQ-p3-litmus-test, REQ-p3-autonomy-level, REQ-p3-master-charter

## Constraints (constraints.md)

- Total: 5, all type nfr
  - C-01 roadmap-scope-phases-1-3 (scope)
  - C-02 out-of-scope-phases-4-6 (scope)
  - C-03 submission-deadline-2026-09-04 (schedule gate — 4 September 2026)
  - C-04 autonomy-trap-warning (design governance)
  - C-05 evaluation-criteria-gates (gate)

## Context (context.md)

- Total: 4 topics (all verbatim from source)
  - Topic 1: Competition Overview
  - Topic 2: The 4 Operational Sectors (Berth & Marine; Container Yard & Internal Transport; Gate & External Haulage; Multimodal Logistics & Supply Chain Adjacencies)
  - Topic 3: The 7 Baseline Digital Systems (CITOS, PORTNET, OptETruck, SmartBooking & iBOX, OptEModal, CALISTA & CALISTA P!NG, PSA BDP Enterprise Solutions)
  - Topic 4: The Three Critical Flows (Physical / Information / Decision)

## Conflicts

- Blockers: 0
- Competing-variants: 0
- Auto-resolved: 0
- Detail: `/home/ahnaf/Documents/Projects/PSACodeSprint/.planning/INGEST-CONFLICTS.md` (INFO-only; no gates tripped)

## Intel files

- Requirements: `.planning/intel/requirements.md`
- Constraints: `.planning/intel/constraints.md`
- Context: `.planning/intel/context.md`
- Decisions: `.planning/intel/decisions.md`
- Conflicts report: `.planning/INGEST-CONFLICTS.md`

Verbatim-fidelity note: per project-owner instruction, source text is copy-pasted, not paraphrased. All intel entries carry `source:` attribution for provenance.