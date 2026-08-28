import { ScrollArea } from '@/components/ui/scroll-area';
import { useEffect, useRef } from 'react';

export interface AgentEvent {
  timestamp: string;
  message: string;
}

interface AgentOutputProps {
  events: AgentEvent[];
}

export default function AgentOutput({ events }: AgentOutputProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  function formatTime(ts: string) {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });
    } catch {
      return ts;
    }
  }

  return (
    <div className="rounded-xl bg-muted/50 p-4">
      <h3 className="text-xs font-semibold mb-2 text-muted-foreground">Agent Output</h3>
      <ScrollArea className="h-[400px]">
        <div ref={scrollRef} className="space-y-1 font-mono text-xs">
          {events.length === 0 && (
            <p className="text-muted-foreground">
              Waiting for agent events...
            </p>
          )}
          {events.map((ev, i) => (
            <div key={i} className="flex gap-2">
              <span className="text-muted-foreground shrink-0">
                [{formatTime(ev.timestamp)}]
              </span>
              <span className="text-foreground">{ev.message}</span>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
