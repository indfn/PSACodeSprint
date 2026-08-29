export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface ContainerData {
  status: string;
  vessel_id: string;
  total_containers: number;
  total_teu: number;
  container_breakdown: Record<string, number>;
  dg_containers: number;
  reefer_containers: number;
  blocks_affected: string[];
  data_age_minutes: number;
}

export interface TruckData {
  status: string;
  terminal: string;
  available_trucks: number;
  total_fleet: number;
  transit_time_minutes: number;
  road_conditions: Record<string, string>;
  cost_per_trip: number;
  estimated_round_trip_minutes: number;
}

export interface FeederData {
  status: string;
  feeder_id: string;
  feeder_operator: string;
  capacity_teu: number;
  current_occupancy_teu: number;
  berth_status: string;
  departure_window: {
    earliest: string;
    latest: string;
    requested: string;
  };
  downstream_constraints: {
    destination_port: string;
    tidal_window: string;
    transit_time_hours: number;
    must_depart_by: string;
  };
  hold_cost_per_hour: number;
  available_capacity_teu: number;
}

export interface QcData {
  berth_id: string;
  qc_count: number;
  qc_status: Array<{ qc_id: string; status: string }>;
  crane_status: Record<string, string>;
  timestamp: string;
}

export interface RunRecord {
  run_id: string;
  problem_id: string;
  status: string;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  scenario?: string;
  summary?: string;
}

export interface AgentTraceStep {
  step: number;
  action: string;
  timestamp: string;
  detail?: string;
  type: 'tool' | 'hitl' | 'complete' | 'escalation' | 'info';
}

export interface LoadingSequence {
  sequence: Array<{
    container_id: string;
    bay: number;
    timestamp: string;
  }>;
}

export interface ProblemInfo {
  problem_id: string;
  name: string;
  description: string;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
}

export interface HitlGate {
  gate_id: string;
  gate_name: string;
  data: Record<string, unknown>;
}

async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {};
  const method = (options?.method || 'GET').toUpperCase();
  if (method !== 'GET' || options?.body) {
    headers['Content-Type'] = 'application/json';
  }
  const mergedHeaders = { ...headers, ...(options?.headers as Record<string, string> | undefined) };
  const res = await fetch(url, {
    ...options,
    headers: mergedHeaders,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export async function startDemo(scenario?: string, problemId?: string) {
  return apiFetch<{ run_id: string; status?: string; hitl_card?: Record<string, unknown>; scenario?: string }>('/agent/run-demo', {
    method: 'POST',
    body: JSON.stringify({
      scenario: scenario || undefined,
      problem_id: problemId || undefined,
    }),
  });
}

export async function getActiveProblem() {
  const res = await apiFetch<{ problem_id: string; active_problem_id: string; problem: ProblemInfo & { systems: string[]; tools: string[]; hitl_gates: string[] } }>('/agent/active-problem');
  return { problem_id: res.problem_id, name: res.problem?.name ?? res.problem_id, description: res.problem?.description ?? '' };
}

export async function switchProblem(problemId: string) {
  return apiFetch<{ status: string; problem_id: string }>(
    `/agent/switch-problem/${encodeURIComponent(problemId)}`,
    { method: 'POST' }
  );
}

export async function getContainerData() {
  return apiFetch<ContainerData>('/api/citos/ppt/containers');
}

export async function getTruckData() {
  return apiFetch<TruckData>('/api/optetruck/capacity');
}

export async function getFeederData(feederId?: string) {
  const id = feederId || 'FEEDER%20ATLANTIC-03';
  return apiFetch<FeederData>(`/api/feeder/${id}`);
}

export async function getQcData(berthId: string = 'B-03') {
  return apiFetch<QcData>(`/api/berth/${encodeURIComponent(berthId)}/qc`);
}

export async function getLoadingSequence() {
  return apiFetch<LoadingSequence>('/api/citos/tuas/loading-sequence', {
    method: 'POST',
  });
}

export async function getRunHistory() {
  const res = await apiFetch<{ runs: Record<string, unknown>[]; count: number }>('/webhook/runs');
  return (res.runs || []).map((r: Record<string, unknown>) => {
    const state = (r.state as Record<string, unknown>) || {};
    const trace = (state.trace as unknown[]) || (r.trace as Record<string, unknown>)?.entries as unknown[] || [];
    const firstTs = (trace[0] as Record<string, unknown>)?.timestamp as string | undefined;
    const lastTs = (trace[trace.length - 1] as Record<string, unknown>)?.timestamp as string | undefined;
    const event = (r.event as Record<string, unknown>) || (state.context as Record<string, unknown>)?.event as Record<string, unknown> || {};
    return {
      run_id: (r.run_id as string) || '',
      problem_id: (r.problem_id as string) || (state.problem_id as string) || (event.problem_id as string) || 'pb-12-itt',
      status: (r.status as string) || (state.status as string) || 'unknown',
      started_at: firstTs || (r as Record<string, unknown>).started_at as string || new Date().toISOString(),
      completed_at: lastTs,
      duration_seconds: undefined,
      scenario: (r.scenario as string) || (state as Record<string, unknown>).scenario as string | undefined,
      summary: (r as Record<string, unknown>).summary as string | undefined,
    } as RunRecord;
  });
}

export async function getAgentTrace(runId: string) {
  const res = await apiFetch<Record<string, unknown> | AgentTraceStep[]>(`/agent/trace/${encodeURIComponent(runId)}`);
  if (Array.isArray(res)) return res as AgentTraceStep[];
  const entries = (res.entries as Record<string, unknown>[]) || [];
  return entries.map((e: Record<string, unknown>, idx: number) => {
    const node = (e.node as string) || 'info';
    const action = (e.action as string) || `${node}:${e.action}`;
    const typeMap: Record<string, AgentTraceStep['type']> = { tool: 'tool', hitl: 'hitl', escalation: 'escalation', monitor: 'info', agent: 'info', graph: 'complete' };
    return {
      step: idx + 1,
      action: action,
      timestamp: (e.timestamp as string) || new Date().toISOString(),
      detail: JSON.stringify((e.result as unknown) || e, null, 2).slice(0, 800),
      type: typeMap[node] || 'info',
    } as AgentTraceStep;
  });
}

export async function hitlRespond(
  runId: string,
  decision: string,
  gateId: string,
  reason?: string
) {
  return apiFetch<{ status: string; hitl_card?: Record<string, unknown>; hitl_pending?: Record<string, unknown> }>('/agent/hitl/respond', {
    method: 'POST',
    body: JSON.stringify({
      run_id: runId,
      decision,
      gate_id: gateId,
      reason: reason || undefined,
    }),
  });
}

export async function injectEdgeCase(caseType: string, minutes?: number, runId?: string) {
  return apiFetch<{ status: string }>('/agent/inject-edge-case', {
    method: 'POST',
    body: JSON.stringify({
      case: caseType,
      minutes: minutes || undefined,
      run_id: runId || undefined,
    }),
  });
}

export async function resetMocks() {
  return apiFetch<{ status: string }>('/agent/reset-mocks', { method: 'POST' });
}

export async function getScenarios() {
  const res = await apiFetch<{ problem_id: string; scenarios: Scenario[] }>('/agent/scenarios');
  return res.scenarios;
}

export async function initializeSession() {
  return apiFetch<{
    problem_id: string;
    scenario: string;
    containers: ContainerData;
    trucks: TruckData;
    feeder: FeederData;
    qc: QcData;
  }>('/agent/initialize', { method: 'POST' });
}

// ---- Problem Registry (Waiting Stage) ----

export interface RegistryProblem {
  problem_id: string;
  short_id: string;
  name: string;
  description: string;
  status: 'idle' | 'running' | 'completed';
}

export async function getRegistry() {
  return apiFetch<{ problems: RegistryProblem[]; active_problem: string }>('/agent/registry');
}

export async function simulateWebhook(problemId: string) {
  return apiFetch<{ run_id: string; status?: string; hitl_card?: Record<string, unknown>; problem_id: string }>(
    `/agent/simulate-webhook/${encodeURIComponent(problemId)}`,
    { method: 'POST' }
  );
}

export async function completeProblem(problemId: string) {
  return apiFetch<{ status: string; problem_id: string }>(
    `/agent/complete-problem/${encodeURIComponent(problemId)}`,
    { method: 'POST' }
  );
}

// ---- Admin ----

export interface AdminConfig {
  llm: {
    provider: string;
    model: string;
    base_url: string;
    api_type: string;
    api_key_env: string;
    fallback_provider?: string;
    fallback_model?: string;
    fallback_base_url?: string;
  };
  active_problem: {
    id: string;
    confidence_threshold: number;
  };
  provider_readiness: {
    ready: boolean;
    message: string;
  };
  api_key_status: Record<string, string>;
}

export async function adminLogin(username: string, password: string) {
  return apiFetch<{ status: string }>('/api/admin/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
    credentials: 'same-origin',
  });
}

export async function adminGetConfig() {
  return apiFetch<AdminConfig>('/api/admin/config', { credentials: 'same-origin' });
}

export async function adminInjectApiKey(provider: string, key: string) {
  return apiFetch<{ status: string; message: string }>('/api/admin/api-key', {
    method: 'POST',
    body: JSON.stringify({ provider, key }),
    credentials: 'same-origin',
  });
}
