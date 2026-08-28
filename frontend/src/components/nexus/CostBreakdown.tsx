import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface CostBreakdownProps {
  roadCost: number;
  seaHandling: number;
  total: number;
  baseline: number;
  alternatives: string[];
}

export default function CostBreakdown({
  roadCost,
  seaHandling,
  total,
  baseline,
  alternatives,
}: CostBreakdownProps) {
  const savings = baseline > 0 ? ((baseline - total) / baseline) * 100 : 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Cost Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Road Cost</span>
            <span className="font-medium">${roadCost.toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Sea Handling</span>
            <span className="font-medium">${seaHandling.toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-xs border-t pt-1.5">
            <span className="font-medium">Total</span>
            <span className="font-semibold">${total.toLocaleString()}</span>
          </div>
        </div>

        {baseline > 0 && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground">vs Baseline</span>
            <span
              className={
                savings > 0 ? 'text-emerald-500 font-medium' : 'text-red-500 font-medium'
              }
            >
              {savings > 0 ? `↓ ${savings.toFixed(1)}% savings` : `↑ ${Math.abs(savings).toFixed(1)}% increase`}
            </span>
          </div>
        )}

        {alternatives.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">
              Alternatives
            </p>
            {alternatives.map((alt, i) => (
              <p key={i} className="text-xs text-foreground">
                • {alt}
              </p>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
