import { Radio, Webhook } from 'lucide-react';

interface EventCardProps {
  eventId: string | null;
  eventData: Record<string, unknown> | null;
}

export default function EventCard({ eventId, eventData }: EventCardProps) {
  if (!eventId) {
    return (
      <div className="rounded-xl border bg-card p-4 space-y-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Radio size={14} className="animate-pulse" />
          <span className="text-sm font-semibold">Event</span>
        </div>
        <p className="text-xs text-muted-foreground">
          No event received. Use the controls above to simulate a webhook event.
        </p>
      </div>
    );
  }

  const source = (eventData?.source as string) || 'CITOS_PPT';
  const eventType = (eventData?.event_type as string) || 'ITT_COORDINATION_REQUEST';
  const vesselId = (eventData?.vessel_id as string) || '—';
  const containerCount = (eventData?.container_count as number) || 0;
  const origin = (eventData?.origin_terminal as string) || 'PPT';
  const dest = (eventData?.destination_terminal as string) || 'TUAS';
  const priority = (eventData?.priority as string) || 'high';
  const requestedBy = (eventData?.requested_by as string) || '—';
  const dg = (eventData?.dg_containers as number) || 0;
  const departure = (eventData?.tuas_vessel_departure as string) || '';

  return (
    <div className="rounded-xl border bg-card p-4 space-y-3">
      <div className="flex items-center gap-2">
        <Webhook size={14} className="text-primary" />
        <span className="text-sm font-semibold">Event Received</span>
        <span className="text-[10px] font-mono text-muted-foreground ml-auto">{eventId}</span>
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
        <div>
          <span className="text-muted-foreground">Type</span>
          <span className="ml-1.5 font-medium">{eventType.replace(/_/g, ' ').toLowerCase()}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Source</span>
          <span className="ml-1.5 font-medium">{source}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Vessel</span>
          <span className="ml-1.5 font-medium">{vesselId}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Containers</span>
          <span className="ml-1.5 font-medium">{containerCount} TEU{dg > 0 ? ` (${dg} DG)` : ''}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Route</span>
          <span className="ml-1.5 font-medium">{origin} → {dest}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Priority</span>
          <span className="ml-1.5 font-medium">{priority}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Requested by</span>
          <span className="ml-1.5 font-medium">{requestedBy}</span>
        </div>
        {departure && (
          <div>
            <span className="text-muted-foreground">Departure</span>
            <span className="ml-1.5 font-medium">{departure.slice(11, 16)}</span>
          </div>
        )}
      </div>
    </div>
  );
}
