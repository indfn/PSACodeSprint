import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface SystemStatusCardProps {
  name: string;
  metric: string;
  value: number;
  max: number;
  status: 'green' | 'amber' | 'red';
}

const statusColors: Record<string, string> = {
  green: 'bg-emerald-500',
  amber: 'bg-amber-500',
  red: 'bg-red-500',
};

export default function SystemStatusCard({
  name,
  metric,
  value,
  max,
  status,
}: SystemStatusCardProps) {
  const pct = max > 0 ? (value / max) * 100 : 0;

  return (
    <Card size="sm">
      <CardHeader className="pb-1">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-medium">{name}</CardTitle>
          <span className={`h-2.5 w-2.5 rounded-full ${statusColors[status]}`} />
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground mb-2">{metric}</p>
        <Progress value={pct} className="h-1.5" />
      </CardContent>
    </Card>
  );
}
