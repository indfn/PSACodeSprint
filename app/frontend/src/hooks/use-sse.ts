import { useEffect, useRef, useCallback } from 'react';

export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
  timestamp: string;
}

const EVENT_TYPES = [
  'trace_entry',
  'hitl_card',
  'hitl_request',
  'hitl_resolved',
  'hitl_timeout',
  'cost_update',
  'confidence_update',
  'run_complete',
  'system_status',
  'escalation',
  'notification',
  'deviation',
  'agent_thinking',
  'tool_call',
  'tool_result',
  'tool_confirmation',
];

export function connectSSE(
  runId: string,
  onEvent: (event: SSEEvent) => void,
  onError?: (error: Event) => void
): () => void {
  const es = new EventSource(`/agent/stream/${runId}`);

  // Named events — EventSource only dispatches to onmessage for unnamed events
  for (const eventType of EVENT_TYPES) {
    es.addEventListener(eventType, ((e: MessageEvent) => {
      try {
        const raw = JSON.parse(e.data);
        onEvent({
          event: eventType,
          data: raw.data || raw,
          timestamp: raw.timestamp || new Date().toISOString(),
        });
      } catch {
        onEvent({
          event: eventType,
          data: { raw: e.data },
          timestamp: new Date().toISOString(),
        });
      }
    }) as EventListener);
  }

  // Fallback for unnamed events
  es.onmessage = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      onEvent({
        event: data.event || 'message',
        data: data.data || data,
        timestamp: data.timestamp || new Date().toISOString(),
      });
    } catch {
      onEvent({
        event: 'message',
        data: { raw: e.data },
        timestamp: new Date().toISOString(),
      });
    }
  };

  es.onerror = (err) => {
    if (onError) onError(err);
  };

  return () => es.close();
}

export function useSSE(runId: string | null, onEvent: (event: SSEEvent) => void) {
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const cleanupRef = useRef<(() => void) | null>(null);

  const disconnect = useCallback(() => {
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!runId) {
      disconnect();
      return;
    }

    disconnect();
    cleanupRef.current = connectSSE(runId, (event) => onEventRef.current(event));

    return disconnect;
  }, [runId, disconnect]);
}
