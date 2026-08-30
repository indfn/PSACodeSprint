import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { getRunHistory, getRegistry, type RunRecord, type RegistryProblem } from '@/api/nexus';
import { useNavigate } from 'react-router';
import { ChevronRight, ChevronDown } from 'lucide-react';

const FALLBACK_PROBLEM_NAMES: Record<string, string> = {
  'pb-12-itt': 'ITT Coordination',
  'pb-01-berth': 'Berth Reassignment',
};

const statusColors: Record<string, string> = {
  completed: 'bg-emerald-500/10 text-emerald-500',
  running: 'bg-blue-500/10 text-blue-500',
  failed: 'bg-red-500/10 text-red-500',
  pending: 'bg-amber-500/10 text-amber-500',
};

function formatTime(ts: string) {
  try {
    return new Date(ts).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  } catch {
    return ts;
  }
}

function formatDuration(secs?: number) {
  if (!secs) return '—';
  if (secs < 60) return `${secs}s`;
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}m ${s}s`;
}

export default function History() {
  const navigate = useNavigate();
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [problemNames, setProblemNames] = useState<Record<string, string>>(FALLBACK_PROBLEM_NAMES);

  useEffect(() => {
    getRunHistory()
      .then(setRuns)
      .catch(() => {});
    getRegistry()
      .then((res) => {
        if (res.problems) {
          const names: Record<string, string> = {};
          res.problems.forEach((p: RegistryProblem) => {
            names[p.problem_id] = p.name;
          });
          setProblemNames(names);
        }
      })
      .catch(() => {});
  }, []);

  function toggleExpand(runId: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(runId)) {
        next.delete(runId);
      } else {
        next.add(runId);
      }
      return next;
    });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold tracking-tight">Run History</h1>
        <Badge variant="secondary" className="text-[10px]">
          {runs.length} runs
        </Badge>
      </div>

      {runs.length === 0 && (
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-sm text-muted-foreground">
              No runs yet. Start a demo from the dashboard.
            </p>
          </CardContent>
        </Card>
      )}

      {runs.length > 0 && (
        <ScrollArea className="h-[calc(100vh-160px)]">
          <div className="space-y-2">
            {runs.map((run) => (
              <Card key={run.run_id} size="sm">
                <CardHeader className="pb-1">
                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => toggleExpand(run.run_id)}
                      className="flex items-center gap-2 text-left"
                    >
                      {expanded.has(run.run_id) ? (
                        <ChevronDown size={14} />
                      ) : (
                        <ChevronRight size={14} />
                      )}
                      <CardTitle className="text-sm font-medium">
                        {problemNames[run.problem_id] || run.problem_id}
                      </CardTitle>
                    </button>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="secondary"
                        className={`text-[10px] ${statusColors[run.status] || ''}`}
                      >
                        {run.status}
                      </Badge>
                      <span className="text-[10px] text-muted-foreground">
                        {formatTime(run.started_at)}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {formatDuration(run.duration_seconds)}
                      </span>
                    </div>
                  </div>
                </CardHeader>

                {expanded.has(run.run_id) && (
                  <CardContent className="pt-0">
                    <div className="space-y-1 text-xs font-mono">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Run ID</span>
                        <span>{run.run_id}</span>
                      </div>
                      {run.scenario && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Scenario</span>
                          <span>{problemNames[run.problem_id] || run.problem_id} · {run.scenario}</span>
                        </div>
                      )}
                      {run.summary && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Summary</span>
                          <span className="text-right max-w-[60%]">
                            {run.summary}
                          </span>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => navigate(`/trace?run_id=${run.run_id}`)}
                      className="mt-2 text-xs text-primary hover:underline"
                    >
                      View full trace →
                    </button>
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
