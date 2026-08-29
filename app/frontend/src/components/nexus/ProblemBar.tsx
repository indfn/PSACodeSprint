import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Loader2, Play, CheckCircle2, Radio } from 'lucide-react';
import { getRegistry, simulateWebhook, type RegistryProblem } from '@/api/nexus';

interface ProblemBarProps {
  onRunStarted: (runId: string, problemId: string) => void;
  activeRunProblemId: string | null;
}

export default function ProblemBar({ onRunStarted, activeRunProblemId }: ProblemBarProps) {
  const [problems, setProblems] = useState<RegistryProblem[]>([]);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchRegistry = useCallback(async () => {
    try {
      const res = await getRegistry();
      setProblems(res.problems);
    } catch {
      setProblems([
        { problem_id: 'pb-12-itt', short_id: 'pb-12', name: 'ITT Coordination', description: '', status: 'idle' },
        { problem_id: 'pb-01-berth', short_id: 'pb-01', name: 'Berth Reassignment', description: '', status: 'idle' },
      ]);
    }
  }, []);

  useEffect(() => {
    fetchRegistry();
    const interval = setInterval(fetchRegistry, 3000);
    return () => clearInterval(interval);
  }, [fetchRegistry]);

  const handleStart = async (problemId: string) => {
    setLoading(problemId);
    setError(null);
    try {
      const res = await simulateWebhook(problemId);
      if (res.run_id) {
        onRunStarted(res.run_id, problemId);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trigger');
    } finally {
      setLoading(null);
    }
  };

  const anyRunning = problems.some(p => p.status === 'running');

  return (
    <div className="flex items-center gap-2 overflow-x-auto">
      <span className="text-[10px] text-muted-foreground font-medium shrink-0">Problems</span>
      {problems.map((p) => {
        const isRunning = p.status === 'running';
        const isCompleted = p.status === 'completed';
        const isThisRunning = activeRunProblemId === p.problem_id;
        const isLoading = loading === p.problem_id;
        const canStart = !isRunning && !isLoading && (!anyRunning || isThisRunning);

        return (
          <div
            key={p.problem_id}
            className={`flex items-center gap-1.5 rounded-lg border px-2 py-1 shrink-0 transition-colors ${
              isThisRunning ? 'border-primary/40 bg-primary/5' :
              isRunning ? 'border-amber-500/30 bg-amber-500/5' :
              isCompleted ? 'border-emerald-500/30 bg-emerald-500/5' :
              'border-border'
            }`}
          >
            {isRunning ? (
              <Loader2 size={10} className="animate-spin text-amber-500" />
            ) : isCompleted ? (
              <CheckCircle2 size={10} className="text-emerald-500" />
            ) : (
              <Radio size={10} className="text-muted-foreground" />
            )}

            <span className="text-[11px] font-medium whitespace-nowrap">{p.name}</span>

            {isThisRunning ? (
              <span className="text-[10px] text-primary font-medium">Active</span>
            ) : isRunning ? (
              <span className="text-[10px] text-amber-500">Queued</span>
            ) : (
              <Button
                size="sm"
                variant="ghost"
                className="h-5 px-1.5 text-[10px]"
                onClick={() => handleStart(p.problem_id)}
                disabled={isLoading || !canStart}
              >
                {isLoading ? <Loader2 size={10} className="animate-spin" /> : <Play size={10} />}
              </Button>
            )}
          </div>
        );
      })}

      {error && (
        <span className="text-[10px] text-red-500 shrink-0">{error}</span>
      )}
    </div>
  );
}
