import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useState, useEffect } from 'react';
import { hitlRespond } from '@/api/nexus';
import { Badge } from '@/components/ui/badge';
import { Clock, Shield, AlertTriangle, CheckCircle2, XCircle, Edit3 } from 'lucide-react';

function humanRisk(raw: string): string {
  const map: Record<string, string> = {
    'road_congestion_delay': 'Road congestion',
    'road_congestion': 'Road congestion',
    'moderate': 'Moderate',
    'low': 'Low',
    'high': 'High',
    'berth_conflict': 'Berth conflict',
    'feeder_delay': 'Feeder delay',
    'low_risk': 'Low risk',
    'medium_risk': 'Medium risk',
    'high_risk': 'High risk',
  };
  return map[raw] || raw.split('_').map(w => w[0].toUpperCase() + w.slice(1)).join(' ');
}

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
function fmtPct(baseline: number, total: number) { if (!baseline) return ''; const s = baseline - total; const p = (s/baseline)*100; return `${s>=0?'↓':''}${s>=0?'+':''}${fmtMoney(Math.abs(s))} (${p>=0?'save':'over'} ${Math.abs(p).toFixed(1)}%)`; }

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
      const payload: Record<string, unknown> = { decision, gate_id: gate!.gate_id, reason: reason || undefined };
      if (mods) (payload as Record<string, unknown>).modifications = mods;
      // Use hitlRespond wrapper that sends correct shape; for modify we need modifications field
      const res = await hitlRespond(runId, decision, gate!.gate_id, reason || undefined);
      // If modify with custom road, do a second modify with modifications is not wired via hitlRespond wrapper — we cheat by direct fetch
      if (decision === 'modify' && mods) {
        await fetch('/agent/hitl/respond', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ run_id: runId, decision: 'modify', gate_id: gate!.gate_id, reason, modifications: mods }) });
      }
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
  const opt = (d.optimal_split as Record<string, unknown>) || (d.cost_breakdown as Record<string, unknown>)?.optimal_split as Record<string, unknown> || null;
  const vs = (d.cost_vs_baseline as Record<string, unknown>) || (d.cost_breakdown as Record<string, unknown>)?.cost_vs_baseline as Record<string, unknown> || null;
  const alts = (d.alternatives as Record<string, unknown>[]) || (d.cost_breakdown as Record<string, unknown>)?.alternatives as Record<string, unknown>[] || [];
  const conf = (d.confidence as number) ?? null;
  const risk = (d.risk_score as number) ?? null;
  const margin = (d.margin_minutes as number) ?? 0;
  const timeoutSec = (d.timeout_seconds as number) ?? 900;
  const timeoutAct = (d.timeout_action as string) ?? '';

  const roadC = (opt?.road_containers as number) ?? 0;
  const seaC = (opt?.sea_containers as number) ?? 0;
  const roadCost = (opt?.road_cost as number) ?? 0;
  const seaCost = (opt?.sea_terminal_handling_cost as number) ?? 0;
  const total = (opt?.total_transport_cost as number) ?? 0;
  const baseline = (vs?.baseline_all_road_cost as number) ?? 0;
  const savings = baseline ? baseline - total : 0;

  return (
    <div className="rounded-xl border bg-card p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">{meta.step}</Badge>
          <h3 className="text-sm font-semibold">{gate.gate_id}: {meta.title}</h3>
        </div>
        <Badge variant="destructive" className="text-xs animate-pulse">Approval Required</Badge>
      </div>

      <div className="rounded-lg bg-muted/50 p-3 space-y-1">
        <p className="text-xs font-medium flex items-center gap-1.5"><CheckCircle2 size={12}/>{meta.what}</p>
        {meta.why && <p className="text-xs text-muted-foreground">{meta.why}</p>}
        <p className="text-xs text-muted-foreground flex items-center gap-1"><Clock size={12}/>Gate: {gate.gate_name} • Timeout {Math.round(timeoutSec/60)}m → {timeoutAct} {meta.timeoutHint && `• ${meta.timeoutHint}`}</p>
      </div>

      {opt && (
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="rounded-lg border p-2">
            <p className="text-xs text-muted-foreground">Road</p>
            <p className="text-sm font-bold">{roadC} cont</p>
            <p className="text-xs text-muted-foreground">{opt.road_breakdown as string || `${opt.road_trips} trips`}</p>
            <p className="text-xs font-medium">{fmtMoney(roadCost)}</p>
          </div>
          <div className="rounded-lg border p-2">
            <p className="text-xs text-muted-foreground">Sea</p>
            <p className="text-sm font-bold">{seaC} cont</p>
            <p className="text-xs text-muted-foreground">{seaCost === 0 ? 'Charter $0 (scheduled)' : fmtMoney(seaCost)}</p>
          </div>
          <div className="rounded-lg border-2 border-primary p-2 bg-primary/5">
            <p className="text-xs text-muted-foreground">Total</p>
            <p className="text-sm font-bold">{fmtMoney(total)}</p>
            <p className="text-xs">{savings>0?`Save ${fmtMoney(savings)}`:`+${fmtMoney(-savings)}`}</p>
            <p className="text-xs text-emerald-600">{fmtPct(baseline,total)}</p>
          </div>
        </div>
      )}

      {baseline>0 && (
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <AlertTriangle size={12} className="text-amber-500"/>
          Baseline: {vs?.baseline_all_road_trips as number} all-road trips = {fmtMoney(baseline)}
        </div>
      )}

      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span className="flex items-center gap-1"><Shield size={12} className={risk !== null && risk > 0.7 ? 'text-red-500' : risk !== null && risk > 0.4 ? 'text-amber-500' : 'text-emerald-500'}/>{risk!==null?`${(risk*100).toFixed(0)}% risk`:'—'}</span>
        <span className="flex items-center gap-1">{conf!==null?`${(conf*100).toFixed(0)}% conf`:'—'}</span>
        {margin && <span className="flex items-center gap-1"><Clock size={12}/>{Math.round(margin/60)}h {margin%60}m</span>}
      </div>

      {alts.length>0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold">If you reject — alternatives the agent will propose:</p>
          <div className="grid gap-2">
            {alts.slice(0,2).map((a, i) => (
              <div key={i} className="rounded-md border p-2 text-xs flex justify-between items-center">
                <div>
                  <p className="font-medium">{String(a.road_containers)} road + {String(a.sea_containers)} sea • {fmtMoney(a.total_transport_cost as number)}</p>
                  <p className="text-muted-foreground">{String(a.road_breakdown)}</p>
                </div>
                <Badge variant={ String(a.risk).includes('congest') ? 'secondary' : 'outline'} className="text-xs">{humanRisk(String(a.risk))}</Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      <Textarea placeholder="Reason for reject/modify (optional but recommended)..." value={reason} onChange={(e)=>setReason(e.target.value)} className="min-h-[50px] text-xs"/>

      {showModify && (
        <div className="rounded-md border p-3 space-y-2 bg-muted/30">
          <p className="text-xs font-medium flex items-center gap-1"><Edit3 size={12}/>Modify split</p>
          <label className="text-xs">Road containers (0-120)
            <input type="number" min={0} max={120} value={modRoad} onChange={(e)=>setModRoad(e.target.value)} placeholder={`${roadC}`} className="mt-1 w-full rounded-md border px-2 py-1 text-xs"/>
          </label>
          <p className="text-xs text-muted-foreground">Sea will be {modRoad ?  (120 - parseInt(modRoad||'0',10)) : seaC} containers. Validation checks LTA chassis & feeder capacity.</p>
        </div>
      )}

      <div className="flex gap-2">
        <Button size="sm" variant="destructive" disabled={loading} onClick={()=>handleDecision('reject')} className="h-7 text-xs gap-1"><XCircle size={12}/>Reject</Button>
        <Button size="sm" variant="outline" disabled={loading} onClick={()=> setShowModify(v=>!v)} className="h-7 text-xs gap-1"><Edit3 size={12}/>{showModify?'Cancel':'Modify'}</Button>
        {showModify ? <Button size="sm" disabled={loading || !modRoad} onClick={()=>handleDecision('modify')} className="h-7 text-xs bg-amber-600 hover:bg-amber-700 text-white">Submit Modify</Button> : <Button size="sm" disabled={loading} onClick={()=>handleDecision('approve')} className="h-7 text-xs gap-1 ml-auto"><CheckCircle2 size={12}/>Approve</Button>}
      </div>
    </div>
  );
}
