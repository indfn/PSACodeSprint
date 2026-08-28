import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Agent Output</CardTitle>
      </CardHeader>
      <CardContent>
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
      </CardContent>
    </Card>
  );
}
