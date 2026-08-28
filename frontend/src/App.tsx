import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Bell,
  Settings,
  ExternalLink,
  Play,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Zap,
  MessageSquare,
  Filter,
  RotateCcw,
  Loader2,
} from "lucide-react";

// ─── Types ──────────────────────────────────────────────────────────────────

interface ProblemInfo {
  id: string;
  label: string;
  systems: string[];
}

interface Scenario {
  id: string;
  label: string;
  description: string;
}

interface SystemData {
  name: string;
  metrics: Record<string, string | number>;
  progress: number;
  status: "green" | "amber" | "red";
}

interface AgentEvent {
  type: string;
  message: string;
  timestamp: string;
  data?: Record<string, unknown>;
}

interface TraceStep {
  step: number;
  action: string;
  timestamp: string;
  detail: string;
  type: "tool" | "hitl" | "complete" | "escalation";
}

interface RunRecord {
  run_id: string;
  status: string;
  scenario: string;
  timestamp: string;
  duration?: string;
}

interface HitlCard {
  gate_id: string;
  gate_label: string;
  decision_data: {
    road_cost?: number;
    sea_cost?: number;
    total_cost?: number;
    split?: string;
    alternatives?: Array<{ label: string; cost: number }>;
  };
}

// ─── Constants ──────────────────────────────────────────────────────────────

const PROBLEMS: ProblemInfo[] = [
  { id: "pb-12-itt", label: "ITT Coordination", systems: ["CITOS PPT", "OptETruck", "Feeder", "Tuas QC"] },
  { id: "pb-01-berth", label: "Berth Reassignment", systems: ["Berth System", "Vessel Tracker", "PortNet"] },
];

const SCENARIOS: Scenario[] = [
  { id: "nominal", label: "Nominal", description: "Standard operations" },
  { id: "deviation", label: "Deviation", description: "Schedule deviation" },
  { id: "stale", label: "Stale", description: "Stale data detected" },
  { id: "escalation", label: "Escalation", description: "Requires escalation" },
];

// ─── Utility Components ─────────────────────────────────────────────────────

function StatusDot({ status }: { status: "green" | "amber" | "red" }) {
  const colors = {
    green: "bg-emerald-500",
    amber: "bg-amber-500",
    red: "bg-red-500",
  };
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${colors[status]}`}
    />
  );
}

function ProgressBar({ value }: { value: number }) {
  return (
    <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
      <div
        className="h-full bg-blue-500 transition-all duration-500"
        style={{ width: `${Math.min(100, value)}%` }}
      />
    </div>
  );
}

// ─── System Cards ───────────────────────────────────────────────────────────

function SystemCard({ data }: { data: SystemData }) {
  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardContent className="p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-zinc-400">{data.name}</span>
          <StatusDot status={data.status} />
        </div>
        <div className="grid grid-cols-2 gap-1.5 mb-2">
          {Object.entries(data.metrics).map(([key, value]) => (
            <div key={key}>
              <span className="text-[10px] text-zinc-500 block">{key}</span>
              <span className="text-sm font-mono text-zinc-200">{value}</span>
            </div>
          ))}
        </div>
        <ProgressBar value={data.progress} />
      </CardContent>
    </Card>
  );
}

// ─── Agent Output ───────────────────────────────────────────────────────────

function AgentOutput({ events }: { events: AgentEvent[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="p-3 pb-2">
        <CardTitle className="text-sm font-medium text-zinc-400 flex items-center gap-2">
          <Zap className="w-3.5 h-3.5" />
          Agent Output
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3 pt-0">
        <ScrollArea className="h-48">
          <div ref={scrollRef} className="space-y-2 pr-4">
            {events.length === 0 ? (
              <p className="text-xs text-zinc-600">No agent activity yet...</p>
            ) : (
              events.map((event, i) => (
                <div key={i} className="text-xs">
                  <span className="text-zinc-600 font-mono">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="text-zinc-400 ml-2">{event.message}</span>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

// ─── HITL Card ──────────────────────────────────────────────────────────────

function HitlCard({
  card,
  onRespond,
}: {
  card: HitlCard;
  onRespond: (decision: string, reason?: string) => void;
}) {
  const [showReject, setShowReject] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [showModify, setShowModify] = useState(false);
  const [modifications, setModifications] = useState<Record<string, string>>({});

  if (!card) return null;

  return (
    <Card className="bg-zinc-900 border-zinc-800 border-amber-500/30">
      <CardHeader className="p-3 pb-2">
        <CardTitle className="text-sm font-medium text-amber-500 flex items-center gap-2">
          <MessageSquare className="w-3.5 h-3.5" />
          HITL Approval — {card.gate_label}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3 pt-0 space-y-3">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-zinc-500 block">Road Cost</span>
            <span className="font-mono text-zinc-200">
              ${card.decision_data.road_cost?.toLocaleString() ?? "—"}
            </span>
          </div>
          <div>
            <span className="text-zinc-500 block">Sea Cost</span>
            <span className="font-mono text-zinc-200">
              ${card.decision_data.sea_cost?.toLocaleString() ?? "—"}
            </span>
          </div>
          <div>
            <span className="text-zinc-500 block">Total</span>
            <span className="font-mono text-zinc-200">
              ${card.decision_data.total_cost?.toLocaleString() ?? "—"}
            </span>
          </div>
          <div>
            <span className="text-zinc-500 block">Split</span>
            <span className="font-mono text-zinc-200">
              {card.decision_data.split ?? "—"}
            </span>
          </div>
        </div>

        {card.decision_data.alternatives && card.decision_data.alternatives.length > 0 && (
          <div>
            <span className="text-[10px] text-zinc-500 block mb-1">Alternatives</span>
            {card.decision_data.alternatives.map((alt, i) => (
              <div key={i} className="flex justify-between text-xs">
                <span className="text-zinc-400">{alt.label}</span>
                <span className="font-mono text-zinc-300">${alt.cost.toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}

        <Separator className="bg-zinc-800" />

        {!showReject && !showModify && (
          <div className="flex gap-2">
            <Button
              size="sm"
              className="flex-1 bg-emerald-600 hover:bg-emerald-700"
              onClick={() => onRespond("approve")}
            >
              <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
              Approve
            </Button>
            <Button
              size="sm"
              variant="destructive"
              className="flex-1"
              onClick={() => setShowReject(true)}
            >
              <XCircle className="w-3.5 h-3.5 mr-1" />
              Reject
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="flex-1"
              onClick={() => setShowModify(true)}
            >
              <Settings className="w-3.5 h-3.5 mr-1" />
              Modify
            </Button>
          </div>
        )}

        {showReject && (
          <div className="space-y-2">
            <textarea
              className="w-full h-16 bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-200 resize-none focus:outline-none focus:border-red-500"
              placeholder="Rejection reason..."
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
            />
            <div className="flex gap-2">
              <Button size="sm" variant="destructive" onClick={() => { onRespond("reject", rejectReason); setShowReject(false); }}>
                Confirm Reject
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setShowReject(false)}>
                Cancel
              </Button>
            </div>
          </div>
        )}

        {showModify && (
          <div className="space-y-2">
            <input
              className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-200 focus:outline-none focus:border-blue-500"
              placeholder="Road cost override"
              value={modifications.road_cost || ""}
              onChange={(e) => setModifications({ ...modifications, road_cost: e.target.value })}
            />
            <input
              className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-200 focus:outline-none focus:border-blue-500"
              placeholder="Sea cost override"
              value={modifications.sea_cost || ""}
              onChange={(e) => setModifications({ ...modifications, sea_cost: e.target.value })}
            />
            <div className="flex gap-2">
              <Button size="sm" onClick={() => { onRespond("modify", JSON.stringify(modifications)); setShowModify(false); }}>
                Submit Modify
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setShowModify(false)}>
                Cancel
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Cost Breakdown ─────────────────────────────────────────────────────────

function CostBreakdown({ data }: { data: HitlCard["decision_data"] }) {
  const baseline = (data.road_cost ?? 0) + (data.sea_cost ?? 0);
  const savings = baseline - (data.total_cost ?? baseline);

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="p-3 pb-2">
        <CardTitle className="text-sm font-medium text-zinc-400">Cost Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="p-3 pt-0">
        <div className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-zinc-500">Road transport</span>
            <span className="font-mono text-zinc-200">${data.road_cost?.toLocaleString() ?? "—"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-zinc-500">Sea transport</span>
            <span className="font-mono text-zinc-200">${data.sea_cost?.toLocaleString() ?? "—"}</span>
          </div>
          <Separator className="bg-zinc-800" />
          <div className="flex justify-between">
            <span className="text-zinc-500">Total</span>
            <span className="font-mono text-zinc-200">${data.total_cost?.toLocaleString() ?? "—"}</span>
          </div>
          {savings > 0 && (
            <div className="flex justify-between">
              <span className="text-emerald-500">Savings vs baseline</span>
              <span className="font-mono text-emerald-500">${savings.toLocaleString()}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Agent Trace Tab ────────────────────────────────────────────────────────

function AgentTrace({ steps }: { steps: TraceStep[] }) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const toggle = (n: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(n)) next.delete(n);
      else next.add(n);
      return next;
    });
  };

  const typeColors: Record<string, string> = {
    tool: "border-blue-500",
    hitl: "border-amber-500",
    complete: "border-emerald-500",
    escalation: "border-red-500",
  };

  const typeIcons: Record<string, React.ReactNode> = {
    tool: <Zap className="w-3 h-3 text-blue-500" />,
    hitl: <MessageSquare className="w-3 h-3 text-amber-500" />,
    complete: <CheckCircle2 className="w-3 h-3 text-emerald-500" />,
    escalation: <AlertTriangle className="w-3 h-3 text-red-500" />,
  };

  return (
    <div className="space-y-1">
      {steps.length === 0 ? (
        <p className="text-xs text-zinc-600">No trace data available.</p>
      ) : (
        steps.map((step) => (
          <div
            key={step.step}
            className={`border-l-2 ${typeColors[step.type]} pl-3 py-1.5 cursor-pointer hover:bg-zinc-900 rounded-r`}
            onClick={() => toggle(step.step)}
          >
            <div className="flex items-center gap-2">
              {expanded.has(step.step) ? (
                <ChevronDown className="w-3 h-3 text-zinc-500" />
              ) : (
                <ChevronRight className="w-3 h-3 text-zinc-500" />
              )}
              {typeIcons[step.type]}
              <span className="text-xs text-zinc-300 font-medium">
                Step {step.step}
              </span>
              <span className="text-xs text-zinc-500">{step.action}</span>
              <span className="text-[10px] text-zinc-600 font-mono ml-auto">
                {new Date(step.timestamp).toLocaleTimeString()}
              </span>
            </div>
            {expanded.has(step.step) && (
              <div className="mt-1 ml-8 text-xs text-zinc-400 bg-zinc-950 rounded p-2 font-mono">
                {step.detail}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}

// ─── History Tab ────────────────────────────────────────────────────────────

function HistoryPanel({ runs }: { runs: RunRecord[] }) {
  const [expandedRun, setExpandedRun] = useState<string | null>(null);

  const statusBadge = (s: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      completed: "default",
      waiting_hitl: "outline",
      failed: "destructive",
    };
    return <Badge variant={variants[s] || "secondary"} className="text-[10px]">{s}</Badge>;
  };

  return (
    <div className="space-y-2">
      {runs.length === 0 ? (
        <p className="text-xs text-zinc-600">No runs yet. Click "Run Demo" to start.</p>
      ) : (
        runs.map((run) => (
          <Card
            key={run.run_id}
            className="bg-zinc-900 border-zinc-800 cursor-pointer hover:border-zinc-700 transition-colors"
            onClick={() => setExpandedRun(expandedRun === run.run_id ? null : run.run_id)}
          >
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {expandedRun === run.run_id ? (
                    <ChevronDown className="w-3 h-3 text-zinc-500" />
                  ) : (
                    <ChevronRight className="w-3 h-3 text-zinc-500" />
                  )}
                  <span className="text-xs font-mono text-zinc-300">
                    {run.run_id.slice(0, 12)}...
                  </span>
                  {statusBadge(run.status)}
                </div>
                <div className="flex items-center gap-3 text-[10px] text-zinc-500">
                  <Badge variant="secondary" className="text-[10px]">{run.scenario}</Badge>
                  <span>{run.timestamp}</span>
                  {run.duration && <span>{run.duration}</span>}
                </div>
              </div>
              {expandedRun === run.run_id && (
                <div className="mt-2 pt-2 border-t border-zinc-800">
                  <p className="text-[10px] text-zinc-500 font-mono">{JSON.stringify(run, null, 2)}</p>
                </div>
              )}
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}

// ─── Edge Injection Sidebar ─────────────────────────────────────────────────

function EdgeInjectionSidebar({
  onInject,
  onReset,
}: {
  onInject: (edgeCase: string) => void;
  onReset: () => void;
}) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm" className="h-8 text-zinc-400">
          <Filter className="w-4 h-4 mr-1" />
          Edge Cases
        </Button>
      </SheetTrigger>
      <SheetContent className="bg-zinc-950 border-zinc-800">
        <SheetHeader>
          <SheetTitle className="text-zinc-200">Edge Injection</SheetTitle>
        </SheetHeader>
        <div className="mt-4 space-y-2">
          <Button
            variant="outline"
            className="w-full justify-start"
            onClick={() => onInject("feeder_berth_conflict")}
          >
            <AlertTriangle className="w-4 h-4 mr-2 text-amber-500" />
            Feeder Berth Conflict
          </Button>
          <Button
            variant="outline"
            className="w-full justify-start"
            onClick={() => onInject("stale_data")}
          >
            <Clock className="w-4 h-4 mr-2 text-amber-500" />
            Stale Data
          </Button>
          <Separator className="bg-zinc-800 my-4" />
          <Button
            variant="outline"
            className="w-full justify-start"
            onClick={onReset}
          >
            <RotateCcw className="w-4 h-4 mr-2 text-zinc-400" />
            Reset Mocks
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}

// ─── Main App ───────────────────────────────────────────────────────────────

function App() {
  const [problem, setProblem] = useState(PROBLEMS[0].id);
  const [scenario, setScenario] = useState("nominal");
  const [activeTab, setActiveTab] = useState("dashboard");
  const [isRunning, setIsRunning] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [agentEvents, setAgentEvents] = useState<AgentEvent[]>([]);
  const [hitlCard, setHitlCard] = useState<HitlCard | null>(null);
  const [traceSteps, setTraceSteps] = useState<TraceStep[]>([]);
  const [runHistory, setRunHistory] = useState<RunRecord[]>([]);
  const [systemData, setSystemData] = useState<SystemData[]>([
    { name: "CITOS PPT", metrics: { Containers: "—", Blocks: "—" }, progress: 0, status: "green" },
    { name: "OptETruck", metrics: { Trucks: "—", Capacity: "—" }, progress: 0, status: "green" },
    { name: "Feeder", metrics: { Vessel: "—", ETA: "—" }, progress: 0, status: "green" },
    { name: "Tuas QC", metrics: { Ready: "—", DG: "—" }, progress: 0, status: "green" },
  ]);
  const [notifications, setNotifications] = useState<string[]>([]);

  const eventSourceRef = useRef<EventSource | null>(null);

  // Fetch system data
  const fetchSystemData = useCallback(async () => {
    try {
      const [containers, trucks, feeder] = await Promise.all([
        fetch("/api/citos/ppt/containers").then((r) => r.json()),
        fetch("/api/optetruck/capacity").then((r) => r.json()),
        fetch("/api/feeder/FEEDER%20ATLANTIC-03").then((r) => r.json()),
      ]);

      setSystemData([
        {
          name: "CITOS PPT",
          metrics: {
            Containers: containers.total_containers ?? "—",
            Blocks: containers.blocks_affected?.length ?? "—",
          },
          progress: ((containers.total_containers ?? 0) / 200) * 100,
          status: "green",
        },
        {
          name: "OptETruck",
          metrics: {
            Trucks: trucks.available_trucks ?? "—",
            Capacity: `${trucks.utilization_pct ?? 0}%`,
          },
          progress: trucks.utilization_pct ?? 0,
          status: (trucks.utilization_pct ?? 0) > 85 ? "amber" : "green",
        },
        {
          name: "Feeder",
          metrics: {
            Vessel: feeder.vessel_id ?? "—",
            ETA: feeder.eta ?? "—",
          },
          progress: feeder.progress_pct ?? 45,
          status: "green",
        },
        {
          name: "Tuas QC",
          metrics: {
            Ready: feeder.containers_ready ?? "—",
            DG: feeder.dg_containers ?? "—",
          },
          progress: feeder.qc_utilization ?? 60,
          status: "green",
        },
      ]);
    } catch {
      // API not available yet
    }
  }, []);

  useEffect(() => {
    fetchSystemData();
  }, [fetchSystemData]);

  // SSE connection
  useEffect(() => {
    if (!runId) return;

    const es = new EventSource(`/agent/stream/${runId}`);
    eventSourceRef.current = es;

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        setAgentEvents((prev) => [
          ...prev,
          {
            type: data.type ?? "message",
            message: data.message ?? data.thinking ?? JSON.stringify(data),
            timestamp: new Date().toISOString(),
            data,
          },
        ]);

        if (data.type === "hitl_required" || data.hitl_card) {
          setHitlCard(data.hitl_card ?? data);
          setActiveTab("dashboard");
        }

        if (data.type === "completed" || data.status === "completed") {
          setIsRunning(false);
          setNotifications((prev) => [...prev, `Run ${runId} completed`]);
        }
      } catch {
        // Non-JSON event
      }
    };

    es.onerror = () => {
      es.close();
      eventSourceRef.current = null;
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [runId]);

  // Run demo
  const handleRun = async () => {
    setIsRunning(true);
    setAgentEvents([]);
    setHitlCard(null);
    setTraceSteps([]);

    try {
      const res = await fetch("/agent/run-demo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario, problem_id: problem }),
      });
      const data = await res.json();
      setRunId(data.run_id);
      setRunHistory((prev) => [
        {
          run_id: data.run_id,
          status: data.status ?? "running",
          scenario,
          timestamp: new Date().toLocaleTimeString(),
        },
        ...prev,
      ]);
    } catch (err) {
      console.error("Run failed:", err);
      setIsRunning(false);
    }
  };

  // HITL response
  const handleHitlResponse = async (decision: string, reason?: string) => {
    if (!runId || !hitlCard) return;

    try {
      await fetch("/agent/hitl/respond", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          run_id: runId,
          decision,
          gate_id: hitlCard.gate_id,
          reason,
        }),
      });
      setHitlCard(null);
    } catch (err) {
      console.error("HITL respond failed:", err);
    }
  };

  // Edge injection
  const handleEdgeInjection = async (edgeCase: string) => {
    try {
      await fetch("/agent/inject-edge-case", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case: edgeCase, run_id: runId ?? undefined }),
      });
      setNotifications((prev) => [...prev, `Injected: ${edgeCase}`]);
    } catch (err) {
      console.error("Injection failed:", err);
    }
  };

  // Reset mocks
  const handleResetMocks = async () => {
    try {
      await fetch("/agent/reset-mocks", { method: "POST" });
      setNotifications((prev) => [...prev, "Mocks reset"]);
    } catch (err) {
      console.error("Reset failed:", err);
    }
  };

  // Fetch trace
  const fetchTrace = async () => {
    if (!runId) return;
    try {
      const res = await fetch(`/agent/trace/${runId}`);
      const data = await res.json();
      if (data.steps) {
        setTraceSteps(data.steps);
      }
    } catch {
      // Trace not available
    }
  };

  useEffect(() => {
    if (activeTab === "trace") fetchTrace();
  }, [activeTab, runId]);

  const currentProblem = PROBLEMS.find((p) => p.id === problem) ?? PROBLEMS[0];

  return (
    <div className="min-h-screen bg-black text-zinc-100">
      {/* ─── Header ─────────────────────────────────────────────────── */}
      <header className="border-b border-zinc-800 bg-zinc-950">
        <div className="max-w-7xl mx-auto px-4 h-12 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-sm font-bold tracking-wider text-zinc-100">
              PSA NEXUS
            </h1>
            <Separator orientation="vertical" className="h-5 bg-zinc-800" />
            <Select value={problem} onValueChange={setProblem}>
              <SelectTrigger className="w-48 h-8 text-xs bg-zinc-900 border-zinc-800">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-800">
                {PROBLEMS.map((p) => (
                  <SelectItem key={p.id} value={p.id} className="text-xs">
                    {p.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-[10px] font-mono">
              Confidence: 0.92
            </Badge>
            <Badge variant="outline" className="text-[10px] font-mono">
              Risk: Low
            </Badge>
            <Separator orientation="vertical" className="h-5 bg-zinc-800" />

            <Select value={scenario} onValueChange={setScenario}>
              <SelectTrigger className="w-28 h-8 text-xs bg-zinc-900 border-zinc-800">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-800">
                {SCENARIOS.map((s) => (
                  <SelectItem key={s.id} value={s.id} className="text-xs">
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button
              size="sm"
              className="h-8"
              onClick={handleRun}
              disabled={isRunning}
            >
              {isRunning ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5" />
              )}
              <span className="ml-1 text-xs">Run Demo</span>
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0 relative">
                  <Bell className="w-4 h-4" />
                  {notifications.length > 0 && (
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full text-[8px] flex items-center justify-center">
                      {notifications.length}
                    </span>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="bg-zinc-900 border-zinc-800 w-64" align="end">
                <DropdownMenuLabel className="text-xs text-zinc-400">
                  Notifications
                </DropdownMenuLabel>
                <DropdownMenuSeparator className="bg-zinc-800" />
                {notifications.length === 0 ? (
                  <DropdownMenuItem className="text-xs text-zinc-600">
                    No notifications
                  </DropdownMenuItem>
                ) : (
                  notifications.slice(-5).reverse().map((n, i) => (
                    <DropdownMenuItem key={i} className="text-xs text-zinc-300">
                      {n}
                    </DropdownMenuItem>
                  ))
                )}
              </DropdownMenuContent>
            </DropdownMenu>

            <Button
              variant="ghost"
              size="sm"
              className="h-8"
              onClick={() => window.open("/admin", "_blank")}
            >
              <Settings className="w-4 h-4 mr-1" />
              <span className="text-xs">Admin</span>
              <ExternalLink className="w-3 h-3 ml-1 text-zinc-500" />
            </Button>

            <EdgeInjectionSidebar
              onInject={handleEdgeInjection}
              onReset={handleResetMocks}
            />
          </div>
        </div>
      </header>

      {/* ─── Tab Bar ────────────────────────────────────────────────── */}
      <div className="border-b border-zinc-800 bg-zinc-950">
        <div className="max-w-7xl mx-auto px-4">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="h-10 bg-transparent border-0 p-0">
              <TabsTrigger
                value="dashboard"
                className="h-10 rounded-none border-b-2 border-transparent data-[state=active]:border-blue-500 data-[state=active]:bg-transparent text-xs"
              >
                Dashboard
              </TabsTrigger>
              <TabsTrigger
                value="trace"
                className="h-10 rounded-none border-b-2 border-transparent data-[state=active]:border-blue-500 data-[state=active]:bg-transparent text-xs"
              >
                Agent Trace
              </TabsTrigger>
              <TabsTrigger
                value="history"
                className="h-10 rounded-none border-b-2 border-transparent data-[state=active]:border-blue-500 data-[state=active]:bg-transparent text-xs"
              >
                History
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </div>

      {/* ─── Content ────────────────────────────────────────────────── */}
      <main className="max-w-7xl mx-auto px-4 py-4">
        {/* Top strip */}
        <div className="flex items-center gap-3 mb-4">
          <h2 className="text-sm font-medium text-zinc-200">
            {currentProblem.label}
          </h2>
          <Separator orientation="vertical" className="h-4 bg-zinc-800" />
          <div className="flex gap-2">
            {currentProblem.systems.map((sys) => (
              <Badge key={sys} variant="secondary" className="text-[10px]">
                {sys}
              </Badge>
            ))}
          </div>
          {isRunning && (
            <Badge variant="outline" className="text-[10px] text-blue-400 ml-auto">
              <Loader2 className="w-3 h-3 animate-spin mr-1" />
              Running...
            </Badge>
          )}
        </div>

        <Tabs value={activeTab}>
          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="mt-0">
            <div className="grid grid-cols-5 gap-4">
              {/* Left column: System cards */}
              <div className="col-span-3">
                <div className="grid grid-cols-2 gap-3">
                  {systemData.map((sys) => (
                    <SystemCard key={sys.name} data={sys} />
                  ))}
                </div>
              </div>

              {/* Right column: Agent + HITL */}
              <div className="col-span-2 space-y-3">
                <AgentOutput events={agentEvents} />
                {hitlCard && (
                  <HitlCard card={hitlCard} onRespond={handleHitlResponse} />
                )}
                {hitlCard && (
                  <CostBreakdown data={hitlCard.decision_data} />
                )}
              </div>
            </div>
          </TabsContent>

          {/* Trace Tab */}
          <TabsContent value="trace" className="mt-0">
            <Card className="bg-zinc-900 border-zinc-800">
              <CardHeader className="p-3 pb-2">
                <CardTitle className="text-sm font-medium text-zinc-400">
                  Execution Trace
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3 pt-0">
                <AgentTrace steps={traceSteps} />
              </CardContent>
            </Card>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history" className="mt-0">
            <HistoryPanel runs={runHistory} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

export default App;
