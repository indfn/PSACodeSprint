import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { HelpCircle } from 'lucide-react';

interface SystemStatusCardProps {
  name: string;
  metric: string;
  value: number;
  max: number;
  status: 'green' | 'amber' | 'red';
  detail?: string;
  tooltip?: string;
}

const statusColors: Record<string, string> = {
  green: 'bg-emerald-500',
  amber: 'bg-amber-500',
  red: 'bg-red-500',
};

export default function SystemStatusCard({ name, metric, value, max, status, detail, tooltip }: SystemStatusCardProps) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="rounded-xl border bg-card px-3 py-2 space-y-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-medium">{name}</span>
          <span className="text-[10px] text-muted-foreground">·</span>
          <span className="text-[10px] text-muted-foreground">{metric}</span>
          {tooltip && <TooltipProvider><Tooltip><TooltipTrigger><HelpCircle size={10} className="text-muted-foreground"/></TooltipTrigger><TooltipContent className="max-w-[240px] text-xs">{tooltip}</TooltipContent></Tooltip></TooltipProvider>}
        </div>
        <span className={`h-2 w-2 rounded-full ${statusColors[status]}`}/>
      </div>
      {detail && <p className="text-[10px] text-muted-foreground">{detail}</p>}
      <Progress value={pct} className="h-1" />
    </div>
  );
}
