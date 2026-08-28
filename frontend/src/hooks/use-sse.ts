import { useEffect, useRef, useCallback } from 'react';

export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export function connectSSE(
  runId: string,
  onEvent: (event: SSEEvent) => void,
  onError?: (error: Event) => void
): () => void {
  const es = new EventSource(`/agent/stream/${runId}`);

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
