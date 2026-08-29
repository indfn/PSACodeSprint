import { useState, useEffect, useCallback } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { RotateCcw, Zap, Radio } from 'lucide-react';
import SystemStatusCard from '@/components/nexus/SystemStatusCard';
import AgentOutput, { AgentEvent } from '@/components/nexus/AgentOutput';
import HitlCard, { HitlGateInfo } from '@/components/nexus/HitlCard';
import CostBreakdown from '@/components/nexus/CostBreakdown';
import WorkflowProgress from '@/components/nexus/WorkflowProgress';
import ProblemBar from '@/components/nexus/ProblemBar';
import { useSSE, SSEEvent } from '@/hooks/use-sse';
import {
  getContainerData,
  getTruckData,
  getFeederData,
  getQcData,
  resetMocks,
  injectEdgeCase,
  initializeSession,
  getScenarios,
  getActiveRun,
  completeProblem,
  type ContainerData,
  type TruckData,
  type FeederData,
  type QcData,
} from '@/api/nexus';

const FALLBACK_SCENARIOS = [
  { id: 'nominal', name: 'Nominal' },
  { id: 'deviation', name: 'Deviation' },
  { id: 'stale', name: 'Stale Data' },
  { id: 'escalation', name: 'Escalation' },
];

const PROBLEM_NAMES: Record<string, string> = {
  'pb-12-itt': 'ITT Coordination',
  'pb-01-berth': 'Berth Reassignment',
};

export default function NexusDashboard() {
  const [activeProblem, setActiveProblem] = useState('pb-12-itt');
  const [scenarios, setScenarios] = useState(FALLBACK_SCENARIOS);
  const [scenario, setScenario] = useState(FALLBACK_SCENARIOS[0].id);
  const [runId, setRunId] = useState<string | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [hitlGate, setHitlGate] = useState<HitlGateInfo | null>(null);

  const [containers, setContainers] = useState<ContainerData | null>(null);
  const [trucks, setTrucks] = useState<TruckData | null>(null);
  const [feeder, setFeeder] = useState<FeederData | null>(null);
  const [qc, setQc] = useState<QcData | null>(null);

  const [costData, setCostData] = useState({
    roadCost: 0,
    seaHandling: 0,
    total: 0,
    baseline: 0,
    alternatives: [] as string[],
  });

  const [confidence, setConfidence] = useState<number | null>(null);
  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [edgeLoading, setEdgeLoading] = useState<string | null>(null);

  // Poll active-run to sync across all instances
  const pollActiveRun = useCallback(async () => {
    try {
      const active = await getActiveRun();
      if (active.run_id && active.status !== 'completed') {
        // There's an active run — connect to it
        if (runId !== active.run_id) {
          setRunId(active.run_id);
          if (active.problem_id) setActiveProblem(active.problem_id);
          setEvents([]);
          setHitlGate(null);
          // Load fresh data for this problem
          resetMocks().catch(() => {});
          initializeSession()
            .then((init) => {
              sessionStorage.setItem('nexus_init_data', JSON.stringify(init));
              setContainers(init.containers);
              setTrucks(init.trucks);
              setFeeder(init.feeder);
              setQc(init.qc);
            })
            .catch(() => {});
        }
        // If there's a hitl_card from the registry, use it
        if (active.hitl_card) {
          const gateId = (active.hitl_card.gate_id as string) || (active.hitl_card.gateId as string) || '';
          const gateName = (active.hitl_card.gate_name as string) || (active.hitl_card.gateName as string) || 'Approval Required';
          const cardData = (active.hitl_card.approval_card as Record<string, unknown>) || active.hitl_card;
          setHitlGate({ gate_id: gateId, gate_name: gateName, data: cardData as Record<string, unknown> });
        }
      } else if (active.status === 'completed' && runId) {
        // Run just completed — clear after brief delay
        setTimeout(() => {
          setRunId(null);
          setEvents([]);
          setHitlGate(null);
          setConfidence(null);
          setRiskScore(null);
        }, 5000);
      } else if (active.status === 'idle' && runId) {
        // No active run and we had one — clear
        setRunId(null);
        setEvents([]);
        setHitlGate(null);
        setConfidence(null);
        setRiskScore(null);
      }
    } catch {
      // Registry not available, ignore
    }
  }, [runId]);

  useEffect(() => {
    pollActiveRun();
    const interval = setInterval(pollActiveRun, 3000);
    return () => clearInterval(interval);
  }, [pollActiveRun]);

  // Load scenarios for active problem
  useEffect(() => {
    getScenarios().then((list) => {
      if (list && list.length) {
        setScenarios(list.map((s) => ({ id: s.id, name: s.name })));
        setScenario((prev) => (list.some((s) => s.id === prev) ? prev : list[0].id));
      }
    }).catch(() => {});
  }, [activeProblem]);

  // Load initial data
  useEffect(() => {
    const cached = sessionStorage.getItem('nexus_init_data');
    if (cached) {
      try {
        const init = JSON.parse(cached);
        if (init.problem_id) setActiveProblem(init.problem_id);
        setContainers(init.containers);
        setTrucks(init.trucks);
        setFeeder(init.feeder);
        setQc(init.qc);
        return;
      } catch { /* ignore */ }
    }
    initializeSession()
      .then((init) => {
        sessionStorage.setItem('nexus_init_data', JSON.stringify(init));
        if (init.problem_id) setActiveProblem(init.problem_id);
        setContainers(init.containers);
        setTrucks(init.trucks);
        setFeeder(init.feeder);
        setQc(init.qc);
      })
      .catch(() => {
        getContainerData().then(setContainers).catch(() => {});
        getTruckData().then(setTrucks).catch(() => {});
        getFeederData().then(setFeeder).catch(() => {});
        getQcData().then(setQc).catch(() => {});
      });
  }, []);

  const applyCostFromPayload = useCallback((payload: Record<string, unknown>) => {
    try {
      const opt = (payload.optimal_split as Record<string, unknown>) || (payload.cost_breakdown as Record<string, unknown>)?.optimal_split as Record<string, unknown> || null;
      const vs = (payload.cost_vs_baseline as Record<string, unknown>) || (payload.cost_breakdown as Record<string, unknown>)?.cost_vs_baseline as Record<string, unknown> || null;
      const alts = (payload.alternatives as unknown[]) || (payload.cost_breakdown as Record<string, unknown>)?.alternatives as unknown[] || [];
      if (opt) {
        setCostData({
          roadCost: (opt.road_cost as number) ?? (opt.roadCost as number) ?? 0,
          seaHandling: (opt.sea_terminal_handling_cost as number) ?? (opt.seaHandling as number) ?? 0,
          total: (opt.total_transport_cost as number) ?? (opt.total as number) ?? 0,
          baseline: (vs?.baseline_all_road_cost as number) ?? (vs?.baseline as number) ?? 0,
          alternatives: Array.isArray(alts) ? alts.map((a) => typeof a === 'string' ? a : JSON.stringify(a)) : [],
        });
      } else if (payload.road_cost || payload.total) {
        setCostData({
          roadCost: (payload.road_cost as number) || 0,
          seaHandling: (payload.sea_handling as number) || 0,
          total: (payload.total as number) || 0,
          baseline: (payload.baseline as number) || 0,
          alternatives: (payload.alternatives as string[]) || [],
        });
      }
    } catch { /* ignore */ }
  }, []);

  // SSE event handler
  const handleSSEEvent = useCallback(
    (event: SSEEvent) => {
      const ts = event.timestamp || new Date().toISOString();
      const data = event.data;

      switch (event.event) {
        case 'trace_entry': {
          const msg = (data.message as string) || (data.action as string) || (data.node ? `${data.node}:${data.action}` : JSON.stringify(data));
          const resultMsg = (data.result as Record<string, unknown>)?.tool ? ` tool=${(data.result as Record<string, unknown>).tool}` : '';
          setEvents((prev) => [...prev, { timestamp: ts, message: `${msg}${resultMsg}` }]);
          if (typeof data.risk_score === 'number') setRiskScore(data.risk_score);
          if (typeof (data.result as Record<string, unknown>)?.risk_score === 'number') setRiskScore((data.result as Record<string, unknown>).risk_score as number);
          if (typeof data.confidence === 'number') setConfidence(data.confidence);
          const resObj = data.result as Record<string, unknown> | undefined;
          if (resObj && typeof resObj.confidence === 'number') setConfidence(resObj.confidence as number);
          applyCostFromPayload(data);
          if (resObj) applyCostFromPayload(resObj);
          break;
        }

        case 'hitl_card':
        case 'hitl_request': {
          const gateId = (data.gate_id as string) || (data.gateId as string) || '';
          const gateName = (data.gate_name as string) || (data.gateName as string) || 'Approval Required';
          const cardData = (data.approval_card as Record<string, unknown>) || (data.decision_data as Record<string, unknown>) || (data.card as Record<string, unknown>) || data;
          if (typeof data.confidence === 'number') setConfidence(data.confidence);
          if (typeof data.risk_score === 'number') setRiskScore(data.risk_score);
          if (typeof (cardData.confidence as number) === 'number') setConfidence(cardData.confidence as number);
          if (typeof (cardData.risk_score as number) === 'number') setRiskScore(cardData.risk_score as number);
          applyCostFromPayload(cardData as Record<string, unknown>);
          applyCostFromPayload(data);
          setHitlGate({ gate_id: gateId, gate_name: gateName, data: cardData as Record<string, unknown> });
          setEvents((prev) => [...prev, { timestamp: ts, message: `HITL gate ${gateId}: ${gateName} — awaiting approval` }]);
          break;
        }

        case 'hitl_resolved':
        case 'hitl_timeout':
          setHitlGate(null);
          setEvents((prev) => [...prev, { timestamp: ts, message: `HITL ${event.event}: ${JSON.stringify(data).slice(0,120)}` }]);
          break;

        case 'cost_update':
          applyCostFromPayload(data);
          if ((data.road_cost as number) || (data.total as number)) {
            setCostData({
              roadCost: (data.road_cost as number) || 0,
              seaHandling: (data.sea_handling as number) || 0,
              total: (data.total as number) || 0,
              baseline: (data.baseline as number) || 0,
              alternatives: (data.alternatives as string[]) || [],
            });
          }
          break;

        case 'confidence_update':
          if (typeof data.confidence === 'number') setConfidence(data.confidence);
          setEvents((prev) => [...prev, { timestamp: ts, message: `Confidence: ${Math.round((data.confidence as number > 1 ? data.confidence as number : (data.confidence as number)*100))}%` }]);
          break;

        case 'tool_call': {
          const tool = (data.tool as string) || (data.name as string) || 'tool';
          setEvents((prev) => [...prev, { timestamp: ts, message: `→ ${tool} ${JSON.stringify((data.args as object) || {}).slice(0,120)}` }]);
          break;
        }

        case 'tool_result': {
          const tool = (data.tool as string) || (data.name as string) || 'tool';
          const out = (data.output as Record<string, unknown>) || data;
          setEvents((prev) => [...prev, { timestamp: ts, message: `← ${tool} completed${(data.fallback_used ? ' (fallback)' : '')}` }]);
          applyCostFromPayload(out);
          applyCostFromPayload(data);
          if (typeof (data.risk_score as number) === 'number') setRiskScore(data.risk_score as number);
          if (typeof (out.risk_score as number) === 'number') setRiskScore(out.risk_score as number);
          break;
        }

        case 'tool_confirmation': {
          const msg = (data.message as string) || `${data.tool}: ${data.status}`;
          setEvents((prev) => [...prev, { timestamp: ts, message: `✓ ${msg}` }]);
          break;
        }

        case 'agent_thinking':
          setEvents((prev) => [...prev, { timestamp: ts, message: `Agent reasoning: ${((data.messages as unknown) || data.step || JSON.stringify(data)).toString().slice(0,200)}` }]);
          break;

        case 'escalation':
          setEvents((prev) => [...prev, { timestamp: ts, message: `⚠ Escalation: ${(data.trigger as string) || JSON.stringify(data).slice(0,150)}` }]);
          if (typeof data.risk_score === 'number') setRiskScore(data.risk_score);
          break;

        case 'deviation':
          setEvents((prev) => [...prev, { timestamp: ts, message: `▲ Deviation: ${(data.type as string) || JSON.stringify(data).slice(0,150)}` }]);
          break;

        case 'notification':
          setEvents((prev) => [...prev, { timestamp: ts, message: `🔔 Notification: ${JSON.stringify(data).slice(0,150)}` }]);
          break;

        case 'run_complete':
          setEvents((prev) => [...prev, { timestamp: ts, message: 'Run complete.' }]);
          if (activeProblem) {
            completeProblem(activeProblem).catch(() => {});
          }
          break;

        case 'system_status':
          getContainerData().then(setContainers).catch(() => {});
          getTruckData().then(setTrucks).catch(() => {});
          getFeederData().then(setFeeder).catch(() => {});
          getQcData().then(setQc).catch(() => {});
          break;

        default:
          setEvents((prev) => [
            ...prev,
            {
              timestamp: ts,
              message: (data.message as string) || `[${event.event}] ${JSON.stringify(data).slice(0,200)}`,
            },
          ]);
      }
    },
    [applyCostFromPayload, activeProblem]
  );

  useSSE(runId, handleSSEEvent);

  // Called by ProblemBar when user clicks Start
  const handleRunStarted = useCallback((newRunId: string, problemId: string) => {
    setRunId(newRunId);
    setActiveProblem(problemId);
    setEvents([]);
    setHitlGate(null);
    setConfidence(null);
    setRiskScore(null);
    resetMocks().catch(() => {});
    initializeSession()
      .then((init) => {
        sessionStorage.setItem('nexus_init_data', JSON.stringify(init));
        setContainers(init.containers);
        setTrucks(init.trucks);
        setFeeder(init.feeder);
        setQc(init.qc);
      })
      .catch(() => {});
  }, []);

  async function handleReset() {
    await resetMocks();
    sessionStorage.removeItem('nexus_init_data');
    setRunId(null);
    setEvents([]);
    setHitlGate(null);
    setConfidence(null);
    setRiskScore(null);
  }

  async function handleEdgeCase(caseType: string) {
    setEdgeLoading(caseType);
    try {
      await injectEdgeCase(caseType, undefined, runId || undefined);
      setEvents((prev) => [
        ...prev,
        { timestamp: new Date().toISOString(), message: `Edge case injected: ${caseType}${runId ? ` (run ${runId.slice(0,8)})` : ''}` },
      ]);
      getContainerData().then(setContainers).catch(() => {});
      getTruckData().then(setTrucks).catch(() => {});
      getFeederData().then(setFeeder).catch(() => {});
      getQcData().then(setQc).catch(() => {});
    } catch (err) {
      console.error('Edge case injection failed:', err);
    } finally {
      setEdgeLoading(null);
    }
  }

  const isIdle = !runId;
  const containerStatus =
    !containers ? 'amber' :
    containers.total_containers > 0
      ? containers.data_age_minutes < 10
        ? 'green'
        : 'amber'
      : 'amber';
  const truckStatus = !trucks ? 'amber' :
    trucks.available_trucks > trucks.total_fleet * 0.3 ? 'green' : 'amber';
  const feederStatus = !feeder ? 'amber' :
    feeder.berth_status.includes('berthed') ? 'green' :
    feeder.berth_status === 'conflict' ? 'red' : 'amber';

  return (
    <div className="space-y-3">
      {/* ProblemBar — always visible at top */}
      <ProblemBar onRunStarted={handleRunStarted} activeRunProblemId={runId ? activeProblem : null} />

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold tracking-tight">Nexus Dashboard</h1>
          <Badge variant="secondary" className="text-xs">
            {PROBLEM_NAMES[activeProblem] || activeProblem}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-[10px]">
            Confidence: {confidence !== null ? `${Math.round((confidence > 1 ? confidence : confidence * 100))}%` : '—'}
          </Badge>
          <Badge variant="outline" className="text-[10px]">
            Risk: {riskScore !== null ? (riskScore >= 0.7 ? 'High' : riskScore >= 0.4 ? 'Medium' : 'Low') : '—'}
          </Badge>
        </div>
      </div>

      {/* Action bar */}
      <div className="flex flex-wrap items-center gap-2">
        <Select value={scenario} onValueChange={(v) => v && setScenario(v)}>
          <SelectTrigger className="h-8 w-[130px]">
            <SelectValue placeholder="Scenario">
              {scenarios.find((s) => s.id === scenario)?.name}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {scenarios.map((s) => (
              <SelectItem key={s.id} value={s.id}>
                {s.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="h-4 w-px bg-border" />
        <Button
          size="sm"
          variant="outline"
          disabled={!!edgeLoading || isIdle}
          onClick={() => handleEdgeCase('berth_conflict')}
          className="gap-1.5"
        >
          <Zap size={14} />
          {edgeLoading === 'berth_conflict' ? 'Injecting...' : 'Berth Conflict'}
        </Button>
        <div className="h-4 w-px bg-border" />
        <Button size="sm" variant="ghost" onClick={handleReset} className="gap-1.5">
          <RotateCcw size={14} />
          Reset
        </Button>
        {runId && (
          <Badge variant="secondary" className="text-[10px]">
            Run: {runId.slice(0, 8)}
          </Badge>
        )}
      </div>

      <WorkflowProgress hitlGateId={hitlGate?.gate_id || null} events={events} status={events.some(e=>e.message.includes('Run complete'))?'completed': hitlGate?'running' : events.length?'running':'idle'} />

      {/* Main content — always renders the same layout */}
      <div className="grid grid-cols-12 gap-4">
        {/* Left column: HITL + Agent output */}
        <div className="col-span-12 lg:col-span-8 space-y-4">
          {isIdle ? (
            /* Idle state: "Waiting for event" placeholder */
            <div className="rounded-xl border bg-card px-4 py-8 flex flex-col items-center justify-center text-center space-y-3 min-h-[180px]">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Radio size={16} className="animate-pulse" />
                <span className="text-sm font-medium">Waiting for event</span>
              </div>
              <p className="text-xs text-muted-foreground max-w-[280px]">
                Select a problem from the bar above and click <span className="font-medium">Start</span> to simulate a webhook event.
              </p>
              <div className="flex items-center gap-4 text-[10px] text-muted-foreground pt-2">
                <span>All instances share this state</span>
                <span>·</span>
                <span>One active run at a time</span>
              </div>
            </div>
          ) : (
            /* Running state: live HITL card */
            <HitlCard
              gate={hitlGate}
              runId={runId || ''}
              onResponded={() => setHitlGate(null)}
              onNextGate={(next) => {
                if (next) {
                  setHitlGate(next);
                  if (typeof (next.data as Record<string, unknown>).confidence === 'number') setConfidence((next.data as Record<string, unknown>).confidence as number);
                  if (typeof (next.data as Record<string, unknown>).risk_score === 'number') setRiskScore((next.data as Record<string, unknown>).risk_score as number);
                  applyCostFromPayload(next.data);
                } else {
                  setHitlGate(null);
                  setEvents((prev) => [...prev, { timestamp: new Date().toISOString(), message: 'HITL approved — proceeding' }]);
                }
              }}
            />
          )}

          <AgentOutput events={events} />
        </div>

        {/* Right column: Cost + Status cards */}
        <div className="col-span-12 lg:col-span-4 space-y-1.5">
          <CostBreakdown
            roadCost={costData.roadCost}
            seaHandling={costData.seaHandling}
            total={costData.total}
            baseline={costData.baseline}
            alternatives={costData.alternatives}
            hitlGateId={hitlGate?.gate_id || null}
            hitlData={hitlGate?.data || null}
          />

          <SystemStatusCard
            name="CITOS PPT"
            metric={`${containers?.total_containers ?? 0} / 140 TEU yard`}
            value={containers?.total_containers ?? 0}
            max={140}
            status={containerStatus}
            detail={containers ? `${containers.dg_containers} DG · ${containers.blocks_affected?.join(', ') || '4 blocks'} · ${containers.data_age_minutes < 10 ? `${containers.data_age_minutes.toFixed(1)}m fresh` : `${containers.data_age_minutes.toFixed(0)}m stale`}` : undefined}
            tooltip="Yard utilization: containers / 140 TEU capacity. Green <10m fresh data, amber stale."
          />
          <SystemStatusCard
            name="OptETruck"
            metric={`${trucks?.available_trucks ?? 0} / ${trucks?.total_fleet ?? 0} trucks`}
            value={trucks?.available_trucks ?? 0}
            max={trucks?.total_fleet ?? 1}
            status={truckStatus}
            detail={trucks ? `${trucks.transit_time_minutes} min PPT→Tuas • $150/trip • ${trucks.road_conditions?.AYE || 'normal'}` : undefined}
            tooltip="LTA: 1×40ft or 2×20ft per truck. Capacity vs 80 trips all-road baseline."
          />
          <SystemStatusCard
            name="Feeder"
            metric={`${feeder?.current_occupancy_teu ?? 0} / ${feeder?.capacity_teu ?? 1} TEU`}
            value={feeder?.current_occupancy_teu ?? 0}
            max={feeder?.capacity_teu ?? 1}
            status={feederStatus}
            detail={feeder ? `${feeder.berth_status} • ${feeder.departure_window?.earliest?.slice(11,16)}–${feeder.departure_window?.latest?.slice(11,16)} • hold $${feeder.hold_cost_per_hour}/hr` : undefined}
            tooltip="Berthed vs conflict (red). Late departure misses Port Klang tidal window → $5k missed connection."
          />
          <SystemStatusCard
            name="Tuas QC"
            metric={qc ? `${qc.qc_status.filter((q) => q.status === 'available').length}/${qc.qc_count} cranes` : 'Loading...'}
            value={qc ? qc.qc_status.filter((q) => q.status === 'available').length : 0}
            max={qc?.qc_count ?? 40}
            status={
              !qc ? 'amber' :
              qc.qc_status.filter((q) => q.status === 'available').length >= qc.qc_count * 0.9 ? 'green' :
              qc.qc_status.some((q) => q.status === 'available') ? 'amber' : 'red'
            }
            detail={qc ? `Berth B-03 • FIFO loading • 30 min margin to departure` : undefined}
            tooltip="40 QCs at Tuas mega port. Sequence updated per ITT ETAs (road 14:30, sea 16:30)."
          />
        </div>
      </div>
    </div>
  );
}
