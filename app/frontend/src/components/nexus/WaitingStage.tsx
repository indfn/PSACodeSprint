import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Radio, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { getRegistry, simulateWebhook, type RegistryProblem } from '@/api/nexus';

interface WaitingStageProps {
  onRunStarted: (runId: string, problemId: string) => void;
}

const statusConfig: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  idle: { icon: <Radio size={14} />, color: 'text-muted-foreground', label: 'Ready' },
  running: { icon: <Loader2 size={14} className="animate-spin" />, color: 'text-amber-500', label: 'Running' },
  completed: { icon: <CheckCircle2 size={14} />, color: 'text-emerald-500', label: 'Completed' },
};

export default function WaitingStage({ onRunStarted }: WaitingStageProps) {
  const [problems, setProblems] = useState<RegistryProblem[]>([]);
  const [activeProblem, setActiveProblem] = useState('');
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchRegistry = useCallback(async () => {
    try {
      const res = await getRegistry();
      setProblems(res.problems);
      setActiveProblem(res.active_problem);
    } catch {
      // Use fallback if registry not available
      setProblems([
        { problem_id: 'pb-12-itt', short_id: 'pb-12', name: 'Multi-Party ITT Coordination Failure', description: 'Move 120 containers PPT→Tuas, optimise road/sea split', status: 'idle' },
        { problem_id: 'pb-01-berth', short_id: 'pb-01', name: 'Berth Reassignment Under Uncertainty', description: 'Reassign vessel to alternate berth under tidal/weather uncertainty', status: 'idle' },
      ]);
    }
  }, []);

  useEffect(() => {
    fetchRegistry();
    const interval = setInterval(fetchRegistry, 5000); // poll every 5s
    return () => clearInterval(interval);
  }, [fetchRegistry]);

  const handleSimulate = async (problemId: string) => {
    setLoading(problemId);
    setError(null);
    try {
      const res = await simulateWebhook(problemId);
      if (res.run_id) {
        onRunStarted(res.run_id, problemId);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trigger webhook');
    } finally {
      setLoading(null);
    }
  };

  const anyRunning = problems.some(p => p.status === 'running');

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
      <div className="w-full max-w-2xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center gap-2">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-sm text-muted-foreground font-medium">System Online</span>
          </div>
          <h2 className="text-lg font-semibold">Problem Registry</h2>
          <p className="text-sm text-muted-foreground">
            Select a problem to simulate a webhook event
          </p>
        </div>

        {/* Problem Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {problems.map((p) => {
            const st = statusConfig[p.status] || statusConfig.idle;
            const isActive = p.problem_id === activeProblem;
            const isRunning = p.status === 'running';
            const isCompleted = p.status === 'completed';
            const isLoading = loading === p.problem_id;

            return (
              <div
                key={p.problem_id}
                className={`rounded-xl border bg-card p-4 space-y-3 transition-all ${
                  isActive ? 'ring-2 ring-primary/40' : ''
                } ${isRunning ? 'border-amber-500/40' : ''} ${isCompleted ? 'border-emerald-500/40' : ''}`}
              >
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-muted-foreground">{p.short_id}</span>
                    <div className={`flex items-center gap-1 ${st.color}`}>
                      {st.icon}
                      <span className="text-[10px] font-medium">{st.label}</span>
                    </div>
                  </div>
                  <h3 className="text-sm font-semibold leading-tight">{p.name}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{p.description}</p>
                </div>

                <Button
                  size="sm"
                  variant={isCompleted ? 'outline' : 'default'}
                  className="w-full text-xs"
                  disabled={isRunning || isLoading || (anyRunning && !isRunning)}
                  onClick={() => handleSimulate(p.problem_id)}
                >
                  {isLoading ? (
                    <>
                      <Loader2 size={12} className="mr-1 animate-spin" />
                      Triggering...
                    </>
                  ) : isRunning ? (
                    'Running...'
                  ) : isCompleted ? (
                    'Re-run'
                  ) : (
                    'Simulate Webhook'
                  )}
                </Button>
              </div>
            );
          })}
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 text-xs text-red-500 justify-center">
            <AlertCircle size={12} />
            <span>{error}</span>
          </div>
        )}

        {/* Status summary */}
        <div className="flex items-center justify-center gap-4 text-[10px] text-muted-foreground">
          <span>{problems.filter(p => p.status === 'idle').length} ready</span>
          <span>·</span>
          <span>{problems.filter(p => p.status === 'running').length} running</span>
          <span>·</span>
          <span>{problems.filter(p => p.status === 'completed').length} completed</span>
        </div>
      </div>
    </div>
  );
}
