import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { hitlRespond } from '@/api/nexus';
import { AlertTriangle, Shield, Clock, TrendingUp, Truck, XCircle, CheckCircle2 } from 'lucide-react';

interface EscalationPopupProps {
  gate: { gate_id: string; gate_name: string; data: Record<string, unknown> };
  runId: string;
  onResolved: () => void;
  onNextGate: (gate: { gate_id: string; gate_name: string; data: Record<string, unknown> } | null) => void;
}

function fmtMoney(n: number) { return `$${Math.round(n).toLocaleString()}`; }

export default function EscalationPopup({ gate, runId, onResolved, onNextGate }: EscalationPopupProps) {
  const d = gate.data || {};
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const canSubmit = reason.trim().length >= 10;
  const conf = (d.confidence as number) ?? null;
  const risk = (d.risk_score as number) ?? null;
  const deviation = (d.deviation as Record<string, unknown>) || null;
  const trigger = (d.trigger as string) || (deviation?.type as string) || (deviation?.trigger as string) || 'escalation';
  const triggeredAt = (d.triggered_at_stage as string) || '';

  async function handle(decision: string) {
    if (!canSubmit) return;
    setLoading(true);
    try {
      const res = await hitlRespond(runId, decision, gate.gate_id, reason);
      const nextCard = (res.hitl_card as Record<string, unknown>) || (res.hitl_pending as Record<string, unknown>);
      if (res.status === 'waiting_hitl' && nextCard) {
        const gid = (nextCard.gate_id as string) || '';
        const gname = (nextCard.gate_name as string) || '';
        const cardInner = (nextCard.approval_card as Record<string, unknown>) || nextCard;
        onNextGate({ gate_id: gid, gate_name: gname, data: cardInner as Record<string, unknown> });
      } else {
        onNextGate(null);
        onResolved();
      }
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }

  const agentReasoning = (d.agent_reasoning as string) || (d.missing_data_notice as string) || '';
  const validationNotes = (d.validation_notes as string) || '';

  return (
    <div className="rounded-xl bg-card border-2 border-red-500 shadow-xl overflow-hidden">
      <div className="p-5 space-y-4 max-h-[80vh] overflow-y-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="destructive" className="animate-pulse">ESCALATION</Badge>
              <span className="text-xs text-muted-foreground">HITL-5</span>
            </div>
            <Badge variant="outline" className="text-[10px]">{trigger}</Badge>
          </div>
          <div>
            <h2 className="text-sm font-bold flex items-center gap-2 text-red-600"><AlertTriangle size={16}/>Escalation to Duty Manager</h2>
            <p className="text-xs text-muted-foreground mt-1">Agent confidence below threshold or operational risk detected. Duty manager review required.</p>
            {triggeredAt && <p className="text-[10px] text-muted-foreground">Triggered at: {triggeredAt}</p>}
          </div>

          {String(d.reason || '') && <p className="text-xs text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-950/30 rounded p-2">{String(d.reason)}</p>}
          {deviation && String(deviation.impact || deviation.message || '') && <p className="text-xs text-muted-foreground">{String(deviation.impact || deviation.message)}</p>}
          {agentReasoning && <div className="rounded border bg-amber-50 dark:bg-amber-950/20 p-2 text-xs"><p className="font-medium text-amber-800 dark:text-amber-300">Agent says:</p><p className="text-muted-foreground whitespace-pre-wrap">{agentReasoning.slice(0,600)}</p></div>}
          {validationNotes && <p className="text-xs text-amber-600">⚠ {String(validationNotes)}</p>}

          {(d.previous_split as Record<string, unknown>) && (d.new_split as Record<string, unknown>) ? (
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="rounded border p-2 bg-muted/30">
                <p className="text-muted-foreground font-medium mb-1">Previous Split</p>
                <p>Road: <span className="font-bold">{String((d.previous_split as Record<string, unknown>).road_containers ?? '?')} cont</span></p>
                <p>Sea: <span className="font-bold">{String((d.previous_split as Record<string, unknown>).sea_containers ?? '?')} cont</span></p>
                <p>Cost: <span className="font-bold">{fmtMoney((d.previous_split as Record<string, unknown>).total_transport_cost as number)}</span></p>
              </div>
              <div className="rounded border-2 border-red-400 bg-red-50 dark:bg-red-950/30 p-2">
                <p className="text-red-600 font-medium mb-1">New Split</p>
                <p>Road: <span className="font-bold">{String((d.new_split as Record<string, unknown>).road_containers ?? '?')} cont</span></p>
                <p>Sea: <span className="font-bold">{String((d.new_split as Record<string, unknown>).sea_containers ?? '?')} cont</span></p>
                <p>Cost: <span className="font-bold">{fmtMoney((d.new_split as Record<string, unknown>).total_transport_cost as number)}</span></p>
              </div>
            </div>
          ) : (d.optimal_split as Record<string, unknown>) ? (
            <div className="rounded border p-3 bg-muted/30 text-xs">
              <p className="font-medium mb-1">Current Split</p>
              <p>Road: <span className="font-bold">{String((d.optimal_split as Record<string, unknown>).road_containers ?? '?')} cont</span> · Sea: <span className="font-bold">{String((d.optimal_split as Record<string, unknown>).sea_containers ?? '?')} cont</span></p>
              <p>Cost: <span className="font-bold">{fmtMoney((d.optimal_split as Record<string, unknown>).total_transport_cost as number || 0)}</span></p>
            </div>
          ) : null}
          {(() => {
            const det = (d.escalation_details as Record<string, unknown>) || null;
            if (!det) return null;
            const k = String(det.trigger || d.escalation_kind || trigger);
            if (k === 'road_capacity_low') return <div className="rounded border bg-amber-50 dark:bg-amber-950/20 p-2 text-xs"><p className="font-medium">Truck Capacity</p><p>Trucks: <span className="font-bold">{String(det.available_trucks ?? '?')}/{String((det as Record<string, unknown>).total_fleet ?? 55)}</span> available, need <span className="font-bold">{String(det.required_trucks ?? '?')} trips</span> · Ratio: <span className="font-bold">{String(det.ratio ?? '?')}</span> (threshold 0.6)</p><p className="text-muted-foreground">Have {String(det.available_trucks ?? '?')} trucks for {String(det.required_trucks ?? '?')} trips — suggest sea-heavy.</p></div>;
            if (k === 'data_stale') return <div className="rounded border bg-amber-50 dark:bg-amber-950/20 p-2 text-xs"><p className="font-medium">Data Freshness</p><p>Age: <span className="font-bold">{String(det.data_age_minutes ?? '?')} min</span> · Source: {String(det.source ?? 'CITOS PPT')} · Stale threshold: {String((det as Record<string, unknown>).freshness_max ?? (det as Record<string, unknown>).threshold ?? 20)} min</p><p className="text-muted-foreground">Data older than threshold — split may be unreliable.</p></div>;
            if (k === 'low_confidence') return <div className="rounded border bg-amber-50 dark:bg-amber-950/20 p-2 text-xs"><p className="font-medium">Model Confidence</p><p>Confidence: <span className="font-bold">{det.confidence !== undefined ? `${(Number(det.confidence)*100).toFixed(0)}%` : '?'}</span> · Threshold: {String(det.threshold ?? '0.85')}</p></div>;
            if (k === 'feeder_hold_exceeded') return <div className="rounded border bg-amber-50 dark:bg-amber-950/20 p-2 text-xs"><p className="font-medium">Feeder Hold</p><p>Hold: <span className="font-bold">{String(det.hold_hours ?? '?')}h</span> · Limit: {String(det.limit ?? '1.5')}h</p></div>;
            if (k === 'cost_exceeded') return <div className="rounded border bg-amber-50 dark:bg-amber-950/20 p-2 text-xs"><p className="font-medium">Cost</p><p>Total: <span className="font-bold">{fmtMoney(det.total_cost as number)}</span> · Baseline: {det.baseline ? fmtMoney(det.baseline as number) : '?'} · Limit: $10,000</p></div>;
            if (k === 'feeder_unresponsive') return <div className="rounded border bg-amber-50 dark:bg-amber-950/20 p-2 text-xs"><p className="font-medium">Feeder Response</p><p>Elapsed: <span className="font-bold">{String(det.elapsed ?? '?')} min</span> · Threshold: {String(det.threshold ?? 15)} min</p></div>;
            return null;
          })()}

          {String(d.cost_impact || '') && <p className="text-xs text-red-600 flex items-center gap-1"><TrendingUp size={12}/>Cost Impact: {String(d.cost_impact)}</p>}
          {String(d.delta_trucks || '') && <p className="text-xs text-muted-foreground flex items-center gap-1"><Truck size={12}/>{String(d.delta_trucks)}</p>}

          <div className="flex items-center gap-3 text-xs text-muted-foreground border-t pt-2">
            <span className="flex items-center gap-1"><Shield size={12} className={risk !== null && risk > 0.35 ? 'text-red-500' : risk !== null && risk > 0.15 ? 'text-amber-500' : 'text-emerald-500'}/>{risk!==null?(risk>0.35?'High risk':risk>0.15?'Med risk':'Low risk'):'—'} · {conf!==null?`${(conf*100).toFixed(0)}% conf`:'—'}</span>
            {(d.margin_minutes as number) ? <span className="flex items-center gap-1"><Clock size={12}/>Departure in {Math.round((d.margin_minutes as number)/60)}h {(d.margin_minutes as number)%60}m</span> : null}
            {(d.timeout_seconds as number) ? <span className="ml-auto"><Clock size={12} className="inline"/> {Math.round((d.timeout_seconds as number)/60)}m → halt</span> : null}
          </div>

          <div className="space-y-2">
            <label className="text-xs font-medium">Duty manager decision *</label>
            <Textarea placeholder="Required — at least 10 characters. What triggered this? What is the impact? What should the agent do next? (e.g., approve re-split with +4 trucks, hold current split, cancel ITT, provide alternative breakdown)" value={reason} onChange={e=>setReason(e.target.value)} className="min-h-[80px] text-xs" />
            <div className="flex justify-between text-[10px]">
              <span className={canSubmit ? 'text-emerald-600' : 'text-amber-600'}>{reason.trim().length}/10 min {canSubmit ? '✓' : '— keep typing'}</span>
              <span className="text-muted-foreground">Guides: What happened? What’s the impact? What’s next and why?</span>
            </div>
            {!canSubmit && <p className="text-[10px] text-amber-600">Tell the agent what to do next so it can continue (approve/reject both need this).</p>}
          </div>

           <div className="flex gap-2">
            <Button size="sm" variant="destructive" disabled={loading || !canSubmit} onClick={()=>handle('reject')} className="h-8 text-xs gap-1"><XCircle size={12}/>Reject</Button>
            <Button size="sm" disabled={loading || !canSubmit} onClick={()=>handle('approve')} className="h-8 text-xs gap-1 ml-auto"><CheckCircle2 size={12}/>Approve</Button>
          </div>
        </div>
      </div>
  );
}
