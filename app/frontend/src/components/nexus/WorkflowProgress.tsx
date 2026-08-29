import { Check, Clock, Circle } from 'lucide-react';

export type WorkflowStage = 'event' | 'ingest' | 'split' | 'hitl1' | 'dispatch' | 'hitl2' | 'hold' | 'hitl3' | 'sequence' | 'hitl4' | 'monitor' | 'complete';

interface StageDef {
  id: WorkflowStage;
  label: string;
  short: string;
}

const STAGES: StageDef[] = [
  { id: 'event', label: 'Event', short: 'Event' },
  { id: 'ingest', label: 'Ingest', short: 'Ingest' },
  { id: 'split', label: 'Compute Split', short: 'Split' },
  { id: 'hitl1', label: 'Split Approval', short: 'HITL-1' },
  { id: 'dispatch', label: 'Dispatch', short: 'Dispatch' },
  { id: 'hitl2', label: 'Dispatch Approval', short: 'HITL-2' },
  { id: 'hold', label: 'Feeder Hold', short: 'Hold' },
  { id: 'hitl3', label: 'Hold Approval', short: 'HITL-3' },
  { id: 'sequence', label: 'Tuas Sequence', short: 'Tuas' },
  { id: 'hitl4', label: 'Sequence Approval', short: 'HITL-4' },
  { id: 'monitor', label: 'Monitor', short: 'Monitor' },
  { id: 'complete', label: 'Complete', short: 'Done' },
];

function getCurrentStageIndex(hitlGateId: string | null, events: Array<{message:string}>, status: string): number {
  if (status === 'completed') return STAGES.length - 1;
  if (status === 'idle' || (!hitlGateId && events.length === 0)) return 0; // waiting at Event
  if (hitlGateId === 'HITL-1') return 3;
  if (hitlGateId === 'HITL-2') return 5;
  if (hitlGateId === 'HITL-3') return 7;
  if (hitlGateId === 'HITL-4') return 9;
  // HITL-5 is emergency escalation — don't advance progress, fall through to event-based logic
  const lastMsg = events[events.length - 1]?.message || '';
  if (lastMsg.includes('HITL-1') || lastMsg.includes('split')) return 3;
  if (lastMsg.includes('dispatch')) return 4;
  if (lastMsg.includes('HITL-2')) return 5;
  if (lastMsg.includes('hold')) return 6;
  if (lastMsg.includes('HITL-3')) return 7;
  if (lastMsg.includes('Tuas') || lastMsg.includes('sequence')) return 8;
  if (lastMsg.includes('HITL-4')) return 9;
  if (lastMsg.includes('monitor') || lastMsg.includes('Deviation')) return 10;
  if (status === 'running' && events.length > 0) {
    if (events.some(e => e.message.includes('compute_itt'))) return 2;
    if (events.some(e => e.message.includes('check_road') || e.message.includes('check_sea'))) return 1;
  }
  return events.length === 0 ? 0 : 1;
}

export function getWorkflowStage(hitlGateId: string | null, events: Array<{message:string}>, status: string): WorkflowStage {
  return STAGES[getCurrentStageIndex(hitlGateId, events, status)]?.id || 'event';
}

export default function WorkflowProgress({ hitlGateId, events, status }: { hitlGateId: string | null; events: Array<{message:string,timestamp:string}>; status?: string }) {
  const current = getCurrentStageIndex(hitlGateId, events, status || '');

  return (
    <div className="rounded-xl border bg-card p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-muted-foreground">Workflow Progress</span>
      </div>
      <div className="flex items-center gap-1 overflow-x-auto">
        {STAGES.map((s, idx) => {
          const isDone = idx < current;
          const isCurrent = idx === current;
          return (
            <div key={s.id} className="flex items-center gap-1 shrink-0">
              <div
                className={`flex items-center justify-center h-6 w-6 rounded-full border text-[10px] font-medium
                ${isDone ? 'bg-emerald-500 border-emerald-500 text-white' : isCurrent ? 'bg-primary border-primary text-primary-foreground ring-2 ring-primary/20' : 'bg-muted border-muted-foreground/20 text-muted-foreground'}`}
              >
                {isDone ? <Check size={12} /> : isCurrent ? <Clock size={12} /> : <Circle size={10} />}
              </div>
              <span className={`text-[10px] whitespace-nowrap ${isCurrent ? 'font-semibold text-foreground' : isDone ? 'text-emerald-600' : 'text-muted-foreground'}`}>{s.short}</span>
              {idx < STAGES.length - 1 && <div className={`h-px w-4 mx-1 ${idx < current ? 'bg-emerald-500' : 'bg-border'}`} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
