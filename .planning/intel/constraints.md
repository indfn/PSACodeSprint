# Constraints Intel

Synthesized from: `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md`
Classification: `codesprint-md.json` — type PRD, confidence high, locked: false
PRECEDENCE of this source: PRD (default ordering ADR > SPEC > PRD > DOC)

Constraint types used: api-contract | schema | nfr | protocol. All entries below are nfr (non-functional / scope / gate constraints). Text is copied verbatim from the source (or, where noted, from the project-owner binding instructions); lightweight structure added around verbatim blocks.

---

## C-01 — Roadmap Scope: Phases 1–3 only (nfr)
- Title: This .planning/ roadmap covers Phase 1–3 of the CodeSprint workflow
- Source: Project-owner binding instruction (task brief); phase definitions verbatim from CodeSprint.md (§2. Overarching Workflow)
- Type: nfr (scope)
- Content (project-owner instruction, binding):

> This repository is scoped to IN-DEPTH DEEP RESEARCH and PROBLEM EVALUATION — specifically CodeSprint.md Phases 1, 2, and 3. The phases map:
> - Phase 1: Broad PSA Singapore Operations & Systems Mapping [scope: PSA → PSA Singapore]
> - Phase 2: Disruption Mining & Problem Bank Creation
> - Phase 3: Problem Evaluation, Litmus Testing & Final Selection

- Impact: ROADMAP.md produced downstream must contain only Phase 1–3 workstreams. Requirements REQ-p1-* / REQ-p2-* / REQ-p3-* (see requirements.md §D) are the phase payloads.

## C-02 — Out of Scope: Phases 4–6 (nfr)
- Title: Phases 4–6 are OUT OF SCOPE for this directory's roadmap (projection stage only)
- Source: Project-owner binding instruction (task brief); phase names verbatim from CodeSprint.md (§2. Overarching Workflow)
- Type: nfr (scope)
- Content (project-owner instruction, binding):

> Later phases (4–6: architecture, agent development, submission assets) are OUT OF SCOPE for the .planning/ roadmap of THIS directory — but the team still needs to know scope exists (capture as out-of-scope, be at projection stage only).

- Phase names preserved verbatim from the source workflow for projection awareness:

> Phase 4: Architecture Design & Synthetic Environment Setup
> Phase 5: Agent Development, Tool Integration & Failure Testing
> Phase 6: Submission Asset Creation (Demo Video & Pitch Deck)

- Impact: Downstream roadmap may reference phases 4–6 as future/projection context only; no planning work may be scheduled on them in this directory.

## C-03 — Submission Deadline: 4 September 2026 (nfr)
- Title: Hard submission deadline
- Source: CodeSprint.md (§2. Key Deliverables & Format)
- Type: nfr (schedule gate)
- Content (verbatim):

> * **Submission Deadline:** 4 September 2026.

- Impact: All Phase 1–3 research and evaluation work must complete with margin before 2026-09-04 so downstream (out-of-scope) phases can still be executed by the team outside this roadmap.

## C-04 — The "Autonomy Trap" Warning (nfr)
- Title: Higher autonomy is not automatically better — autonomy level must be use-case- and risk-calibrated
- Source: CodeSprint.md (§1. The Core Objective & Theme)
- Type: nfr (design governance)
- Content (verbatim):

> * **The "Autonomy Trap" warning:** *"Higher autonomy is not automatically better. Teams should select an appropriate level based on use case, operational risk, and available controls."* (Advisory vs. Human-in-the-Loop vs. Autonomous).

- Impact: Any autonomy-level decision (see decisions.md D-2) must be justified against use case, operational risk, and available controls — never "max autonomy by default."

## C-05 — Evaluation Criteria as Gates (nfr)
- Title: The four competition evaluation criteria act as acceptance gates for problem selection and solution framing
- Source: CodeSprint.md (§2. Key Deliverables & Format)
- Type: nfr (gate)
- Content (verbatim):

> * **Evaluation Criteria:**
>   1. *Agentic AI Design & Technical Execution* (ReAct/Plan-and-Solve mechanics, tool orchestration, state management, trace logging).
>   2. *Innovation & Originality* (Tackling non-trivial port/logistics challenges beyond simple chatbots).
>   3. *Scalability & Responsible AI* (Risk-calibrated human-in-the-loop, latency, security, safety guardrails).
>   4. *Presentation & Clarity* (System architecture rigor, clear ROI/throughput impact math).

- Gate semantics [derived]: A candidate problem fails Phase 3 selection if it cannot pass criterion 2 (non-trivial) and criterion 3 (responsible AI); the selected problem's charter must be framed to support criterion 1 and criterion 4. Full criteria also captured as requirements REQ-eval-* (dual-listing is intentional — see INGEST-CONFLICTS.md INFO entries).
- Impact: Roadmapper must thread these gates into Phase 3 exit criteria (REQ-p3-litmus-test / REQ-p3-master-charter).

---

## Constraint index (5, all nfr)

- C-01 roadmap-scope-phases-1-3 (nfr, scope)
- C-02 out-of-scope-phases-4-6 (nfr, scope)
- C-03 submission-deadline-2026-09-04 (nfr, schedule gate)
- C-04 autonomy-trap-warning (nfr, design governance)
- C-05 evaluation-criteria-gates (nfr, gate)