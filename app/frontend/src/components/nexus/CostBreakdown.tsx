import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { HelpCircle, TrendingDown, TrendingUp, Ship, Truck } from 'lucide-react';

interface Alternative { road_containers: number; sea_containers: number; total_transport_cost: number; road_breakdown: string; risk: string; road_cost: number; sea_terminal_handling_cost: number; }

interface CostBreakdownProps {
  roadCost: number;
  seaHandling: number;
  total: number;
  baseline: number;
  alternatives: string[];
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
    'low_risk': 'Low risk',
    'medium_risk': 'Medium risk',
    'high_risk': 'High risk',
  };
  return map[raw] || raw.split('_').map(w => w[0].toUpperCase() + w.slice(1)).join(' ');
}

export default function CostBreakdown({ roadCost, seaHandling, total, baseline, alternatives }: CostBreakdownProps) {
  const savings = baseline - total;
  const pct = baseline ? (savings / baseline) * 100 : 0;
  const parsedAlts: Alternative[] = alternatives.map(parseAlt).filter(Boolean) as Alternative[];

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
            <p className="text-sm font-bold">${roadCost.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground">{roadCost ? `${Math.round(roadCost/150)} trips × $150` : '—'}</p>
          </div>
          <div className="rounded-lg border p-2">
            <p className="text-xs text-muted-foreground flex items-center gap-1"><Ship size={12}/>Sea handling</p>
            <p className="text-sm font-bold">${seaHandling.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground">$35 × {seaHandling ? Math.round(seaHandling/35) : 0} sea containers</p>
          </div>
        </div>
        <div className="flex justify-between items-center border-t pt-2">
          <span className="text-sm font-medium">Optimised total</span><span className="text-sm font-bold">${total.toLocaleString()}</span>
        </div>
        {baseline > 0 && (
          <div className="rounded-md bg-muted/50 p-2 space-y-1">
            <div className="flex justify-between text-xs"><span className="text-muted-foreground">Baseline (all-road)</span><span className="font-medium">${baseline.toLocaleString()}</span></div>
            <div className="flex items-center gap-2 text-xs">
              {savings >= 0 ? <TrendingDown size={12} className="text-emerald-500"/> : <TrendingUp size={12} className="text-red-500"/>}
              <span className={savings>=0?'text-emerald-600 font-medium':'text-red-600 font-medium'}>{savings>=0?'Save': 'Over'} ${Math.abs(savings).toLocaleString()} ({Math.abs(pct).toFixed(1)}%)</span>
              <Badge variant={savings>=0?'secondary':'destructive'} className="text-xs ml-auto">{savings>=0?'↓ cheaper':'↑ pricier'}</Badge>
            </div>
          </div>
        )}

        {parsedAlts.length > 0 && (
          <div className="space-y-1">
            <div className="rounded-md border overflow-hidden">
              <div className="grid grid-cols-[1fr_1fr_80px] gap-px bg-border text-xs">
                <div className="bg-muted p-1.5 font-medium">Road / Sea</div><div className="bg-muted p-1.5 font-medium">Cost</div><div className="bg-muted p-1.5 font-medium">Risk</div>
                {parsedAlts.map((a,i)=> (
                  <>
                    <div key={`r${i}`} className="bg-card p-1.5">{a.road_containers} / {a.sea_containers}</div>
                    <div key={`c${i}`} className="bg-card p-1.5 font-medium">${a.total_transport_cost.toLocaleString()}</div>
                    <div key={`k${i}`} className="bg-card p-1.5"><Badge variant={a.risk.includes('congest')?'secondary':'outline'} className="text-xs">{humanRisk(a.risk)}</Badge></div>
                  </>
                ))}
              </div>
            </div>
          </div>
        )}
        {alternatives.length>0 && parsedAlts.length===0 && (
          <div className="space-y-1"><p className="text-xs font-medium">Alternatives</p>{alternatives.map((a,i)=> <p key={i} className="text-xs">• {a.slice(0,120)}</p>)}</div>
        )}
      </CardContent>
    </Card>
  );
}
