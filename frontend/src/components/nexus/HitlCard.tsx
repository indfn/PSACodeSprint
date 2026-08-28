import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useState } from 'react';
import { hitlRespond } from '@/api/nexus';
import { Badge } from '@/components/ui/badge';

export interface HitlGateInfo {
  gate_id: string;
  gate_name: string;
  data: Record<string, unknown>;
}

interface HitlCardProps {
  gate: HitlGateInfo;
  runId: string;
  onResponded?: () => void;
}

function formatValue(val: unknown): string {
  if (val === null || val === undefined) return '—';
  if (typeof val === 'object') return JSON.stringify(val, null, 2);
  return String(val);
}

function renderDecisionData(data: Record<string, unknown>) {
  const entries = Object.entries(data).filter(([, v]) => v !== null && v !== undefined);
  if (entries.length === 0) return <p className="text-xs text-muted-foreground">No data</p>;
  return (
    <div className="space-y-1.5">
      {entries.map(([key, val]) => (
        <div key={key} className="flex justify-between text-xs">
          <span className="text-muted-foreground capitalize">
            {key.replace(/_/g, ' ')}
          </span>
          <span className="font-medium text-right max-w-[60%] truncate">
            {formatValue(val)}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function HitlCard({ gate, runId, onResponded }: HitlCardProps) {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [responded, setResponded] = useState(false);

  async function handleDecision(decision: string) {
    setLoading(true);
    try {
      await hitlRespond(runId, decision, gate.gate_id, reason || undefined);
      setResponded(true);
      onResponded?.();
    } catch (err) {
      console.error('HITL respond failed:', err);
    } finally {
      setLoading(false);
    }
  }

  if (responded) {
    return (
      <Card size="sm">
        <CardContent className="py-3">
          <p className="text-xs text-muted-foreground">Decision submitted.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card size="sm">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-medium">
            {gate.gate_name}
          </CardTitle>
          <Badge variant="destructive" className="text-[10px]">
            Pending
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {renderDecisionData(gate.data)}

        <Textarea
          placeholder="Reason (optional)..."
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className="min-h-[60px] text-xs"
        />

        <div className="flex gap-1.5">
          <Button
            size="sm"
            variant="destructive"
            disabled={loading}
            onClick={() => handleDecision('reject')}
            className="h-7 text-xs"
          >
            Reject
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={loading}
            onClick={() => handleDecision('modify')}
            className="h-7 text-xs"
          >
            Modify
          </Button>
          <Button
            size="sm"
            disabled={loading}
            onClick={() => handleDecision('approve')}
            className="h-7 text-xs"
          >
            Approve
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
