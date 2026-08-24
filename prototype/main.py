"""
PSACodeSprint prototype entry — delegates to psa-agent
Per master-charter §7 + tech-stack.md
Run: python PSACodeSprint/prototype/main.py
Or:  python psa-agent/run_demo.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "psa-agent"))

from agent.core import run_agent  # type: ignore

EVENT = {
  "event_type": "ITT_COORDINATION_REQUEST",
  "timestamp": "2026-08-19T10:30:00+08:00",
  "source": "CITOS_PPT",
  "priority": "high",
  "payload": {
    "origin_terminal": "PPT",
    "destination_terminal": "TUAS",
    "vessel_id": "MV PACIFIC STAR",
    "tuas_vessel_departure": "2026-08-19T20:00:00+08:00",
    "container_count": 120,
  }
}

if __name__ == "__main__":
    state = run_agent(EVENT)
    import json
    print(json.dumps({
        "run_id": state.get("run_id"),
        "status": state.get("status"),
        "split": state.get("split_result",{}).get("optimal_split"),
        "trace_len": len(state.get("trace",[])),
        "hitl": len(state.get("hitl_history",[]))
    }, indent=2))
