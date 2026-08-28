export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface ContainerData {
  containers: Array<{
    id: string;
    status: string;
    type: string;
    weight_tonnes: number;
    destination: string;
  }>;
  total: number;
  summary: Record<string, number>;
}

export interface TruckData {
  available: number;
  total: number;
  capacity_tonnes: number;
  breakdown: Record<string, number>;
}

export interface FeederData {
  vessel_id: string;
  name: string;
  status: string;
  eta: string;
  capacity_teu: number;
  current_load: number;
  containers_onboard: number;
  route: string;
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
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export async function startDemo(scenario?: string, problemId?: string) {
  return apiFetch<{ run_id: string }>('/agent/run-demo', {
    method: 'POST',
    body: JSON.stringify({
      scenario: scenario || undefined,
      problem_id: problemId || undefined,
    }),
  });
}

export async function getActiveProblem() {
  return apiFetch<ProblemInfo>('/agent/active-problem');
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

export async function getFeederData() {
  return apiFetch<FeederData>('/api/feeder/FEEDER%20ATLANTIC-03');
}

export async function getLoadingSequence() {
  return apiFetch<LoadingSequence>('/api/citos/tuas/loading-sequence', {
    method: 'POST',
  });
}

export async function getRunHistory() {
  return apiFetch<RunRecord[]>('/webhook/runs');
}

export async function getAgentTrace(runId: string) {
  return apiFetch<AgentTraceStep[]>(`/agent/trace/${encodeURIComponent(runId)}`);
}

export async function hitlRespond(
  runId: string,
  decision: string,
  gateId: string,
  reason?: string
) {
  return apiFetch<{ status: string }>('/agent/hitl/respond', {
    method: 'POST',
    body: JSON.stringify({
      run_id: runId,
      decision,
      gate_id: gateId,
      reason: reason || undefined,
    }),
  });
}

export async function injectEdgeCase(caseType: string, minutes?: number) {
  return apiFetch<{ status: string }>('/agent/inject-edge-case', {
    method: 'POST',
    body: JSON.stringify({
      case: caseType,
      minutes: minutes || undefined,
    }),
  });
}

export async function resetMocks() {
  return apiFetch<{ status: string }>('/agent/reset-mocks', { method: 'POST' });
}

export async function getScenarios() {
  return apiFetch<Scenario[]>('/agent/scenarios');
}
