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
         - GEMINI_API_KEY=${GEMINI_API_KEY}
         - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
         - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
         - CUSTOM_API_KEY=${CUSTOM_API_KEY}
         - LLM_PROVIDER=${LLM_PROVIDER:-anthropic}   # any of: anthropic, openai, gemini, deepseek, ollama, vllm, lmstudio, custom
         - LLM_MODEL=${LLM_MODEL:-claude-sonnet-4-20250514}
         - LLM_BASE_URL=${LLM_BASE_URL:-}              # for custom/ollama/vllm/lmstudio (e.g. http://localhost:11434/v1)
         - LLM_FALLBACK_PROVIDER=${LLM_FALLBACK_PROVIDER:-openai}
         - LLM_FALLBACK_MODEL=${LLM_FALLBACK_MODEL:-gpt-4o}
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
   - `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY` / `DEEPSEEK_API_KEY` / `OPENROUTER_API_KEY` / `CUSTOM_API_KEY` (any one suffices — provider-agnostic)
   - `LLM_PROVIDER` (any of: `anthropic`, `openai`, `gemini`, `deepseek`, `ollama`, `vllm`, `lmstudio`, `custom`) + `LLM_MODEL` + `LLM_BASE_URL` (for local/custom)
   - `LLM_FALLBACK_PROVIDER` + `LLM_FALLBACK_MODEL` (optional fallback)
   - `LANGSMITH_API_KEY` (optional, for trace visualization)
   - `LANGSMITH_PROJECT=psa-nexus`
3. Verify health check passes
4. Verify UI loads at public URL
5. Verify `LANGSMITH_API_KEY` wiring: if set, traces appear in LangSmith dashboard

**Verification:**
```bash
curl https://your-app.up.railway.app/health  # returns OK
open https://your-app.up.railway.app/ui/     # UI loads
```

### 8.4: End-to-End Smoke Test + Latency (Both Problems + Robustness)
**Duration:** ~3 hours
**What:** Test full demo flows on deployed instance — PB-12 + sibling + robustness. Instrument latency for deck slide 7.

**Steps:**
1. **PB-12 happy path:** webhook → T1→T3→T4 ($10,400) → HITL-1→HITL-2→HITL-3→dispatch→T5→HITL-4→done. Verify: 5 gates fire, trace with `risk_score` on every entry, deviation_log empty, SSE streams all 9 event types.
2. **PB-12 deviation:** inject berth conflict → monitor detects → re-compute 100/20 → HITL-5 emergency → delta dispatch → T5 again. Verify: escalation #1+#2, confidence 0.95→0.78→0.90, deviation_log entry, `risk_score` spike.
3. **Sibling switch:** `POST /agent/switch-problem/pb-01-berth` → verify PB-01 tools (VTIS/OptEVoyage/CITOS) listed, agent adapts, HITL fires for berth reassignment — proves platform claim on deploy, not just locally.
4. **Robustness spot-check:** trigger API 503 on T2 → agent uses fallback (`FALLBACKS`), logs `tool_error_fallback` + `notification` SSE; trigger incomplete data → guardrail → secondary query.
5. **HITL rejection:** reject at HITL-1 → alternatives[] presented; modify at HITL-1 → re-validate + re-run T4 → re-present. Stale resume after timeout → 422.
6. **Latency instrumentation:** measure wall time (happy <30s, deviation <90s — from `LLMResponse.latency_ms` + trace `duration_ms`), SSE p50/p95 (time from `broadcaster.publish` to `onmessage` in browser). Add `app/tests/test_latency.py` that asserts `wall_happy < 30s` and `sse_p95 < 500ms` (thresholds for deck). Export `latency_report.json` for slide 7.

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
   - Slide 1: Executive Summary — "PSA Nexus: Agentic Multi-Party Coordination Platform" + team + C2 cluster ($1.26M–$2.08M) — one core, 7 YAMLs, 8 LLM providers
   - Slide 2: The Disruption Gap — PB-12 ITT failure, why CITOS/PORTNET rule engines fall short (charter §2, phone calls, 4–8h, $316K/mo cluster aggregate)
   - Slide 3: The Agentic Solution & Value Prop — Nexus platform (6 shared primitives, one LangGraph core, YAML-per-problem), PB-12 flagship (PPT↔Tuas, 5 systems, 27 min, $8K/incident, ReAct loop)
   - Slide 4: Autonomy & HITL Risk Framework — Tier 2 HITL Exception Solver (Autonomy Trap: HIGH financial risk + multi-party authority), 5 gates with timeouts/timeout_actions (30/15/15/10/30 min), confidence 0.85, 7 triggers
   - Slide 5: System Architecture — LangGraph StateGraph (interrupt+Command+thread_id), tool registry (TOOLSETS per problem), state memory, SSE broadcaster, problem switcher, provider-agnostic (8 endpoints, any base_url)
   - Slide 6: Execution Trace & Multi-Tool Orchestration — live trace screenshot with risk_score + fallback_used per entry, tool sequence (T1→T5 + notify), ReAct thought→tool→observe, tokens + latency_ms from LLMResponse
   - Slide 7: Safety, Guardrails, Fallback & Responsible AI — 6 input guards, 4 robustness scenarios (nominal/incomplete/503/safety), chat_with_retry + FALLBACKS + health_check→fallback provider, schema validation (Pydantic ge 50, weight 0-60000), webhook 422 not 500, late-resume guard, latency wall <30s / SSE p95 (measured 8.4), security: no hardcoded secrets
   - Slide 8: Scalability & Generalisability — 1 YAML = 1 problem visual (PB-12 ITT vs PB-01 Berth: 5 vs 5 tools, 5 vs 2 gates, same core), 7-problem cluster map, prompt templated from ProblemConfig not hardcoded
   - Slide 9: Quantified Business Impact & ROI — $8K/incident equation (charter §5: $8450-$450, T4 transport $1.6K = $12K→$10.4K), $384K–$576K annual (4-6/mo × $8K), $1.26M–$2.08M cluster (8-row table), ESG: 20 fewer road trips on AYE/West Coast Hwy, throughput/TEU
   - Slide 10: Summary & Future Roadmap — what's built (48 sub-phases, 70 requirements, 4 pillars), what ports can adopt, next problems to generalise
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
