## What This Repo Is

This is a research-only workspace for the **PSA Code Sprint: Agentic AI in Action** competition. It covers Phases 1–3 of a structured research pipeline — from understanding port operations, through finding problems, to selecting one problem for the team to build an AI agent around.

**Deadline:** 4 Sep 2026

---

## Pipeline at a Glance

```
Phase 1: Understand how PSA Singapore runs          (COMPLETE)
    ↓
Phase 2: Find what breaks and build a problem bank  (COMPLETE)
    ↓
Phase 3: Score, rank, and lock one Master Problem   (COMPLETE)
    ↓
Phase 4+: Build the agent                           (next team action — out of scope)
```

---

## Phase 1 — Understand PSA Singapore's Operations

**Goal:** Learn how PSA Singapore runs — what systems they use, what each sector does, and how information flows between them.

| File | What It Contains |
|------|-----------------|
| `research/sectors/berth-marine.md` | How vessels arrive, berth, load/unload, and depart |
| `research/sectors/container-yard-transport.md` | How containers move through the yard (AGVs, yard cranes, reefers) |
| `research/sectors/gate-haulage.md` | How trucks enter/exit, booking systems, customs |
| `research/sectors/multimodal-logistics.md` | Sea-air transfers, warehousing, end-to-end visibility |
| `research/systems/baseline-systems.md` | All 7 PSA digital systems (CITOS, PORTNET, OptETruck, etc.) |
| `research/flows/critical-flows.md` | Physical, information, and decision flows for all 4 sectors |

Every claim is cited. Sources follow a priority: PSA official → Singapore government → industry/academic → news.

---

## Phase 2 — Mine Disruptions and Build Problem Bank

**Goal:** Find the operational failure points — where current software and manual processes break down — and turn them into structured problem candidates.

| File | What It Contains |
|------|-----------------|
| `problems/02-01-disruption-scenarios.md` | 16 disruption scenarios across all 4 sectors |
| `problems/02-02-failure-modes.md` | Why each scenario is hard to solve — the system gaps, manual workarounds, and costs |
| `problems/02-03-problem-bank.md` | 16 structured problem charters ready for scoring |

Every problem references specific Phase 1 files with line numbers (e.g., `berth-marine.md:135-142`). No web searches were done in this phase — all problems are grounded in Phase 1 research.

**Key finding:** 6 root-cause clusters were identified. The biggest is **Manual Multi-Party Coordination** — 9 of 16 problems involve phone calls and WhatsApp to resolve exceptions. A single well-designed agent could address multiple problems at once.

---

## Phase 3 — Score, Rank, and Select a Master Problem

**Goal:** Filter all 16 problems against the competition's Agentic AI criteria, pick the best cluster, select one flagship problem, and lock a Master Problem Charter. Phase 03-02 and 03-03 can be rerun if the team chooses a different main problem.

### What the three files do

**`problem-selection/03-01-litmus-test-scores.md`** — The first filter. Each of the 16 problems is scored against 5 yes/no questions (a "litmus test"). A problem must pass all 5 to stay in the running. This eliminates problems that are too narrow, too deterministic, or too small in impact.

**`problem-selection/03-02-autonomy-level.md`** — Decides how much human oversight the agent needs. High-risk decisions (money, safety, multi-party commitments) get a mandatory human-in-the-loop gate. Low-risk read-only tasks get full automation.

**`buildplan/03-03-master-charter.md`** — The final locked document. Describes the one problem the team will build around: what the agent does, which systems it touches, what data it sees, what decisions it makes, what it cannot do without a human, and how much money it saves.

### How the litmus test works (5 filters)

| Filter | What It Asks | Why It Matters |
|--------|-------------|----------------|
| L1: Is this an agentic problem? | Does it need multi-step reasoning, multiple tools, and adaptive re-planning? | If a simple if/else or lookup solves it, an agent is overkill |
| L2: Is this a multi-system problem? | Does it span 3+ PSA software systems? | Agents prove their value when they bridge disconnected systems |
| L3: Does it have real cost? | Does the current failure cost PSA money every month? | No real cost = no real impact |
| L4: Does it need human judgment? | Are there decisions too risky or ambiguous to fully automate? | This is where agents earn trust — by knowing when to ask |
| L5: Is it macro-impactable? | Does fixing it move a number PSA's leadership would care about? | A micro-optimisation is not worth an agent |

### How problems are ranked (cluster scoring)

After the litmus test, the surviving problems are grouped into clusters by shared root cause (e.g., all "manual phone call coordination" problems go together). Each cluster is then scored on 4 dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Agentic sweet spot | 35% | How well the problem fits multi-tool, adaptive agent capabilities |
| Business impact | 30% | How much money the cluster saves PSA annually |
| Coverage breadth | 20% | How many sibling problems the same agent can also solve |
| Demo compellingness | 15% | How easy it is to show a working demo that impresses judges |

**Winner: Cluster C2 — Manual Multi-Party Coordination** (score 4.80/5.00, 7 passing problems, ~$316K/month aggregate).

### What "Master Problem Charter" means

The Master Problem Charter is the one document a builder reads to understand what they are building and why. It contains:

- **As-Is state:** What happens today (manual, fragmented, costly)
- **To-Be state:** What the agent does (concrete tool calls, data flows, decision points)
- **Mock API specs:** The exact data structures the agent will read and write
- **Human-in-the-loop gates:** Exactly which decisions require human approval before the agent acts
- **ROI model:** How much money the agent saves, with formulas grounded in real port economics
- **Demo trace:** A step-by-step walkthrough of a single incident from trigger to resolution

The charter covers **one flagship problem** but is designed so that the same agent architecture can be extended to solve sibling problems in the same cluster.

### Flagship problem selected

**PB-12: Multi-Party ITT Coordination Failure**

A vessel at Tuas Port needs 120 containers moved from Pasir Panjang Terminal (PPT) to Tuas before departure. Today, the ITT coordinator manually calls hauliers, WhatsApps the feeder operator, checks road conditions on Google Maps, and hopes everything lines up. When it does not — a berth conflict, a truck shortage, a traffic jam — the vessel demurs at $2,500/hour.

The agent acts as a **coordination layer** between 5 disconnected systems (CITOS at both terminals, OptETruck for trucks, feeder operator system, and PORTNET). It reads data from all 5, proposes a road/sea split, and asks a human to approve before committing anything. If conditions change mid-operation, it re-computes and asks again.

**Annual ROI:** $384K–$576K for the flagship problem alone; $1.26M–$2.08M across all 7 sibling problems in the cluster.

---

## How Phases Connect

```
Phase 1 (Research)           Phase 2 (Problem Mining)        Phase 3 (Evaluation)
───────────────              ───────────────────────         ─────────────────────
Map 4 sectors                Identify 16 disruptions         Litmus test: 12 pass, 4 fail
Map 7 systems                Analyze failure modes           Cluster scoring: C2 wins
Map 3 flow types             Build problem bank              Flagship: PB-12 selected
                                                              Master Charter locked
```

---

## Project Structure

```
PSACodeSprint/
├── research/                              # Phase 1 output
│   ├── sectors/                           # 4 operational sector profiles
│   │   ├── berth-marine.md
│   │   ├── container-yard-transport.md
│   │   ├── gate-haulage.md
│   │   └── multimodal-logistics.md
│   ├── systems/
│   │   └── baseline-systems.md            # 7 PSA digital systems
│   └── flows/
│       └── critical-flows.md              # Physical, info, decision flows
├── problems/                              # Phase 2 + Phase 3 output
│   ├── 02-01-disruption-scenarios.md      # 16 disruption scenarios
│   ├── 02-02-failure-modes.md             # 16 failure mode analyses
│   ├── 02-03-problem-bank.md             # 16 structured problem charters
├── problem-selection/                     # Phase 3 output
│   ├── 03-01-litmus-test-scores.md       # Litmus test + cluster rankings
│   └── 03-02-autonomy-level.md           # HITL guardrails + risk profile
├── buildplan/                             # Build planning
│   ├── tech-stack.md                     # Tech stack decision report
│   └── 03-03-master-charter.md           # Final locked Master Problem Charter
├── prototype/                             # Implementation
│   ├── main.py                           # FastAPI entry point
│   ├── configs/                          # Problem configs (YAML)
│   │   ├── pb-12-itt.yaml               # PB-12: ITT coordination
│   │   ├── pb-01-berth.yaml             # PB-01: Berth delay
│   │   └── ...                           # 7 problem configs total
│   ├── shared/utils/
│   │   └── provider.py                   # LLM provider abstraction
│   └── pre_approval/
│       ├── ai_optimisation/
│       │   └── compute_itt_split.py      # Tool 4: optimisation engine
│       └── road_itt/
│           └── optetruck_tools.py        # Tool 2: road ITT capacity
└── .planning/                             # Internal project management (ignore)
```

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Operational sectors mapped | 4 |
| Digital systems documented | 7 |
| Disruption scenarios identified | 16 |
| Problem charters created | 16 |
| Litmus test passes | 12 of 16 |
| Root-cause clusters found | 6 |
| Winning cluster | C2 — Manual Multi-Party Coordination (4.80/5.00) |
| Flagship problem | PB-12 — Multi-Party ITT Coordination Failure |
| Flagship annual ROI | $384K–$576K |
| Cluster annual ROI (all 7 problems) | $1.26M–$2.08M |
| Total research sources cited | 100+ |

---

## What Happens Next

Phases 1–3 are complete. The Master Problem Charter (`buildplan/03-03-master-charter.md`) is the handoff document to the build team. The next step is Phase 4: Architecture and Agent Development — which is outside this workspace's scope.
