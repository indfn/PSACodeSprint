## Purpose of this repo

Phase 1: Broad PSA Operations & Systems Mapping
  ↓
Phase 2: Disruption Mining (Identify Current Frictions within PSA areas) & Problem Bank Creation
  ↓
Phase 3: Problem Evaluation, Litmus Testing (Where to apply Agentic Solution) & Final Selection

---

## Phase Description

### Phase 1: Research PSA Singapore's Operations (COMPLETE)

**Goal:** Understand how PSA Singapore runs — what systems they use, what each sector does, and how information flows.

**What was produced:**

| File | What It Contains |
|------|-----------------|
| `research/sectors/berth-marine.md` | How vessels arrive, berth, load/unload, and depart |
| `research/sectors/container-yard-transport.md` | How containers move through the yard (AGVs, yard cranes, reefers) |
| `research/sectors/gate-haulage.md` | How trucks enter/exit, booking systems, customs |
| `research/sectors/multimodal-logistics.md` | Sea-air transfers, warehousing, end-to-end visibility |
| `research/systems/baseline-systems.md` | All 7 PSA digital systems (CITOS, PORTNET, OptETruck, etc.) |
| `research/flows/critical-flows.md` | Physical, information, and decision flows for all 4 sectors |

**How it was verified:** Every claim is cited with a source URL. Sources follow a priority order: PSA official first, then Singapore government (MPA, Customs), then industry/academic, then news. Each section is marked with verification status (verified, single-source, or needs verification).

---

### Phase 2: Mine Disruptions & Build Problem Bank (COMPLETE)

**Goal:** Find the operational failure points — where current software and manual processes break down — and turn them into structured problem candidates.

**What was produced:**

| File | What It Contains |
|------|-----------------|
| `problems/02-01-disruption-scenarios.md` | 16 disruption scenarios across all 4 sectors |
| `problems/02-02-failure-modes.md` | Why each scenario is hard to solve — the system gaps, manual workarounds, and costs |
| `problems/02-03-problem-bank.md` | 16 structured problem charters ready for scoring |

**How it was verified:** Every problem references specific Phase 1 research files with line numbers (e.g., `berth-marine.md:135-142`). No web searches were done in this phase — all problems are grounded in the research from Phase 1. Each problem includes a quantified cost formula based on standard Singapore port economics.

**Key finding:** We identified 6 root-cause clusters — groups of problems that share the same underlying issue. The biggest cluster is **Manual Multi-Party Coordination** (9 of 16 problems involve phone calls and WhatsApp to resolve exceptions). This means a single well-designed agent could potentially address multiple problems at once.

---

### Phase 3: Evaluate & Select One Problem (NOT STARTED)

**Goal:** Score all 16 problems against the competition's 5 Agentic AI criteria, pick the best cluster, select one flagship problem, and lock a Master Problem Charter.

**What it will produce:**

| File | What It Contains |
|------|-----------------|
| `problems/03-01-litmus-test-scores.md` | Scores for all 16 problems + cluster rankings |
| `problems/03-02-autonomy-level.md` | Risk assessment and human-in-the-loop guardrails |
| `problems/03-03-master-charter.md` | The final charter — persona, systems, API specs, ROI model, demo storyboard |

---

## How the Phases Connect

```
Phase 1 (Research)          Phase 2 (Problem Mining)       Phase 3 (Evaluation)
─────────────────          ────────────────────────       ─────────────────────
Map 4 sectors              Identify 16 disruptions        Score all 16 problems
Map 7 systems              Analyze failure modes          Pick best cluster
Map 3 flow types           Build problem bank             Lock one Master Problem (for demo) +
                                                          also solve some cluster problems
```

---

## Project Structure

```
PSACodeSprint/
├── research/                    # Phase 1 output
│   ├── sectors/                 # 4 operational sector profiles
│   ├── systems/                 # 7 baseline digital system profiles
│   └── flows/                   # Physical, Information, Decision flows
├── problems/                    # Phase 2 + Phase 3 output
│   ├── 02-01-disruption-scenarios.md
│   ├── 02-02-failure-modes.md
│   ├── 02-03-problem-bank.md
│   ├── 03-01-litmus-test-scores.md      (Phase 3)
│   ├── 03-02-autonomy-level.md          (Phase 3)
│   └── 03-03-master-charter.md          (Phase 3)
└── .planning/                   # Internal project management
    ├── PROJECT.md               # Scope, constraints, decisions
    ├── STATE.md                 # Current progress
    ├── ROADMAP.md               # Phase plan
    └── phases/                  # Detailed plans per phase
```

---

## Verification Methodology

This project uses a grounded research approach — no claims are made without sources.

**Phase 1 (Research):**
- Multi-source cross-verification (2–3 independent queries per sub-topic)
- Source priority: PSA official → Singapore govt → Industry/academic → News
- Every section tagged with verification status

**Phase 2 (Problem Mining):**
- No open-ended web searches — all problems grounded in Phase 1 research
- Every problem includes `[filename.md:lineX-lineY]` references to source material
- Cost formulas based on published Singapore port economics

**Phase 3 (Evaluation):**
- 5-point binary litmus test (pass/fail per criterion)
- Cluster-weighted scoring matrix (4 dimensions, weighted)
- Dual-layer ROI: single problem impact + cluster generalisation impact

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Operational sectors mapped | 4 |
| Digital systems documented | 7 |
| Disruption scenarios identified | 16 |
| Problem charters created | 16 |
| Root-cause clusters found | 6 |
| Total research sources cited | 100+ |
| Estimated incidents per month (all problems) | 50–80 |
| Estimated monthly cost of all problems | $500K–$1.5M |

---

## What Happens Next

Phase 3 scores all 16 problems, picks the winning cluster, selects one flagship problem, and produces a Master Problem Charter. After that, the team moves to Phases 4–6 (architecture, agent development, submission) — which are outside this workspace's scope.
