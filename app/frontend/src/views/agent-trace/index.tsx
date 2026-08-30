import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { getAgentTrace, getActiveRun, type AgentTraceStep } from '@/api/nexus';
import { ChevronRight, ChevronDown } from 'lucide-react';
import { useSSE, SSEEvent } from '@/hooks/use-sse';
import { useSearchParams } from 'react-router';

const typeColors: Record<string, string> = {
  tool: 'border-l-blue-500',
  hitl: 'border-l-amber-500',
  complete: 'border-l-emerald-500',
  escalation: 'border-l-red-500',
  info: 'border-l-gray-500',
};

const typeBadgeColors: Record<string, string> = {
  tool: 'bg-blue-500/10 text-blue-500',
  hitl: 'bg-amber-500/10 text-amber-500',
  complete: 'bg-emerald-500/10 text-emerald-500',
  escalation: 'bg-red-500/10 text-red-500',
  info: 'bg-gray-500/10 text-gray-500',
};

function formatTime(ts: string) {
  try {
    return new Date(ts).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  } catch {
    return ts;
  }
}

export default function AgentTrace() {
  const [searchParams] = useSearchParams();
  const urlRunId = searchParams.get('run_id');
  const [resolvedRunId, setResolvedRunId] = useState<string | null>(urlRunId);
  const runId = urlRunId || resolvedRunId;
  const [steps, setSteps] = useState<AgentTraceStep[]>([]);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [newestFirst, setNewestFirst] = useState(true);

  // Resolve run_id from active-run API if not in URL
  useEffect(() => {
    if (!urlRunId) {
      getActiveRun()
        .then((active) => { if (active.run_id) setResolvedRunId(active.run_id); })
        .catch(() => {});
    }
  }, [urlRunId]);

  useEffect(() => {
    if (runId) {
      getAgentTrace(runId)
        .then(setSteps)
        .catch(() => {});
    }
  }, [runId]);

  useSSE(runId, (event: SSEEvent) => {
    if (event.event === 'trace_entry') {
      // Skip show_card trace entries — hitl_card SSE handles those
      if (event.data.node === 'hitl' && event.data.action === 'show_card') return;
      setSteps((prev) => [
        ...prev,
        {
          step: prev.length + 1,
          action: (event.data.action as string) || `${(event.data.node as string)||''}:${(event.data.action as string)||''}`,
          timestamp: event.timestamp,
          detail: JSON.stringify(event.data.result || event.data, null, 2).slice(0,1200),
          type: (event.data.type as AgentTraceStep['type']) || (event.data.node === 'tool' ? 'tool' : event.data.node === 'hitl' ? 'hitl' : event.data.node === 'escalation' ? 'escalation' : 'info'),
        },
      ]);
    }
  });

  function toggleExpand(stepNum: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(stepNum)) {
        next.delete(stepNum);
      } else {
        next.add(stepNum);
      }
      return next;
    });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold tracking-tight">Agent Trace</h1>
        {runId && (
          <Badge variant="secondary" className="text-[10px]">
            Run: {runId}
          </Badge>
        )}
      </div>

      {!runId && (
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-sm text-muted-foreground">
              No active run. Start a demo from the dashboard or provide a run_id
              as a query parameter.
            </p>
          </CardContent>
        </Card>
      )}

      {runId && steps.length === 0 && (
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-sm text-muted-foreground">
              Waiting for trace events...
            </p>
          </CardContent>
        </Card>
      )}

      {steps.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Trace ({steps.length} steps)</CardTitle>
              <Button variant="ghost" size="sm" className="h-6 text-xs gap-1" onClick={()=>setNewestFirst(v=>!v)}>{newestFirst ? 'Newest first ↓' : 'Oldest first ↑'}</Button>
            </div>
            <p className="text-xs text-muted-foreground">Full tool JSON — Agent Output is the human summary.</p>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[calc(100vh-200px)]">
              <div className="space-y-2">
                {(newestFirst ? [...steps].reverse() : steps).map((step) => (
                  <div
                    key={step.step}
                    className={`border-l-2 ${typeColors[step.type] || typeColors.info} pl-3`}
                  >
                    <button
                      onClick={() => toggleExpand(step.step)}
                      className="flex w-full items-center gap-2 text-left"
                    >
                      {expanded.has(step.step) ? (
                        <ChevronDown size={14} />
                      ) : (
                        <ChevronRight size={14} />
                      )}
                      <span className="text-xs font-mono text-muted-foreground w-6">
                        {step.step}
                      </span>
                      <span className="text-sm font-medium flex-1">
                        {step.action}
                      </span>
                      <Badge
                        variant="secondary"
                        className={`text-[10px] ${typeBadgeColors[step.type] || ''}`}
                      >
                        {step.type}
                      </Badge>
                      <span className="text-[10px] text-muted-foreground">
                        {formatTime(step.timestamp)}
                      </span>
                    </button>
                    {expanded.has(step.step) && step.detail && (
                      <div className="mt-1 ml-8 text-xs text-muted-foreground whitespace-pre-wrap font-mono">
                        {step.detail}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
