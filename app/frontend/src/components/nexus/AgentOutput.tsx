import { ScrollArea } from '@/components/ui/scroll-area';
import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { ArrowDownUp } from 'lucide-react';

export interface AgentEvent {
  timestamp: string;
  message: string;
}

interface AgentOutputProps {
  events: AgentEvent[];
}

function humanize(msg: string): { text: string; kind: 'ingest'|'tool'|'hitl'|'success'|'warn'|'info' } {
  if (msg.startsWith('→')) {
    if (msg.includes('get_itt_candidates')) return { text: 'Agent queried yard inventory — checking which containers are ready', kind: 'tool' };
    if (msg.includes('check_road')) return { text: 'Checking road capacity — validating truck availability & LTA limits', kind: 'tool' };
    if (msg.includes('check_sea')) return { text: 'Checking sea capacity — feeder berth & tidal window', kind: 'tool' };
    if (msg.includes('compute_itt_split')) return { text: 'Computing optimal road-vs-sea split…', kind: 'tool' };
    if (msg.includes('dispatch_road')) return { text: 'Planning truck dispatch — West Coast Hwy → AYE → Tuas', kind: 'tool' };
    if (msg.includes('request_feeder_hold')) return { text: 'Requesting feeder hold — asking operator to hold vessel', kind: 'tool' };
    if (msg.includes('update_tuas')) return { text: 'Updating Tuas loading sequence — aligning QC bays to ITT ETAs', kind: 'tool' };
    return { text: msg.replace(/^→\s*/, 'Calling tool: '), kind: 'tool' };
  }
  if (msg.startsWith('←')) {
    if (msg.includes('fallback')) return { text: 'Tool completed via fallback (primary failed) — see trace for detail', kind: 'warn' };
    if (msg.includes('dispatch_road')) return { text: 'Dispatch planned — trucks assigned (see HITL-2)', kind: 'success' };
    if (msg.includes('request_feeder_hold')) return { text: 'Feeder hold costed — $800/hr', kind: 'info' };
    if (msg.includes('update_tuas')) return { text: 'Tuas sequence updated — margin before departure preserved', kind: 'success' };
    if (msg.includes('get_itt')) return { text: 'Inventory ready — containers confirmed in yard', kind: 'success' };
    if (msg.includes('check_road') || msg.includes('check_sea')) return { text: 'Capacity checked — constraints validated', kind: 'success' };
    if (msg.includes('compute_itt')) return { text: 'Split computed — see HITL-1 for cost breakdown', kind: 'success' };
    return { text: msg.replace(/^←\s*/, 'Completed: '), kind: 'success' };
  }
  if (msg.includes('HITL gate')) return { text: msg, kind: 'hitl' };
  if (msg.includes('HITL approved')) return { text: 'Approved — advancing to next stage', kind: 'success' };
  if (msg.includes('Confidence')) return { text: msg, kind: 'info' };
  if (msg.includes('Escalation')) return { text: msg, kind: 'warn' };
  if (msg.includes('Deviation')) return { text: msg, kind: 'warn' };
  if (msg.includes('Agent reasoning')) return { text: 'Agent is reasoning…', kind: 'info' };
  if (msg.includes('Demo started')) return { text: msg, kind: 'info' };
  if (msg.includes('Run complete')) return { text: 'Workflow complete — all stages done. Check History for full trace.', kind: 'success' };
  return { text: msg, kind: 'info' };
}

const kindStyle: Record<string, string> = {
  tool: 'text-blue-600 dark:text-blue-400',
  hitl: 'text-amber-600 dark:text-amber-400 font-medium',
  success: 'text-emerald-600 dark:text-emerald-400',
  warn: 'text-amber-600 dark:text-amber-400',
  ingest: 'text-muted-foreground',
  info: 'text-foreground',
};

export default function AgentOutput({ events }: AgentOutputProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [newestFirst, setNewestFirst] = useState(false);
  const ordered = newestFirst ? [...events].reverse() : events;

  useEffect(() => {
    if (scrollRef.current && !newestFirst) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events, newestFirst]);

  function formatTime(ts: string) {
    try { return new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }); } catch { return ts; }
  }

  return (
    <div className="rounded-xl bg-muted/50 p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-semibold text-muted-foreground">Agent Output</h3>
        <Button variant="ghost" size="sm" className="h-6 text-xs gap-1" onClick={() => setNewestFirst(v=>!v)}><ArrowDownUp size={12}/>{newestFirst ? 'Newest' : 'Oldest'}</Button>
      </div>
      <ScrollArea className="h-[400px]">
        <div ref={scrollRef} className="space-y-1 text-xs">
          {events.length === 0 && <p className="text-muted-foreground">Waiting for agent events — click Start Demo.</p>}
          {ordered.map((ev, i) => {
            const h = humanize(ev.message);
            return (
              <div key={i} className="flex gap-2">
                <span className="text-muted-foreground shrink-0">[{formatTime(ev.timestamp)}]</span>
                <span className={kindStyle[h.kind]}>{h.text}</span>
              </div>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
