---
phase: ai_optimisation
reviewed: 2026-08-23T12:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - prototype/pre_approval/ai_optimisation/compute_itt_split.py
  - prototype/shared/utils/provider.py
findings:
  critical: 0
  warning: 0
  info: 2
  total: 2
status: resolved
---

# Phase: Code Review Report

**Reviewed:** 2026-08-23
**Depth:** standard
**Files Reviewed:** 2
**Status:** resolved (all 12 findings fixed)

## Summary

Reviewed the multi-constraint optimisation engine (`compute_itt_split.py`) and the LLM provider abstraction layer (`provider.py`). All 2 critical and 10 warning issues have been resolved. The 2 info-level observations remain as noted below.

## Resolved Findings

| ID | Severity | File | Resolution |
|---|---|---|---|
| CR-01 | critical | compute_itt_split.py:539 | Added `reference_time` param to `_compute_timeline` — defaults to `None` (current time), accepts fixed time for deterministic tests |
| CR-02 | critical | provider.py:308-318 | Fixed Gemini tool format — builds single `function_declarations` list instead of per-tool dicts; fixed role mapping (system skip, assistant→model, user→user) |
| WR-01 | warning | compute_itt_split.py:911-918 | Fixed esc_3 label ("Total transport cost exceeds limit"), added actual cost > threshold check, added esc_2 (feeder hold) and esc_4 (data age) checks |
| WR-02 | warning | compute_itt_split.py:550-554 | Initialized `waves = 0`, added `road_trips > 0` guard — zero trucks with road containers now produces 0 duration (caught by feasibility check) |
| WR-03 | warning | compute_itt_split.py:739-740 | Feeder loading rate/hours now read from `pc_constraints` with fallback defaults |
| WR-04 | warning | compute_itt_split.py:752-758 | `FEEDER_AVAILABLE_FOR_ITT_TEU` now reads from `pc_constraints.get("feeder_available_teu", 40)` |
| WR-05 | warning | compute_itt_split.py:761 | Removed redundant `max_sea_teu` cap (loop already bounds by container counts) |
| WR-06 | warning | compute_itt_split.py:101-113 | `to_dict()` now includes `description`, `escalation_triggers`, `confidence_threshold` |
| WR-07 | warning | provider.py:606-627 | Added `base_url` param to `AnthropicProvider`, `OpenAIProvider`, `DeepSeekProvider`; factory passes `base_url` to named providers |
| WR-08 | warning | provider.py:304 | Fixed Gemini role mapping — system messages skipped, assistant→model, user→user |
| WR-09 | warning | provider.py (all) | Added `chat_with_retry()` method with exponential backoff (3 retries, 1s base) |
| WR-10 | warning | provider.py:662 | Health check is now lazy — cached after first call, no repeated network pings |

## Info (no action needed)

### IN-01: DeepSeek provider is copy-paste of OpenAI provider

**File:** `prototype/shared/utils/provider.py:365-428`
**Status:** Intentional — DeepSeek has its own provider class for clarity and `base_url` default (`https://api.deepseek.com`). Could be collapsed into `CustomProvider` in future.

### IN-02: `container_40ft + container_20ft` may differ from `total_containers` for non-standard sizes

**File:** `prototype/pre_approval/ai_optimisation/compute_itt_split.py:696-699`
**Status:** Cosmetic — only affects log messages. Non-standard container sizes are not expected in the demo scenario.

---

_Reviewed: 2026-08-23_
_Updated: 2026-08-23 (all findings resolved)_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
