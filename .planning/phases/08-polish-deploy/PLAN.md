# Phase 8: Polish & Deploy — PSA Nexus Launch

## Goal
Dockerise, deploy PSA Nexus to free tier, and prepare submission assets that showcase it as a generalizable platform.

## Depends on
Phase 7

## Requirements
D-01 through D-08

## Success Criteria
1. Docker image builds and runs on Railway/Render free tier
2. 10-minute demo video recorded showing normal + edge-case flows
3. 10-slide presentation deck covers problem, architecture, decision logic, guardrails, ROI
4. All submission assets uploaded before 2026-09-04

## Plan

### 8.1: Dockerfile
**Duration:** ~1 hour
**What:** Create Dockerfile.

**Steps:**
1. Create `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim AS builder
   
   WORKDIR /app
   
   # Install dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy application
   COPY app/ ./app/
   
   # Expose port
   EXPOSE 8000
   
   # Run
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
2. Create `.dockerignore`:
   ```
   .planning/
   prototype/
   .git/
   __pycache__/
   *.pyc
   .env
   ```
3. Create `requirements.txt` (pinned versions per charter Section 9):
   ```
   fastapi==0.115.12
   uvicorn==0.34.0
   langgraph==1.2.11
   langchain-core==0.3.60
   anthropic==0.40.0
   openai==1.50.0
   pydantic==2.11.0
   pyyaml==6.0.2
   httpx==0.27.2
   langsmith==0.1.147
   ```

**Verification:**
```bash
docker build -t psa-agent .
docker run -p 8000:8000 psa-agent
curl localhost:8000/health  # returns OK
```

### 8.2: docker-compose.yml
**Duration:** ~30 min
**What:** Create docker-compose for local development.

**Steps:**
1. Create `docker-compose.yml`:
   ```yaml
   services:
     agent:
       build: .
       ports:
         - "8000:8000"
       environment:
         - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
         - OPENAI_API_KEY=${OPENAI_API_KEY}
         - LLM_PROVIDER=${LLM_PROVIDER:-anthropic}
         - LLM_MODEL=${LLM_MODEL:-claude-sonnet-4-20250514}
       volumes:
         - ./app/configs:/app/app/configs
   ```

**Verification:**
```bash
docker compose up
curl localhost:8000/health
```

### 8.3: Deploy to Free Tier
**Duration:** ~2 hours
**What:** Deploy to Railway or Render.

**Steps:**
1. Choose platform (Railway recommended for simplicity):
   - Railway: `railway login` → `railway init` → `railway up`
   - Render: connect GitHub repo, auto-deploy
2. Configure environment variables:
   - `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
   - `LLM_PROVIDER` and `LLM_MODEL`
   - `LANGSMITH_API_KEY` (optional, for trace visualization)
   - `LANGSMITH_PROJECT=psa-itt-demo`
3. Verify health check passes
4. Verify UI loads at public URL
5. Verify `LANGSMITH_API_KEY` wiring: if set, traces appear in LangSmith dashboard

**Verification:**
```bash
curl https://your-app.up.railway.app/health  # returns OK
open https://your-app.up.railway.app/ui/     # UI loads
```

### 8.4: End-to-End Smoke Test (Both Problems + Robustness)
**Duration:** ~3 hours
**What:** Test full demo flows on deployed instance — PB-12 + sibling + robustness.

**Steps:**
1. **PB-12 happy path:** webhook → T1→T3→T4 ($10,400) → HITL-1→HITL-2→HITL-3→dispatch→T5→HITL-4→done. Verify: 5 gates fire, trace + deviation_log, SSE streams.
2. **PB-12 deviation:** inject berth conflict → monitor detects → re-compute 100/20 → HITL-5 emergency → delta dispatch → T5 again. Verify: escalation #1+#2, confidence 0.95→0.78→0.90, deviation_log.
3. **Sibling switch:** `POST /agent/switch-problem/pb-01-berth` → verify PB-01 tools (VTIS/OptEVoyage/CITOS) listed, agent adapts, HITL fires for berth reassignment.
4. **Robustness spot-check:** trigger API 503 on T2 → agent logs fallback, notifies.
5. **HITL rejection:** reject at HITL-1 → alternatives presented; modify at HITL-1 → re-validate + re-run T4.
6. **Latency:** measure wall time (happy <30s, deviation <90s), SSE p50/p95 latency.

**Verification:**
```bash
# All 6 checks pass on public URL
# Problem switching works live
# Latency within targets
```

### 8.5: Presentation Deck — PSA Nexus (10 Slides per CodeSprint §6.2)
**Duration:** ~4 hours
**What:** Create 10-slide deck per competition rubric §6.2.

**Steps:**
1. Create `submission/deck.md` (Google Slides / PowerPoint):
   - Slide 1: Executive Summary — "PSA Nexus: Agentic Multi-Party Coordination Platform" + team + C2 cluster ($1.26M–$2.08M)
   - Slide 2: The Disruption Gap — PB-12 ITT failure, why CITOS/PORTNET rule engines fall short (charter §2, phone calls, 4–8h)
   - Slide 3: The Agentic Solution & Value Prop — Nexus platform, PB-12 flagship demo (PPT↔Tuas, 5 systems, 27 min, $8K/incident)
   - Slide 4: Autonomy & HITL Risk Framework — Tier 2 HITL Exception Solver, 5 gates with timeouts, confidence 0.85 threshold
   - Slide 5: System Architecture — LangGraph StateGraph, tool registry, state memory, SSE, one-core-many-problems
   - Slide 6: Execution Trace & Multi-Tool Orchestration — live trace screenshot, tool call sequence (T1→T5), ReAct loop
   - Slide 7: Safety, Guardrails & Fallback — 6 input guards, 7 escalation triggers, 4 robustness scenarios (nominal/incomplete/503/safety), schema validation
   - Slide 8: Scalability & Generalisability — 1 YAML = 1 problem visual (PB-12 ITT vs PB-01 Berth side-by-side), tool swap, 7-problem cluster map
   - Slide 9: Quantified Business Impact & ROI — $8K/incident equation (charter §5), $384K–$576K annual (flagship), $1.26M–$2.08M cluster, ESG (fewer road trips)
   - Slide 10: Summary & Future Roadmap — what's built, what ports can adopt, next steps
2. Export as PDF
3. Include architecture diagram (Mermaid) + generalisability visual

**Verification:**
```bash
# Deck has 10 slides
# Covers all required topics
# Visuals are clear and professional
```

### 8.6: Demo Video — PSA Nexus (10 min per CodeSprint §6.3)
**Duration:** ~4 hours
**What:** Record 10-minute video per competition rubric §6.3.

**Steps:**
1. Script the video:
   - Part 1 (0:00–2:00): Operational Problem & PSA Context — PB-12 ITT failure, manual baseline (12 steps, phone calls, 4–8h, $8K)
   - Part 2 (2:00–3:30): High-Level Architecture — PSA Nexus platform, LangGraph, 8 tools, 5 HITL gates, one core / 7 problems
   - Part 3 (3:30–7:30): Live System Walkthrough —
     * Ingest live disruption event (webhook, 120 containers)
     * Show live trace + tool calling (T1→T5, $10,400 split)
     * Demonstrate robustness: missing field → gap detected, 503 → fallback
     * HITL approval gate (approve → dispatch)
     * **Platform switch: PB-12 → PB-01 (berth delay) — same core, different tools**
   - Part 4 (7:30–9:00): Edge Cases & Safety — feeder berth conflict injected at step 8 → deviation detected → re-plan 100/20 → HITL-5 → delta dispatch; stale data → escalation
   - Part 5 (9:00–10:00): Business Impact Math + Closing — $8K/incident equation, $1.26M cluster, "one YAML = one problem"
2. Record using screen capture (OBS, Loom) — dashboard + trace visible throughout
3. Edit for clarity and pacing
4. Export as MP4

**Verification:**
```bash
# Video is ~10 minutes
# Shows full demo flow
# Clear narration
```

### 8.7: Submission Package
**Duration:** ~1 hour
**What:** Prepare all submission assets.

**Steps:**
1. Create `submission/` directory:
   ```
   submission/
   ├── deck.pdf          # presentation
   ├── demo.mp4          # video
   ├── README.md         # project summary
   ├── source.zip        # source code archive
   └── architecture.png  # architecture diagram
   ```
2. Create `submission/README.md`:
   - Project name and tagline
   - Problem statement
   - Solution overview
   - Architecture summary
   - How to run locally
   - Key decisions and trade-offs
   - ROI analysis
3. Create `source.zip`:
   - Include: app/, configs/, requirements.txt, Dockerfile, README.md
   - Exclude: .planning/, prototype/, .git/, __pycache__/
4. Verify all assets present

**Verification:**
```bash
ls -la submission/
# deck.pdf, demo.mp4, README.md, source.zip, architecture.png all present
```

## Verification Loop

After all sub-phases complete:
1. `docker build -t psa-agent .` — builds successfully
2. `docker compose up` — starts correctly
3. Deployed to Railway/Render — accessible via public URL
4. Full demo flow works on deployed instance
5. Presentation deck has 10 slides, covers all topics
6. Demo video is 10 minutes, shows full flow
7. All submission assets present

## Commit
After verification: `git commit -m "Phase 8: Polish & deploy — Docker, deployment, submission assets"`
