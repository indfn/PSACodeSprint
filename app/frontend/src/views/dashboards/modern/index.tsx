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
import { RotateCcw, Zap, Play } from 'lucide-react';
import SystemStatusCard from '@/components/nexus/SystemStatusCard';
import AgentOutput, { AgentEvent } from '@/components/nexus/AgentOutput';
import HitlCard, { HitlGateInfo } from '@/components/nexus/HitlCard';
import EscalationPopup from '@/components/nexus/EscalationPopup';
import CostBreakdown from '@/components/nexus/CostBreakdown';
import WorkflowProgress from '@/components/nexus/WorkflowProgress';
import EventCard from '@/components/nexus/EventCard';
import { useSSE, SSEEvent } from '@/hooks/use-sse';
import {
  getContainerData,
  getTruckData,
  getFeederData,
  getQcData,
  resetMocks,
  resetAll,
  resetRun,
  injectEdgeCase,
  getScenarios,
  getActiveRun,
  getActiveProblem,
  getRegistry,
  createEvent,
  switchProblem,
  completeProblem,
  type ContainerData,
  type TruckData,
  type FeederData,
  type QcData,
  type RegistryProblem,
} from '@/api/nexus';

const FALLBACK_SCENARIOS = [
  { id: 'nominal', name: 'Normal' },
  { id: 'deviation', name: 'Feeder Berth Conflict' },
  { id: 'stale', name: 'Stale/Missing Data' },
  { id: 'escalation', name: 'Low Trucks' },
];

const FALLBACK_PROBLEMS: RegistryProblem[] = [
  { problem_id: 'pb-12-itt', name: 'ITT Coordination', description: '', status: 'idle', short_id: 'pb-12' },
  { problem_id: 'pb-01-berth', name: 'Berth Reassignment', description: '', status: 'idle', short_id: 'pb-01' },
];

export default function NexusDashboard() {
  const [activeProblem, setActiveProblem] = useState('pb-12-itt');
  const [problems, setProblems] = useState<RegistryProblem[]>(FALLBACK_PROBLEMS);
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
  const [simulating, setSimulating] = useState(false);
  const [webhookEvent, setWebhookEvent] = useState<{ id: string; data: Record<string, unknown> } | null>(null);

  // Poll active-run to sync across all instances
  const pollActiveRun = useCallback(async () => {
    try {
      const active = await getActiveRun();
      if (active.run_id && active.status !== 'completed') {
        if (runId !== active.run_id) {
          setRunId(active.run_id);
          if (active.problem_id) setActiveProblem(active.problem_id);
          setEvents([]);
          setHitlGate(null);
        }
        if (active.hitl_card) {
          const gateId = (active.hitl_card.gate_id as string) || (active.hitl_card.gateId as string) || '';
          const gateName = (active.hitl_card.gate_name as string) || (active.hitl_card.gateName as string) || 'Approval Required';
          const cardData = (active.hitl_card.approval_card as Record<string, unknown>) || active.hitl_card;
          setHitlGate({ gate_id: gateId, gate_name: gateName, data: cardData as Record<string, unknown> });
        }
      } else if (active.status === 'completed' && runId) {
        setTimeout(() => {
          setRunId(null);
          setEvents([]);
          setHitlGate(null);
          setConfidence(null);
          setRiskScore(null);
          setWebhookEvent(null);
          setContainers(null);
          setTrucks(null);
          setFeeder(null);
          setQc(null);
          setCostData({ roadCost: 0, seaHandling: 0, total: 0, baseline: 0, alternatives: [] });
        }, 5000);
      } else if (active.status === 'idle' && runId) {
        setRunId(null);
        setEvents([]);
        setHitlGate(null);
        setConfidence(null);
        setRiskScore(null);
        setWebhookEvent(null);
        setContainers(null);
        setTrucks(null);
        setFeeder(null);
        setQc(null);
        setCostData({ roadCost: 0, seaHandling: 0, total: 0, baseline: 0, alternatives: [] });
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

  // Sync active problem from backend on mount
  useEffect(() => {
    getActiveProblem()
      .then((p) => { if (p.problem_id) setActiveProblem(p.problem_id); })
      .catch(() => {});
  }, []);

  // Fetch all problems from registry on mount
  useEffect(() => {
    getRegistry()
      .then((res) => {
        if (res.problems && res.problems.length) {
          setProblems(res.problems);
        }
      })
      .catch(() => {});
  }, []);

  // Load scenarios for active problem
  useEffect(() => {
    getScenarios().then((list) => {
      if (list && list.length) {
        setScenarios(list.map((s) => ({ id: s.id, name: s.name })));
        setScenario((prev) => (list.some((s) => s.id === prev) ? prev : list[0].id));
      }
    }).catch(() => {});
  }, [activeProblem]);

  // Status cards populate progressively via SSE tool_result events
  // (get_itt_candidates → CITOS, check_road → OptETruck, check_sea → Feeder, compute_split → QC)

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
          // Skip show_card trace entries — hitl_card SSE handles those
          if (data.node === 'hitl' && data.action === 'show_card') break;
          const resObj = data.result as Record<string, unknown> | undefined;
          // Build rich message from trace data
          let msg = '';
          if (data.node === 'agent' && data.action === 'reason') {
            const tc = resObj?.tool_calls as Array<{name: string; function?: {name: string}}> | undefined;
            const rawContent = (resObj?.content as string) || '';
            // Extract reasoning and tool names from content (may be JSON with reasoning+tool_calls, or plain text)
            let reasoning = '';
            let toolNames: string[] = [];
            // Get tool names from trace tool_calls (OpenAI format {function:{name}} or flat {name})
            if (tc && tc.length > 0) {
              toolNames = tc.map((t) => t.function?.name || t.name).filter(Boolean);
            }
            // ALWAYS try to extract from raw content — provider may have parsed JSON that trace didn't
            if (rawContent) {
              try {
                let jsonText = rawContent.trim();
                if (jsonText.startsWith('```')) {
                  const lines = jsonText.split('\n');
                  jsonText = lines.slice(1, -1).join('\n');
                }
                const parsed = JSON.parse(jsonText);
                if (parsed && typeof parsed === 'object') {
                  reasoning = parsed.reasoning || '';
                  if (parsed.tool_calls && Array.isArray(parsed.tool_calls)) {
                    const jsonTools = parsed.tool_calls.map((t: {name: string}) => t.name).filter(Boolean);
                    if (jsonTools.length > toolNames.length) toolNames = jsonTools;
                  }
                }
              } catch {
                // Not JSON — use content as reasoning, regex for tool names
                reasoning = rawContent;
                if (toolNames.length === 0) {
                  const nameMatches = rawContent.match(/"name"\s*:\s*"(\w+)"/g);
                  if (nameMatches) {
                    toolNames = nameMatches.map((m: string) => m.replace(/"name"\s*:\s*"/, '').replace(/"$/, ''));
                  }
                }
              }
            }
            // ALWAYS emit reasoning as a separate event if we have it
            if (reasoning && reasoning.length > 10) {
              setEvents((prev) => [...prev, { timestamp: new Date().toISOString(), message: `reasoning:${reasoning}` }]);
            }
            if (toolNames.length > 0) {
              msg = `Agent reasoning → calling ${toolNames.join(', ')}`;
            } else if (reasoning) {
              msg = `Agent: ${reasoning.slice(0, 200)}`;
            } else {
              msg = 'Agent reasoning…';
            }
          } else if (data.node === 'tool' && data.action === 'call_tool') {
            const toolName = resObj?.tool || 'tool';
            msg = `→ ${toolName}`;
          } else if (data.node === 'tool' && data.action === 'result') {
            const toolName = resObj?.tool || 'tool';
            msg = `← ${toolName} completed`;
          } else if (data.node === 'hitl') {
            msg = data.action === 'approve' ? 'HITL approved' : data.action === 'reject' ? 'HITL rejected' : `HITL ${data.action}`;
          } else if (data.node === 'monitor') {
            msg = `Monitor: ${data.action}`;
          } else {
            msg = (data.message as string) || (data.action as string) || `${data.node}:${data.action}`;
          }
          const resultMsg = resObj?.tool ? ` tool=${resObj.tool}` : '';
          setEvents((prev) => [...prev, { timestamp: ts, message: `${msg}${resultMsg}` }]);
          if (typeof data.risk_score === 'number') setRiskScore(data.risk_score);
          if (typeof resObj?.risk_score === 'number') setRiskScore(resObj.risk_score as number);
          if (typeof data.confidence === 'number') setConfidence(data.confidence);
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
          // Populate status cards directly from tool output (not refetch, to avoid RNG desync)
          if (tool === 'get_itt_candidates') {
            const c = out as unknown as ContainerData;
            if (c.total_containers || c.total_teu) setContainers(c);
            else getContainerData().then(setContainers).catch(() => {});
          } else if (tool === 'check_road_itt_capacity') {
            const t = out as unknown as TruckData;
            if (t.available_trucks !== undefined) setTrucks(t);
            else getTruckData().then(setTrucks).catch(() => {});
          } else if (tool === 'check_sea_itt_capacity') {
            const f = out as unknown as FeederData;
            if (f.feeder_id) setFeeder(f);
            else getFeederData().then(setFeeder).catch(() => {});
          } else if (tool === 'compute_itt_split' || tool === 'update_tuas_loading_sequence') {
            getQcData().then(setQc).catch(() => {});
          }
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

  async function handleSimulate() {
    setSimulating(true);
    setWebhookEvent(null);
    try {
      const res = await createEvent(activeProblem);
      setWebhookEvent({ id: `evt-${Date.now()}`, data: res.event });
    } catch (err) {
      console.error('Create event failed:', err);
    } finally {
      setSimulating(false);
    }
  }

  const handleRunStarted = useCallback((newRunId: string) => {
    setRunId(newRunId);
    setEvents([]);
    setHitlGate(null);
    setConfidence(null);
    setRiskScore(null);
    setCostData({ roadCost: 0, seaHandling: 0, total: 0, baseline: 0, alternatives: [] });
    setContainers(null);
    setTrucks(null);
    setFeeder(null);
    setQc(null);
  }, []);

  async function handleReset() {
    const curRunId = runId;
    setRunId(null);
    setEvents([]);
    setHitlGate(null);
    setConfidence(null);
    setRiskScore(null);
    setWebhookEvent(null);
    setContainers(null);
    setTrucks(null);
    setFeeder(null);
    setQc(null);
    setCostData({ roadCost: 0, seaHandling: 0, total: 0, baseline: 0, alternatives: [] });
    sessionStorage.removeItem('nexus_init_data');
    try {
      if (curRunId) await resetRun(curRunId);
      else await resetAll();
    } catch { /* fallback: ensure mocks clean even if run reset fails */ }
    try { await resetMocks(); } catch { /* ignore */ }
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
  const feederBerthLabel = !feeder ? '' :
    feeder.berth_status === 'berthed_at_PPT_B12' ? 'Berthed at PPT B12' :
    feeder.berth_status === 'berthed' ? 'Berthed' :
    feeder.berth_status === 'conflict' ? 'Conflict' :
    feeder.berth_status === 'available' ? 'Available' :
    feeder.berth_status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold tracking-tight">Nexus Dashboard</h1>
          <Badge variant="secondary" className="text-xs">
            {problems.find((p) => p.problem_id === activeProblem)?.name || activeProblem}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-[10px]">
            Confidence: {confidence !== null ? `${Math.round((confidence > 1 ? confidence : confidence * 100))}%` : '—'}
          </Badge>
          <Badge variant={riskScore !== null && riskScore > 0.35 ? 'destructive' : riskScore !== null && riskScore > 0.15 ? 'secondary' : 'outline'} className="text-[10px]">
            Risk: {riskScore !== null ? (riskScore > 0.35 ? 'High' : riskScore > 0.15 ? 'Medium' : 'Low') : '—'}
          </Badge>
        </div>
      </div>

      {/* Action bar */}
      <div className="flex flex-wrap items-center gap-2">
        <Select value={activeProblem} onValueChange={(v) => {
          if (v && v !== activeProblem) {
            setActiveProblem(v);
            switchProblem(v).catch(() => {});
          }
        }}>
          <SelectTrigger className="h-8 w-[160px]">
            <SelectValue>
              {problems.find((p) => p.problem_id === activeProblem)?.name || activeProblem}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {problems.map((p) => (
              <SelectItem key={p.problem_id} value={p.problem_id}>
                {p.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          size="sm"
          disabled={simulating || !!runId}
          onClick={handleSimulate}
          className="gap-1.5"
        >
          <Play size={14} />
          {simulating ? 'Creating...' : 'Simulate Webhook'}
        </Button>
        <div className="h-4 w-px bg-border" />
        <span className="text-[10px] text-muted-foreground">Scenario for run:</span>
        <Select value={scenario} onValueChange={(v) => v && setScenario(v)}>
          <SelectTrigger className="h-8 w-[130px]">
            <SelectValue>
              {scenarios.find((s) => s.id === scenario)?.name || scenario}
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
          disabled={!!edgeLoading || !runId}
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

      <WorkflowProgress hitlGateId={hitlGate?.gate_id || null} hitlData={hitlGate?.data || null} events={events} status={events.some(e=>e.message.includes('Run complete'))?'completed': hitlGate?'running' : events.length?'running':'idle'} />

      {/* Main content — always renders the same layout */}
      <div className="grid grid-cols-12 gap-4">
        {/* Left column: Event/HITL card + Agent output */}
        <div className="col-span-12 lg:col-span-8 space-y-4">
          {!runId ? (
            /* Idle: show EventCard */
            <EventCard
              eventId={webhookEvent?.id || null}
              eventData={webhookEvent?.data || null}
              scenario={scenario}
              problemId={activeProblem}
              onRunStarted={handleRunStarted}
            />
          ) : hitlGate ? (
            hitlGate.gate_id === 'HITL-5' ? (
              <EscalationPopup gate={hitlGate} runId={runId} onResolved={() => setHitlGate(null)} onNextGate={(next) => {
                if (next) {
                  setHitlGate(next);
                  if (typeof (next.data as Record<string, unknown>).confidence === 'number') setConfidence((next.data as Record<string, unknown>).confidence as number);
                  if (typeof (next.data as Record<string, unknown>).risk_score === 'number') setRiskScore((next.data as Record<string, unknown>).risk_score as number);
                  applyCostFromPayload(next.data);
                } else {
                  setHitlGate(null);
                  setEvents((prev) => [...prev, { timestamp: new Date().toISOString(), message: 'Escalation resolved — proceeding' }]);
                }
              }} />
            ) : (
            /* HITL gate active: show approval card */
            <HitlCard
              gate={hitlGate}
              runId={runId}
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
          )
          ) : events.length === 0 ? (
            /* Just started, no events yet: show webhook event received */
            <EventCard
              eventId={webhookEvent?.id || null}
              eventData={webhookEvent?.data || null}
              scenario={scenario}
              problemId={activeProblem}
              onRunStarted={handleRunStarted}
            />
          ) : (
            /* Running but no HITL gate: ingest/processing stage */
            <div className="rounded-xl border bg-card p-4 flex items-center gap-2 text-muted-foreground">
              <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
              <span className="text-sm">Processing… waiting for agent to reach HITL gate</span>
            </div>
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
            awaiting={!containers}
            metric={containers ? `Total ${containers.total_teu} TEU for Transfer` : '—'}
            value={containers?.total_teu ?? 0}
            max={containers?.total_teu ?? 1}
            status={containerStatus}
            detail={containers ? `${containers.container_breakdown?.['40ft_feu'] ?? 0} · 40ft Containers\n${containers.container_breakdown?.['20ft_teu'] ?? 0} · 20ft Containers` : undefined}
            tooltip={containers ? `ITT need: ${containers.container_breakdown?.['40ft_feu'] ?? 0}×40ft (×2 TEU) + ${containers.container_breakdown?.['20ft_teu'] ?? 0}×20ft = ${containers.total_teu} TEU · ${containers.dg_containers} DG · ${containers.blocks_affected?.join(', ') || '4 blocks'} · ${containers.data_age_minutes < 10 ? `${containers.data_age_minutes.toFixed(1)}m fresh` : `${containers.data_age_minutes.toFixed(0)}m stale`}` : 'ITT candidates from CITOS PPT'}
          />
          <SystemStatusCard
            name="OptETruck"
            awaiting={!trucks}
            metric={`${trucks?.available_trucks ?? 0} / ${trucks?.total_fleet ?? 0} trucks`}
            value={trucks?.available_trucks ?? 0}
            max={trucks?.total_fleet ?? 1}
            status={truckStatus}
            detail={trucks ? `${trucks.transit_time_minutes} min PPT→Tuas • $150/trip • ${trucks.road_conditions?.AYE || 'normal'}` : undefined}
            tooltip="LTA: 1×40ft or 2×20ft per truck. Capacity vs 80 trips all-road baseline."
          />
          <SystemStatusCard
            name="Feeder"
            awaiting={!feeder}
            metric={`${feeder?.current_occupancy_teu ?? 0} / ${feeder?.capacity_teu ?? 1} TEU`}
            value={feeder?.current_occupancy_teu ?? 0}
            max={feeder?.capacity_teu ?? 1}
            status={feederStatus}
            detail={feeder ? `${feederBerthLabel} • ${feeder.departure_window?.earliest?.slice(11,16)}–${feeder.departure_window?.latest?.slice(11,16)} • hold $${feeder.hold_cost_per_hour}/hr` : undefined}
            tooltip="Berthed vs conflict (red). Late departure misses Port Klang tidal window → $5k missed connection."
          />
          <SystemStatusCard
            name="Tuas QC"
            awaiting={!qc}
            metric={qc ? `${qc.qc_status.filter((q) => q.status === 'available').length}/${qc.qc_count} cranes` : 'Awaiting ingest'}
            value={qc ? qc.qc_status.filter((q) => q.status === 'available').length : 0}
            max={qc?.qc_count ?? 40}
            status={
              !qc ? 'amber' :
              qc.qc_status.filter((q) => q.status === 'available').length >= qc.qc_count * 0.9 ? 'green' :
              qc.qc_status.some((q) => q.status === 'available') ? 'amber' : 'red'
            }
            detail={qc ? `Berth B-03 • FIFO loading • 30 min to departure` : undefined}
            tooltip="40 QCs at Tuas mega port. Sequence updated per ITT ETAs (road 14:30, sea 16:30)."
          />
        </div>
      </div>
    </div>
  );
}
