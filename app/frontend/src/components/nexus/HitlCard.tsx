import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useState, useEffect } from 'react';
import { hitlRespond } from '@/api/nexus';
import { Badge } from '@/components/ui/badge';
import { Clock, Shield, AlertTriangle, CheckCircle2, XCircle, Edit3, Truck, Ship, Anchor, Container, TrendingUp } from 'lucide-react';

export interface HitlGateInfo {
  gate_id: string;
  gate_name: string;
  data: Record<string, unknown>;
}

interface HitlCardProps {
  gate: HitlGateInfo | null;
  runId: string;
  onResponded?: () => void;
  onNextGate?: (gate: HitlGateInfo | null) => void;
}

const GATE_DESCRIPTIONS: Record<string, { step: string; title: string; what: string; why: string; timeoutHint: string }> = {
  'HITL-1': { step: '1 / 4', title: 'ITT Split Plan', what: 'Agent computed the optimal road-vs-sea split for 120 containers.', why: 'Your approval authorizes truck dispatch planning.', timeoutHint: 'No action → escalates to Duty Manager' },
  'HITL-2': { step: '2 / 4', title: 'Truck Dispatch', what: 'Ready to dispatch trucks on West Coast Hwy → AYE → Tuas.', why: 'Confirms road capacity and LTA chassis limits.', timeoutHint: 'Timeout → dispatch cancelled' },
  'HITL-3': { step: '3 / 4', title: 'Feeder Hold Request', what: 'Request 1-hour hold for FEEDER ATLANTIC-03 to catch tidal window.', why: 'Holds cost $800/hr but avoids $5,000 missed connection.', timeoutHint: 'Timeout → escalates' },
  'HITL-4': { step: '4 / 4', title: 'Tuas Loading Sequence', what: 'Updates QC bays for MV PACIFIC STAR based on ITT ETAs.', why: 'Aligns road (14:30) and sea (16:30) arrivals to vessel departure 20:00.', timeoutHint: 'Timeout → sequence held as-is' },
  'HITL-5': { step: 'Emergency', title: 'Duty Manager Escalation', what: 'Deviation detected — emergency re-split required.', why: 'Requires senior approval due to low confidence or cost breach.', timeoutHint: 'Timeout → workflow halted' },
};

function fmtMoney(n: number) { return `$${Math.round(n).toLocaleString()}`; }
function fmtTime(iso: string) { try { return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }); } catch { return iso; } }

export default function HitlCard({ gate, runId, onResponded, onNextGate }: HitlCardProps) {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [responded, setResponded] = useState(false);
  const [showModify, setShowModify] = useState(false);
  const [modRoad, setModRoad] = useState('');
  useEffect(() => { setResponded(false); setReason(''); setShowModify(false); setModRoad(''); }, [gate?.gate_id]);

  async function handleDecision(decision: string) {
    setLoading(true);
    try {
      const mods = decision === 'modify' && modRoad ? { road_containers: parseInt(modRoad,10) } : undefined;
      const res = await hitlRespond(runId, decision, gate!.gate_id, reason || undefined, mods);
      const nextCard = (res.hitl_card as Record<string, unknown>) || (res.hitl_pending as Record<string, unknown>);
      if (res.status === 'waiting_hitl' && nextCard) {
        const gid = (nextCard.gate_id as string) || '';
        const gname = (nextCard.gate_name as string) || 'Approval Required';
        const cardInner = (nextCard.approval_card as Record<string, unknown>) || nextCard;
        onNextGate?.({ gate_id: gid, gate_name: gname, data: cardInner as Record<string, unknown> });
      } else if (['completed','halted','cancelled','holding'].includes(res.status)) {
        onNextGate?.(null); onResponded?.();
      } else {
        setResponded(true); onResponded?.();
      }
    } catch (err) { console.error('HITL respond failed:', err); } finally { setLoading(false); }
  }

  if (!gate || responded) {
    return (
      <div className="rounded-xl bg-muted/50 p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-muted-foreground">Approval Queue</h3>
          <span className="h-2 w-2 rounded-full bg-muted-foreground/30" />
        </div>
        <p className="text-xs text-muted-foreground mt-2">No approvals pending — agent is running or awaiting next stage.</p>
      </div>
    );
  }

  const meta = GATE_DESCRIPTIONS[gate.gate_id] || { step: gate.gate_id, title: gate.gate_name, what: 'Review the agent\'s proposal and approve, reject, or modify.', why: '', timeoutHint: '' };
  const d = gate.data || {};
  const conf = (d.confidence as number) ?? null;
  const risk = (d.risk_score as number) ?? null;
  const margin = (d.margin_minutes as number) ?? 0;
  const timeoutSec = (d.timeout_seconds as number) ?? 900;
  const timeoutAct = (d.timeout_action as string) ?? '';
  const isHitl1 = gate.gate_id === 'HITL-1';

  // Gate-specific data
  const dispatch = (d.dispatch as Record<string, unknown>) || null;
  const feederHold = (d.feeder_hold as Record<string, unknown>) || null;
  const tuasSeq = (d.tuas_sequence as Record<string, unknown>) || null;
  const deviation = (d.deviation as Record<string, unknown>) || null;

  // HITL-1: split data
  const opt = (d.optimal_split as Record<string, unknown>) || (d.cost_breakdown as Record<string, unknown>)?.optimal_split as Record<string, unknown> || null;
  const vs = (d.cost_vs_baseline as Record<string, unknown>) || (d.cost_breakdown as Record<string, unknown>)?.cost_vs_baseline as Record<string, unknown> || null;
  const roadC = (opt?.road_containers as number) ?? 0;
  const seaC = (opt?.sea_containers as number) ?? 0;
  const roadCost = (opt?.road_cost as number) ?? 0;
  const seaCost = (opt?.sea_terminal_handling_cost as number) ?? 0;
  const total = (opt?.total_transport_cost as number) ?? 0;
  const baseline = (vs?.baseline_all_road_cost as number) ?? 0;
  const savings = baseline ? baseline - total : 0;

  return (
    <div className="rounded-xl border bg-card p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">{meta.step}</Badge>
          <h3 className="text-sm font-semibold">{gate.gate_id}: {meta.title}</h3>
        </div>
        <Badge variant="destructive" className="text-xs animate-pulse">Approval Required</Badge>
      </div>

      {/* Gate description */}
      <div className="rounded-lg bg-muted/50 p-3 space-y-1">
        <p className="text-xs font-medium flex items-center gap-1.5"><CheckCircle2 size={12}/>{meta.what}</p>
        {meta.why && <p className="text-xs text-muted-foreground">{meta.why}</p>}
        <p className="text-xs text-muted-foreground flex items-center gap-1"><Clock size={12}/>Timeout {Math.round(timeoutSec/60)}m → {timeoutAct} {meta.timeoutHint && `• ${meta.timeoutHint}`}</p>
      </div>

      {/* Gate-specific content */}
      {isHitl1 && opt && (
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="rounded-lg border p-2">
            <p className="text-xs text-muted-foreground flex items-center justify-center gap-1"><Truck size={12}/>Road</p>
            <p className="text-sm font-bold">{roadC} cont</p>
            <p className="text-xs text-muted-foreground">{opt.road_breakdown as string || `${opt.road_trips} trips`}</p>
            <p className="text-xs font-medium">{fmtMoney(roadCost)}</p>
          </div>
          <div className="rounded-lg border p-2">
            <p className="text-xs text-muted-foreground flex items-center justify-center gap-1"><Ship size={12}/>Sea</p>
            <p className="text-sm font-bold">{seaC} cont</p>
            <p className="text-xs text-muted-foreground">{seaCost === 0 ? 'Charter $0' : fmtMoney(seaCost)}</p>
          </div>
          <div className="rounded-lg border-2 border-primary p-2 bg-primary/5">
            <p className="text-xs text-muted-foreground">Total</p>
            <p className="text-sm font-bold">{fmtMoney(total)}</p>
            <p className="text-xs text-emerald-600">{savings>0?`Save ${fmtMoney(savings)}`:`+${fmtMoney(-savings)}`}</p>
          </div>
        </div>
      )}

      {isHitl1 && baseline > 0 && (
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <AlertTriangle size={12} className="text-amber-500"/>
          Baseline: {vs?.baseline_all_road_trips as number} all-road trips = {fmtMoney(baseline)}
        </div>
      )}

      {!isHitl1 && dispatch && (
        <div className="rounded-lg border p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium flex items-center gap-1"><Truck size={12}/>Dispatch Ready</span>
            <Badge variant="secondary" className="text-[10px]">{(dispatch.status as string) || 'dispatched'}</Badge>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div><span className="text-muted-foreground">Trucks:</span> <span className="font-medium">{String(dispatch.num_trucks)}</span></div>
            <div><span className="text-muted-foreground">Trips:</span> <span className="font-medium">{String(dispatch.total_trips)}</span></div>
            <div><span className="text-muted-foreground">Containers:</span> <span className="font-medium">{String(dispatch.container_count)}</span></div>
            <div><span className="text-muted-foreground">Cost:</span> <span className="font-medium">{fmtMoney(dispatch.dispatch_cost as number)}</span></div>
          </div>
          <div className="text-xs text-muted-foreground">Route: {String(dispatch.route)}</div>
          {String(dispatch.eta || '') && <div className="text-xs text-muted-foreground">ETA Tuas: {fmtTime(String(dispatch.eta))}</div>}
          {(dispatch.num_trucks as number) && (dispatch.total_trips as number) && (dispatch.container_count as number) && (() => {
            const n = Number(dispatch.num_trucks);
            const t = Number(dispatch.total_trips);
            const c = String(dispatch.container_count);
            const assignments = dispatch.truck_assignments as Array<Record<string, unknown>> | undefined;
            if (Array.isArray(assignments) && assignments.length) {
              const two = assignments.filter(a => Number(a.trips) === 2).length;
              const one = assignments.filter(a => Number(a.trips) === 1).length;
              if (two || one) {
                return <div className="text-xs text-muted-foreground bg-muted/50 rounded p-2">{two ? `${two} trucks × 2 trips` : ''}{two && one ? ' + ' : ''}{one ? `${one} trucks × 1 trip` : ''} = {t} trips to move {c} containers (LTA: 1×40ft or 2×20ft per trip)</div>;
              }
            }
            const twoTrip = Math.max(0, t - n);
            const oneTrip = Math.max(0, n - twoTrip);
            const detail = twoTrip > 0 && oneTrip > 0 ? `${twoTrip} trucks × 2 trips + ${oneTrip} trucks × 1 trip = ${t} trips` : `${n} trucks × ${t} trips`;
            return <div className="text-xs text-muted-foreground bg-muted/50 rounded p-2">{detail} to move {c} containers (LTA: 1×40ft or 2×20ft per trip, ~210 min round-trip)</div>;
          })()}
        </div>
      )}

      {!isHitl1 && !dispatch && feederHold && (
        <div className="rounded-lg border p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium flex items-center gap-1"><Anchor size={12}/>Feeder Hold</span>
            <Badge variant={feederHold.tidal_risk === 'critical' ? 'destructive' : feederHold.tidal_risk === 'marginal' ? 'secondary' : 'outline'} className="text-[10px]">Tidal: {String(feederHold.tidal_risk)}</Badge>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div><span className="text-muted-foreground">Duration:</span> <span className="font-medium">{String(feederHold.hold_hours)}h</span></div>
            <div><span className="text-muted-foreground">Cost:</span> <span className="font-medium">{fmtMoney(feederHold.hold_cost as number)}</span></div>
            <div><span className="text-muted-foreground">Rate:</span> <span className="font-medium">{fmtMoney(feederHold.hold_cost_per_hour as number)}/hr</span></div>
            <div><span className="text-muted-foreground">Response:</span> <span className="font-medium">{String(feederHold.operator_response)}</span></div>
          </div>
          {String(feederHold.previous_departure || '') && String(feederHold.new_departure || '') && (
            <div className="text-xs text-muted-foreground">
              Departure: {fmtTime(String(feederHold.previous_departure))} → {fmtTime(String(feederHold.new_departure))}
            </div>
          )}
        </div>
      )}

      {!isHitl1 && !dispatch && !feederHold && tuasSeq && (
        <div className="rounded-lg border p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium flex items-center gap-1"><Container size={12}/>Tuas Sequence</span>
            <Badge variant="secondary" className="text-[10px]">{String(tuasSeq.vessel_id)}</Badge>
          </div>
          {String(tuasSeq.updated_loading_sequence || '') && (
            <div className="text-xs text-muted-foreground font-mono bg-muted/50 rounded p-2">{String(tuasSeq.updated_loading_sequence)}</div>
          )}
          {Array.isArray(tuasSeq.qc_adjustments) && tuasSeq.qc_adjustments.length > 0 && (
            <div className="grid grid-cols-2 gap-1 text-xs">
              {(tuasSeq.qc_adjustments as Record<string, unknown>[]).map((q, i) => (
                <div key={i} className="flex items-center gap-1">
                  <span className="font-medium">{String(q.qc_id)}</span>
                  <span className="text-muted-foreground">→ {String(q.new_bay)}</span>
                  <span className="text-muted-foreground">({fmtTime(String(q.eta))})</span>
                </div>
              ))}
            </div>
          )}
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            {String(tuasSeq.estimated_loading_completion || '') && <span>Done: {fmtTime(String(tuasSeq.estimated_loading_completion))}</span>}
            {String(tuasSeq.margin_before_departure_minutes || '') && <span>Departure in {String(tuasSeq.margin_before_departure_minutes)}m</span>}
          </div>
        </div>
      )}

      {/* HITL-5: Emergency re-split content */}
      {!isHitl1 && !dispatch && !feederHold && !tuasSeq && gate.gate_id === 'HITL-5' && (
        <div className="rounded-lg border border-red-200 dark:border-red-900 p-3 space-y-3 bg-red-50/50 dark:bg-red-950/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium flex items-center gap-1 text-red-600"><AlertTriangle size={12}/>Emergency Re-Split Required</span>
            <Badge variant="destructive" className="text-[10px]">{String(deviation?.type || deviation?.trigger || 'berth_conflict')}</Badge>
          </div>
          {String(d.reason || '') && <p className="text-xs text-red-700 dark:text-red-400">{String(d.reason)}</p>}
          {String(deviation?.message || '') && <p className="text-xs text-muted-foreground">{String(deviation.message)}</p>}

          {/* Previous vs New split comparison */}
          {(d.previous_split as Record<string, unknown>) && (d.new_split as Record<string, unknown>) && (
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="rounded border border-red-200 dark:border-red-900 p-2 bg-white/50 dark:bg-black/20">
                <p className="text-muted-foreground font-medium mb-1">Previous Split</p>
                <div className="space-y-0.5">
                  <p>Road: <span className="font-bold">{String((d.previous_split as Record<string, unknown>).road_containers ?? '?')} cont</span></p>
                  <p>Sea: <span className="font-bold">{String((d.previous_split as Record<string, unknown>).sea_containers ?? '?')} cont</span></p>
                  <p>Cost: <span className="font-bold">{fmtMoney((d.previous_split as Record<string, unknown>).total_transport_cost as number)}</span></p>
                </div>
              </div>
              <div className="rounded border-2 border-red-400 dark:border-red-700 p-2 bg-red-100/50 dark:bg-red-900/30">
                <p className="text-red-600 font-medium mb-1">New Split</p>
                <div className="space-y-0.5">
                  <p>Road: <span className="font-bold">{String((d.new_split as Record<string, unknown>).road_containers ?? '?')} cont</span></p>
                  <p>Sea: <span className="font-bold">{String((d.new_split as Record<string, unknown>).sea_containers ?? '?')} cont</span></p>
                  <p>Cost: <span className="font-bold">{fmtMoney((d.new_split as Record<string, unknown>).total_transport_cost as number)}</span></p>
                </div>
              </div>
            </div>
          )}

          {String(d.cost_impact || '') && (
            <div className="flex items-center gap-1.5 text-xs text-red-600 font-medium">
              <TrendingUp size={12}/>Cost Impact: {String(d.cost_impact)}
            </div>
          )}
          {String(d.delta_trucks || '') && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Truck size={12}/>Truck Adjustment: {String(d.delta_trucks)}
            </div>
          )}
        </div>
      )}

      {/* Non-HITL-5 deviation fallback */}
      {!isHitl1 && !dispatch && !feederHold && !tuasSeq && gate.gate_id !== 'HITL-5' && deviation && (
        <div className="rounded-lg border border-red-200 dark:border-red-900 p-3 space-y-2 bg-red-50/50 dark:bg-red-950/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium flex items-center gap-1 text-red-600"><AlertTriangle size={12}/>Emergency Deviation</span>
            <Badge variant="destructive" className="text-[10px]">{String(deviation.type || deviation.trigger || 'deviation')}</Badge>
          </div>
          {String(deviation.message || '') && <p className="text-xs text-muted-foreground">{String(deviation.message)}</p>}
          {String(deviation.severity || '') && <p className="text-xs text-muted-foreground">Severity: {String(deviation.severity)}</p>}
        </div>
      )}

      {/* Confidence / risk / margin */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1"><Shield size={12} className={risk !== null && risk > 0.35 ? 'text-red-500' : risk !== null && risk > 0.15 ? 'text-amber-500' : 'text-emerald-500'}/>{risk!==null?(risk > 0.35 ? 'High risk' : risk > 0.15 ? 'Med risk' : 'Low risk'):'—'}</span>
          <span>{conf!==null?`${(conf*100).toFixed(0)}% conf`:'—'}</span>
        </div>
        {margin ? <span className="flex items-center gap-1"><Clock size={12}/>Departure in {Math.round(margin/60)}h {margin%60}m</span> : null}
      </div>

      {/* Reason */}
      <Textarea placeholder="Reason for reject (optional but recommended)..." value={reason} onChange={(e)=>setReason(e.target.value)} className="min-h-[40px] text-xs"/>

      {/* Modify — HITL-1 only */}
      {isHitl1 && showModify && (
        <div className="rounded-md border p-3 space-y-2 bg-muted/30">
          <p className="text-xs font-medium flex items-center gap-1"><Edit3 size={12}/>Modify split</p>
          <label className="text-xs">Road containers (0-120)
            <input type="number" min={0} max={120} value={modRoad} onChange={(e)=>setModRoad(e.target.value)} placeholder={`${roadC}`} className="mt-1 w-full rounded-md border px-2 py-1 text-xs"/>
          </label>
          <p className="text-xs text-muted-foreground">Sea will be {modRoad ? (120 - parseInt(modRoad||'0',10)) : seaC} containers.</p>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-2">
        <Button size="sm" variant="destructive" disabled={loading} onClick={()=>handleDecision('reject')} className="h-7 text-xs gap-1"><XCircle size={12}/>Reject</Button>
        {isHitl1 && <Button size="sm" variant="outline" disabled={loading} onClick={()=> setShowModify(v=>!v)} className="h-7 text-xs gap-1"><Edit3 size={12}/>{showModify?'Cancel':'Modify'}</Button>}
        {isHitl1 && showModify ? (
          <Button size="sm" disabled={loading || !modRoad} onClick={()=>handleDecision('modify')} className="h-7 text-xs bg-amber-600 hover:bg-amber-700 text-white">Submit Modify</Button>
        ) : (
          <Button size="sm" disabled={loading} onClick={()=>handleDecision('approve')} className="h-7 text-xs gap-1 ml-auto"><CheckCircle2 size={12}/>Approve</Button>
        )}
      </div>
    </div>
  );
}
