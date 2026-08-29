import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { HelpCircle, TrendingDown, TrendingUp, Ship, Truck, Anchor, Container } from 'lucide-react';

interface Alternative { road_containers: number; sea_containers: number; total_transport_cost: number; road_breakdown: string; risk: string; road_cost: number; sea_terminal_handling_cost: number; }

interface CostBreakdownProps {
  roadCost: number;
  seaHandling: number;
  total: number;
  baseline: number;
  alternatives: string[];
  hitlGateId?: string | null;
  hitlData?: Record<string, unknown> | null;
}

function parseAlt(alt: string): Alternative | null {
  try { const o = JSON.parse(alt); if (typeof o.road_containers === 'number') return o as Alternative; } catch {}
  return null;
}

function humanRisk(raw: string): string {
  const map: Record<string, string> = {
    'road_congestion_delay': 'Road congestion',
    'road_congestion': 'Road congestion',
    'moderate': 'Moderate',
    'low': 'Low',
    'high': 'High',
    'berth_conflict': 'Berth conflict',
    'feeder_delay': 'Feeder delay',
  };
  return map[raw] || raw.split('_').map(w => w[0].toUpperCase() + w.slice(1)).join(' ');
}

function fmtMoney(n: number) { return `$${Math.round(n).toLocaleString()}`; }
function fmtTime(iso: string) { try { return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }); } catch { return iso; } }

export default function CostBreakdown({ roadCost, seaHandling, total, baseline, alternatives, hitlGateId, hitlData }: CostBreakdownProps) {
  const savings = baseline - total;
  const pct = baseline ? (savings / baseline) * 100 : 0;
  const parsedAlts: Alternative[] = alternatives.map(parseAlt).filter(Boolean) as Alternative[];
  const gid = hitlGateId?.toLowerCase().replace('-', '_') || '';
  const d = hitlData || {};

  // HITL-2: Dispatch summary
  if (gid === 'hitl_2' && d.dispatch) {
    const disp = d.dispatch as Record<string, unknown>;
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2"><Truck size={14}/>Dispatch</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="rounded-lg border p-2">
              <p className="text-muted-foreground">Trucks</p>
              <p className="text-sm font-bold">{String(disp.num_trucks)}</p>
            </div>
            <div className="rounded-lg border p-2">
              <p className="text-muted-foreground">Trips</p>
              <p className="text-sm font-bold">{String(disp.total_trips)}</p>
            </div>
          </div>
          <div className="text-xs text-muted-foreground">Route: {String(disp.route)}</div>
          {String(disp.eta || '') && <div className="text-xs text-muted-foreground">ETA: {fmtTime(String(disp.eta))}</div>}
          <div className="flex justify-between items-center border-t pt-2 text-xs">
            <span className="text-muted-foreground">Dispatch cost</span>
            <span className="font-bold">{fmtMoney(disp.dispatch_cost as number)}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // HITL-3: Feeder hold summary
  if (gid === 'hitl_3' && d.feeder_hold) {
    const hold = d.feeder_hold as Record<string, unknown>;
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2"><Anchor size={14}/>Feeder Hold</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="rounded-lg border p-2">
              <p className="text-muted-foreground">Duration</p>
              <p className="text-sm font-bold">{String(hold.hold_hours)}h</p>
            </div>
            <div className="rounded-lg border p-2">
              <p className="text-muted-foreground">Cost</p>
              <p className="text-sm font-bold">{fmtMoney(hold.hold_cost as number)}</p>
            </div>
          </div>
          <div className="text-xs text-muted-foreground">Rate: {fmtMoney(hold.hold_cost_per_hour as number)}/hr</div>
          {String(hold.previous_departure || '') && String(hold.new_departure || '') && (
            <div className="text-xs text-muted-foreground">
              Departure: {fmtTime(String(hold.previous_departure))} → {fmtTime(String(hold.new_departure))}
            </div>
          )}
          <div className="flex items-center gap-1 text-xs">
            <span className="text-muted-foreground">Tidal:</span>
            <Badge variant={hold.tidal_risk === 'critical' ? 'destructive' : hold.tidal_risk === 'marginal' ? 'secondary' : 'outline'} className="text-[10px]">{String(hold.tidal_risk)}</Badge>
          </div>
        </CardContent>
      </Card>
    );
  }

  // HITL-4: Tuas sequence summary
  if (gid === 'hitl_4' && d.tuas_sequence) {
    const seq = d.tuas_sequence as Record<string, unknown>;
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2"><Container size={14}/>Tuas Sequence</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="text-xs text-muted-foreground">Vessel: {String(seq.vessel_id)}</div>
          {String(seq.updated_loading_sequence || '') && (
            <div className="text-[10px] font-mono bg-muted/50 rounded p-2">{String(seq.updated_loading_sequence)}</div>
          )}
          {Array.isArray(seq.qc_adjustments) && (
            <div className="space-y-1 text-xs">
              {(seq.qc_adjustments as Record<string, unknown>[]).map((q, i) => (
                <div key={i} className="flex items-center gap-1">
                  <span className="font-medium">{String(q.qc_id)}</span>
                  <span className="text-muted-foreground">→ {String(q.new_bay)}</span>
                </div>
              ))}
            </div>
          )}
          <div className="flex justify-between items-center border-t pt-2 text-xs text-muted-foreground">
            <span>Completion: {seq.estimated_loading_completion ? fmtTime(String(seq.estimated_loading_completion)) : '—'}</span>
            <span>Margin: {String(seq.margin_before_departure_minutes)}m</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Default: HITL-1 / HITL-5 / no gate — cost split view
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">Cost Breakdown
          <TooltipProvider><Tooltip><TooltipTrigger><HelpCircle size={12} className="text-muted-foreground"/></TooltipTrigger><TooltipContent className="max-w-[260px] text-xs">Baseline = all-road cost if every container went by truck (road trips × $150). Optimised mixes road + scheduled feeder (sea has $0 charter, only $35 handling per container). Savings is transport-only.</TooltipContent></Tooltip></TooltipProvider>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-lg border p-2">
            <p className="text-xs text-muted-foreground flex items-center gap-1"><Truck size={12}/>Road</p>
            <p className="text-sm font-bold">{fmtMoney(roadCost)}</p>
            <p className="text-xs text-muted-foreground">{roadCost ? `${Math.round(roadCost/150)} trips × $150` : '—'}</p>
          </div>
          <div className="rounded-lg border p-2">
            <p className="text-xs text-muted-foreground flex items-center gap-1"><Ship size={12}/>Sea handling</p>
            <p className="text-sm font-bold">{fmtMoney(seaHandling)}</p>
            <p className="text-xs text-muted-foreground">$35 × {seaHandling ? Math.round(seaHandling/35) : 0} sea containers</p>
          </div>
        </div>
        <div className="flex justify-between items-center border-t pt-2">
          <span className="text-sm font-medium">Optimised total</span><span className="text-sm font-bold">{fmtMoney(total)}</span>
        </div>
        {baseline > 0 && (
          <div className="rounded-md bg-muted/50 p-2 space-y-1">
            <div className="flex justify-between text-xs"><span className="text-muted-foreground">Baseline (all-road)</span><span className="font-medium">{fmtMoney(baseline)}</span></div>
            <div className="flex items-center gap-2 text-xs">
              {savings >= 0 ? <TrendingDown size={12} className="text-emerald-500"/> : <TrendingUp size={12} className="text-red-500"/>}
              <span className={savings>=0?'text-emerald-600 font-medium':'text-red-600 font-medium'}>{savings>=0?'Save': 'Over'} ${Math.abs(savings).toLocaleString()} ({Math.abs(pct).toFixed(1)}%)</span>
              <Badge variant={savings>=0?'secondary':'destructive'} className="text-xs ml-auto">{savings>=0?'↓ cheaper':'↑ pricier'}</Badge>
            </div>
          </div>
        )}

        {parsedAlts.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">Alternative splits</p>
            <div className="rounded-md border overflow-hidden">
              <div className="grid grid-cols-[auto_auto_1fr] gap-px bg-border text-xs">
                <div className="bg-muted p-1.5 font-medium">Road / Sea</div><div className="bg-muted p-1.5 font-medium">Cost</div><div className="bg-muted p-1.5 font-medium">Risk</div>
                {parsedAlts.map((a,i)=> (
                  <React.Fragment key={i}>
                    <div className="bg-card p-1.5">{a.road_containers} / {a.sea_containers}</div>
                    <div className="bg-card p-1.5 font-medium">{fmtMoney(a.total_transport_cost)}</div>
                    <div className="bg-card p-1.5"><Badge variant={a.risk.includes('congest')?'secondary':'outline'} className="text-xs">{humanRisk(a.risk)}</Badge></div>
                  </React.Fragment>
                ))}
              </div>
            </div>
          </div>
        )}
        {alternatives.length>0 && parsedAlts.length===0 && (
          <div className="space-y-1"><p className="text-xs font-medium text-muted-foreground">Alternative splits</p>{alternatives.map((a,i)=> <p key={i} className="text-xs">• {a.slice(0,120)}</p>)}</div>
        )}
      </CardContent>
    </Card>
  );
}

