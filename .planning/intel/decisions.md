# Decisions Intel

Status: NO ADRs in the ingest set. The source document (`/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md`) is a PRD and contains no formal ADR decision records. However, the source DOES state framing choices (selection preferences / recommended stances). Per synthesis rules these are recorded below as PROPOSED decisions — they are NOT locked, and must be confirmed by the team (e.g., via discussion at the relevant phase or a future ADR) before being treated as binding.

Default PRECEDENCE applies (ADR > SPEC > PRD > DOC) — these proposed decisions carry PRD-level authority only until confirmed.

---

## D-1 — Roadmap Scope: Phases 1–3 only; Phases 4–6 out of scope
- Title: Scope decision for this .planning/ roadmap
- Source: Project-owner binding instruction (task brief) — NOT from CodeSprint.md (the source workflow documents 6 phases; the scope restriction is imposed by the project owner for THIS directory)
- Status: **proposed** (owner-stated as binding; recommend formalizing as a confirmed framing decision for this .planning/ context)
- Decision statement: This repository's .planning/ roadmap is scoped to in-depth deep research and problem evaluation — CodeSprint.md Phases 1 (Broad PSA Singapore Operations & Systems Mapping), 2 (Disruption Mining & Problem Bank Creation), and 3 (Problem Evaluation, Litmus Testing & Final Selection). Phases 4–6 (architecture, agent development, submission assets) are OUT OF SCOPE; they exist at projection stage only.
- Scope: Directory-level .planning/ roadmap boundary

## D-2 — Target Autonomy Level: HITL Exception Solver (Recommended)
- Title: Autonomy level recommendation for the agentic solution
- Source: `/home/ahnaf/Documents/Projects/PSACodeSprint/CodeSprint.md` (§3, Phase 3, 3.2)
- Status: **proposed** (source marks this autonomy level as "Recommended"; not yet confirmed by the team; must be confirmed during Phase 3 execution — see REQ-p3-autonomy-level)
- Decision statement (verbatim):

> * **3.2. Define the Target Autonomy Level:**
>   * Categorize the solution into one of three levels:
>     * *Advisory (Copilot):* High physical risk; agent suggests plans, human manually triggers actions.
>     * *Human-in-the-Loop (HITL) Exception Solver (Recommended):* Medium risk; agent autonomously gathers data, runs recovery simulations, drafts API updates, and waits for a 1-click human confirmation before executing.
>     * *Supervised Autonomous:* Low risk; agent executes actions directly and notifies the human, escalating only when an error occurs.

- Decision statement (condensed): Target autonomy level = Human-in-the-Loop (HITL) Exception Solver — agent autonomously gathers data, runs recovery simulations, drafts API updates, and waits for 1-click human confirmation before executing.
- Binding constraint on this choice: the "Autonomy Trap" warning (constraints.md C-04) — "Higher autonomy is not automatically better. Teams should select an appropriate level based on use case, operational risk, and available controls."
- Scope: Agent autonomy design (Phase 3.2 → Phase 4 architecture)

---

## Decision index (2, both proposed — none locked)

- D-1 (proposed): Roadmap scope Phases 1–3 only (owner instruction; confirm as framing decision)
- D-2 (proposed): Autonomy level = HITL Exception Solver (Recommended) (source recommendation; confirm during Phase 3)