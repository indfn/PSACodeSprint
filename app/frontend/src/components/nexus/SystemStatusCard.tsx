import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
const statusLabel: Record<string, string> = { green: 'Healthy', amber: 'Attention', red: 'Conflict' };

export default function SystemStatusCard({ name, metric, value, max, status, detail, tooltip }: SystemStatusCardProps) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <Card size="sm">
      <CardHeader className="pb-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <CardTitle className="text-xs font-medium">{name}</CardTitle>
            {tooltip && <TooltipProvider><Tooltip><TooltipTrigger><HelpCircle size={10} className="text-muted-foreground"/></TooltipTrigger><TooltipContent className="max-w-[240px] text-xs">{tooltip}</TooltipContent></Tooltip></TooltipProvider>}
          </div>
          <span className={`h-2.5 w-2.5 rounded-full ${statusColors[status]}`} title={statusLabel[status]}/>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground mb-1">{metric}</p>
        {detail && <p className="text-xs text-muted-foreground mb-2">{detail}</p>}
        <Progress value={pct} className="h-1.5" />
      </CardContent>
    </Card>
  );
}
