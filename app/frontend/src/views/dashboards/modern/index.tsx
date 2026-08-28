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
import { Play, RotateCcw, Zap } from 'lucide-react';
import SystemStatusCard from '@/components/nexus/SystemStatusCard';
import AgentOutput, { AgentEvent } from '@/components/nexus/AgentOutput';
import HitlCard, { HitlGateInfo } from '@/components/nexus/HitlCard';
import CostBreakdown from '@/components/nexus/CostBreakdown';
import { useSSE, SSEEvent } from '@/hooks/use-sse';
import {
  startDemo,
  getContainerData,
  getTruckData,
  getFeederData,
  resetMocks,
  getActiveProblem,
  injectEdgeCase,
  type ContainerData,
  type TruckData,
  type FeederData,
} from '@/api/nexus';

const PROBLEMS = [
  { id: 'pb-12-itt', name: 'ITT Coordination' },
  { id: 'pb-01-berth', name: 'Berth Reassignment' },
];

const SCENARIOS = [
  { id: 'nominal', name: 'Nominal' },
  { id: 'deviation', name: 'Deviation' },
  { id: 'stale', name: 'Stale Data' },
  { id: 'escalation', name: 'Escalation' },
];

export default function NexusDashboard() {
  const [activeProblem, setActiveProblem] = useState(PROBLEMS[0].id);
  const [scenario, setScenario] = useState(SCENARIOS[0].id);
  const [runId, setRunId] = useState<string | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [hitlGate, setHitlGate] = useState<HitlGateInfo | null>(null);

  const [containers, setContainers] = useState<ContainerData | null>(null);
  const [trucks, setTrucks] = useState<TruckData | null>(null);
  const [feeder, setFeeder] = useState<FeederData | null>(null);

  const [costData, setCostData] = useState({
    roadCost: 0,
    seaHandling: 0,
    total: 0,
    baseline: 0,
    alternatives: [] as string[],
  });

  const [loading, setLoading] = useState(false);
  const [edgeLoading, setEdgeLoading] = useState<string | null>(null);

  // Load initial data
  useEffect(() => {
    getActiveProblem()
      .then((p) => setActiveProblem(p.problem_id))
      .catch(() => {});
    getContainerData().then(setContainers).catch(() => {});
    getTruckData().then(setTrucks).catch(() => {});
    getFeederData().then(setFeeder).catch(() => {});
  }, []);

  // SSE event handler
  const handleSSEEvent = useCallback(
    (event: SSEEvent) => {
      const ts = event.timestamp || new Date().toISOString();
      const data = event.data;

      switch (event.event) {
        case 'trace_entry':
          setEvents((prev) => [
            ...prev,
            {
              timestamp: ts,
              message: (data.message as string) || (data.action as string) || JSON.stringify(data),
            },
          ]);
          break;

        case 'hitl_request':
          setHitlGate({
            gate_id: (data.gate_id as string) || '',
            gate_name: (data.gate_name as string) || 'Approval Required',
            data: (data.decision_data as Record<string, unknown>) || data,
          });
          break;

        case 'hitl_resolved':
          setHitlGate(null);
          break;

        case 'cost_update':
          setCostData({
            roadCost: (data.road_cost as number) || 0,
            seaHandling: (data.sea_handling as number) || 0,
            total: (data.total as number) || 0,
            baseline: (data.baseline as number) || 0,
            alternatives: (data.alternatives as string[]) || [],
          });
          break;

        case 'run_complete':
          setEvents((prev) => [
            ...prev,
            { timestamp: ts, message: 'Run complete.' },
          ]);
          break;

        case 'system_status':
          // Refresh system status cards
          getContainerData().then(setContainers).catch(() => {});
          getTruckData().then(setTrucks).catch(() => {});
          getFeederData().then(setFeeder).catch(() => {});
          break;

        default:
          setEvents((prev) => [
            ...prev,
            {
              timestamp: ts,
              message:
                (data.message as string) ||
                `[${event.event}] ${JSON.stringify(data)}`,
            },
          ]);
      }
    },
    []
  );

  useSSE(runId, handleSSEEvent);

  async function handleStartDemo() {
    setLoading(true);
    setEvents([]);
    setHitlGate(null);
    try {
      const res = await startDemo(scenario, activeProblem);
      setRunId(res.run_id);
      setEvents((prev) => [
        ...prev,
        {
          timestamp: new Date().toISOString(),
          message: `Demo started. Run ID: ${res.run_id}`,
        },
      ]);
    } catch (err) {
      console.error('Failed to start demo:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleReset() {
    await resetMocks();
    setRunId(null);
    setEvents([]);
    setHitlGate(null);
    getContainerData().then(setContainers).catch(() => {});
    getTruckData().then(setTrucks).catch(() => {});
    getFeederData().then(setFeeder).catch(() => {});
  }

  async function handleEdgeCase(caseType: string) {
    setEdgeLoading(caseType);
    try {
      await injectEdgeCase(caseType);
      setEvents((prev) => [
        ...prev,
        { timestamp: new Date().toISOString(), message: `Edge case injected: ${caseType}` },
      ]);
      getContainerData().then(setContainers).catch(() => {});
      getTruckData().then(setTrucks).catch(() => {});
      getFeederData().then(setFeeder).catch(() => {});
    } catch (err) {
      console.error('Edge case injection failed:', err);
    } finally {
      setEdgeLoading(null);
    }
  }

  const containerStatus =
    containers && containers.total_containers > 0
      ? containers.data_age_minutes < 10
        ? 'green'
        : 'amber'
      : 'green';
  const truckStatus = trucks
    ? trucks.available_trucks > trucks.total_fleet * 0.3
      ? 'green'
      : 'amber'
    : 'green';
  const feederStatus = feeder
    ? feeder.berth_status.includes('berthed')
      ? 'green'
      : feeder.berth_status === 'conflict'
      ? 'red'
      : 'amber'
    : 'green';

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold tracking-tight">Nexus Dashboard</h1>
          <Select value={activeProblem} onValueChange={(v) => v && setActiveProblem(v)}>
            <SelectTrigger className="h-8 w-[180px]">
              <SelectValue placeholder="Select problem">
                {PROBLEMS.find((p) => p.id === activeProblem)?.name}
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              {PROBLEMS.map((p) => (
                <SelectItem key={p.id} value={p.id}>
                  {p.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-[10px]">
            Confidence: 92%
          </Badge>
          <Badge variant="outline" className="text-[10px]">
            Risk: Low
          </Badge>
        </div>
      </div>

      {/* Action bar */}
      <div className="flex flex-wrap items-center gap-2">
        <Button
          size="sm"
          disabled={loading}
          onClick={handleStartDemo}
          className="gap-1.5"
        >
          <Play size={14} />
          {loading ? 'Starting...' : 'Start Demo'}
        </Button>
        <Select value={scenario} onValueChange={(v) => v && setScenario(v)}>
          <SelectTrigger className="h-8 w-[130px]">
            <SelectValue placeholder="Scenario">
              {SCENARIOS.find((s) => s.id === scenario)?.name}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {SCENARIOS.map((s) => (
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
          disabled={!!edgeLoading}
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

      {/* Main content */}
      <div className="grid grid-cols-12 gap-4">
        {/* Left column: HITL + Agent output */}
        <div className="col-span-12 lg:col-span-8 space-y-4">
          <HitlCard
            gate={hitlGate}
            runId={runId || ''}
            onResponded={() => setHitlGate(null)}
          />

          <AgentOutput events={events} />
        </div>

        {/* Right column: Status cards + Cost */}
        <div className="col-span-12 lg:col-span-4 space-y-3">
          <SystemStatusCard
            name="CITOS PPT"
            metric={`${containers?.total_containers ?? 0} containers`}
            value={containers?.total_containers ?? 0}
            max={120}
            status={containerStatus}
          />
          <SystemStatusCard
            name="OptETruck"
            metric={`${trucks?.available_trucks ?? 0} / ${trucks?.total_fleet ?? 0} trucks`}
            value={trucks?.available_trucks ?? 0}
            max={trucks?.total_fleet ?? 1}
            status={truckStatus}
          />
          <SystemStatusCard
            name="Feeder"
            metric={`${feeder?.current_occupancy_teu ?? 0} / ${feeder?.capacity_teu ?? 1} TEU`}
            value={feeder?.current_occupancy_teu ?? 0}
            max={feeder?.capacity_teu ?? 1}
            status={feederStatus}
          />
          <SystemStatusCard
            name="Tuas QC"
            metric="Operational"
            value={100}
            max={100}
            status="green"
          />

          <CostBreakdown
            roadCost={costData.roadCost}
            seaHandling={costData.seaHandling}
            total={costData.total}
            baseline={costData.baseline}
            alternatives={costData.alternatives}
          />
        </div>
      </div>
    </div>
  );
}
