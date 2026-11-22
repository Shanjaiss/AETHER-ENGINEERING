import {
  HealthResponse,
  Workspace,
  Task,
  PatchDiff,
  ExecutionRun,
  QualityReportResponse,
  ConflictCheckResponse,
  FileTreeNode,
  FileContentResponse,
  CodeSearchResponse,
  BenchmarkDefinition,
  BenchmarkSummaryReport,
  BenchmarkRunItem,
  SettingsResponse,
  TaskUnderstandingResult,
  DependencyGraphResponse,
  CrossFileSymbolMap,
  CallSiteItem,
  ChangeImpactReport,
  AblationStudyReport,
  ModelComparisonReport,
  SecurityBenchmarkReport,
  SWEBenchStatus,
  UserResponse,
  TokenResponse,
  AuditLogItem
} from '../types';

const API_BASE = '/api/v1';

export function getAuthToken(): string | null {
  try {
    return localStorage.getItem('aether_token');
  } catch {
    return null;
  }
}

export function setAuthToken(token: string): void {
  try {
    localStorage.setItem('aether_token', token);
  } catch {
    // ignore
  }
}

export function clearAuthToken(): void {
  try {
    localStorage.removeItem('aether_token');
  } catch {
    // ignore
  }
}

function getAuthHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const headers: Record<string, string> = { ...extraHeaders };
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = 'Network request failed';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.error || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }
  if (response.status === 204) {
    return {} as T;
  }
  return response.json();
}

export const api = {
  // System Health
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<HealthResponse>(res);
  },

  // Workspaces
  async getWorkspaces(): Promise<Workspace[]> {
    const res = await fetch(`${API_BASE}/workspaces/`);
    return handleResponse<Workspace[]>(res);
  },

  async createWorkspace(data: { name: string; path: string; metadata_json?: Record<string, any> }): Promise<Workspace> {
    const res = await fetch(`${API_BASE}/workspaces/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<Workspace>(res);
  },

  async getWorkspace(id: string): Promise<Workspace> {
    const res = await fetch(`${API_BASE}/workspaces/${id}`);
    return handleResponse<Workspace>(res);
  },

  async deleteWorkspace(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/workspaces/${id}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res);
  },

  // Tasks
  async getTasks(workspaceId?: string): Promise<Task[]> {
    const url = workspaceId
      ? `${API_BASE}/tasks/?workspace_id=${encodeURIComponent(workspaceId)}`
      : `${API_BASE}/tasks/`;
    const res = await fetch(url);
    return handleResponse<Task[]>(res);
  },

  async getTask(id: string): Promise<Task> {
    const res = await fetch(`${API_BASE}/tasks/${id}`);
    return handleResponse<Task>(res);
  },

  async createTask(data: { workspace_id: string; title: string; description: string }): Promise<Task> {
    const res = await fetch(`${API_BASE}/tasks/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<Task>(res);
  },

  async cancelTask(taskId: string): Promise<Task> {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/cancel`, {
      method: 'POST',
    });
    return handleResponse<Task>(res);
  },

  async analyzeTask(taskId: string): Promise<TaskUnderstandingResult> {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/analyze`, {
      method: 'POST',
    });
    return handleResponse<TaskUnderstandingResult>(res);
  },

  async analyzeRequirement(data: { title: string; description: string; workspace_id?: string }): Promise<TaskUnderstandingResult> {
    const res = await fetch(`${API_BASE}/tasks/analyze-requirement`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<TaskUnderstandingResult>(res);
  },

  // Planning Engine
  async generatePlan(taskId: string): Promise<Task> {
    const res = await fetch(`${API_BASE}/planning/${taskId}/generate`, {
      method: 'POST',
    });
    return handleResponse<Task>(res);
  },

  async approvePlan(taskId: string, decision: 'APPROVED' | 'REJECTED', notes?: string): Promise<Task> {
    const res = await fetch(`${API_BASE}/planning/${taskId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, notes }),
    });
    return handleResponse<Task>(res);
  },

  // Coding Engine
  async executeCoding(taskId: string): Promise<Task> {
    const res = await fetch(`${API_BASE}/coding/${taskId}/execute`, {
      method: 'POST',
    });
    return handleResponse<Task>(res);
  },

  async rollbackCoding(taskId: string): Promise<Task> {
    const res = await fetch(`${API_BASE}/coding/${taskId}/rollback`, {
      method: 'POST',
    });
    return handleResponse<Task>(res);
  },

  async getDiffs(taskId: string): Promise<PatchDiff[]> {
    const res = await fetch(`${API_BASE}/coding/${taskId}/diffs`);
    return handleResponse<PatchDiff[]>(res);
  },

  // Verification & Self-Debugging
  async runVerification(taskId: string): Promise<Task> {
    const res = await fetch(`${API_BASE}/verification/${taskId}/run`, {
      method: 'POST',
    });
    return handleResponse<Task>(res);
  },

  async getExecutions(taskId: string): Promise<ExecutionRun[]> {
    const res = await fetch(`${API_BASE}/verification/${taskId}/executions`);
    return handleResponse<ExecutionRun[]>(res);
  },

  // Code Review & Merge Gate
  async getQualityReport(taskId: string): Promise<QualityReportResponse> {
    const res = await fetch(`${API_BASE}/review/${taskId}/report`);
    return handleResponse<QualityReportResponse>(res);
  },

  async checkConflicts(taskId: string): Promise<ConflictCheckResponse> {
    const res = await fetch(`${API_BASE}/review/${taskId}/conflicts`);
    return handleResponse<ConflictCheckResponse>(res);
  },

  async submitReviewDecision(taskId: string, decision: 'APPROVED' | 'REJECTED', notes?: string): Promise<Task> {
    const res = await fetch(`${API_BASE}/review/${taskId}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, notes }),
    });
    return handleResponse<Task>(res);
  },

  async applyChanges(taskId: string): Promise<Task> {
    const res = await fetch(`${API_BASE}/review/${taskId}/apply`, {
      method: 'POST',
    });
    return handleResponse<Task>(res);
  },

  exportPatchUrl(taskId: string): string {
    return `${API_BASE}/review/${taskId}/export`;
  },

  // Repository Intelligence
  async scanRepository(workspaceId: string, path: string): Promise<any> {
    const res = await fetch(`${API_BASE}/repositories/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace_id: workspaceId, path }),
    });
    return handleResponse<any>(res);
  },

  async getRepoTree(repoId: string, maxDepth: number = 5): Promise<FileTreeNode> {
    const res = await fetch(`${API_BASE}/repositories/${repoId}/tree?max_depth=${maxDepth}`);
    return handleResponse<FileTreeNode>(res);
  },

  async getRepoFile(repoId: string, path: string): Promise<FileContentResponse> {
    const res = await fetch(`${API_BASE}/repositories/${repoId}/file?path=${encodeURIComponent(path)}`);
    return handleResponse<FileContentResponse>(res);
  },

  async searchRepo(repoId: string, query: string, maxResults: number = 30): Promise<CodeSearchResponse> {
    const res = await fetch(`${API_BASE}/repositories/${repoId}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, max_results: maxResults }),
    });
    return handleResponse<CodeSearchResponse>(res);
  },

  async getDependencies(repoId: string): Promise<DependencyGraphResponse> {
    const res = await fetch(`${API_BASE}/repositories/${repoId}/dependencies`);
    return handleResponse<DependencyGraphResponse>(res);
  },

  async getCrossFileSymbols(repoId: string): Promise<CrossFileSymbolMap[]> {
    const res = await fetch(`${API_BASE}/repositories/${repoId}/cross-file-symbols`);
    return handleResponse<CrossFileSymbolMap[]>(res);
  },

  async getCallSites(repoId: string, symbol: string): Promise<CallSiteItem[]> {
    const res = await fetch(`${API_BASE}/repositories/${repoId}/call-sites?symbol=${encodeURIComponent(symbol)}`);
    return handleResponse<CallSiteItem[]>(res);
  },

  async getChangeImpact(repoId: string, filePath: string): Promise<ChangeImpactReport> {
    const res = await fetch(`${API_BASE}/repositories/${repoId}/change-impact?file_path=${encodeURIComponent(filePath)}`);
    return handleResponse<ChangeImpactReport>(res);
  },

  // Evaluation Lab
  async getBenchmarks(category?: string, heldOutOnly?: boolean): Promise<BenchmarkDefinition[]> {
    let url = `${API_BASE}/benchmarks/`;
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (heldOutOnly !== undefined) params.append('held_out_only', String(heldOutOnly));
    const qs = params.toString();
    if (qs) url += `?${qs}`;
    const res = await fetch(url);
    return handleResponse<BenchmarkDefinition[]>(res);
  },

  async runBenchmarks(options?: {
    benchmarkIds?: string[];
    category?: string;
    heldOutOnly?: boolean;
  }): Promise<BenchmarkSummaryReport> {
    const res = await fetch(`${API_BASE}/benchmarks/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        benchmark_ids: options?.benchmarkIds,
        category: options?.category,
        held_out_only: options?.heldOutOnly,
      }),
    });
    return handleResponse<BenchmarkSummaryReport>(res);
  },

  async getBenchmarkRuns(limit: number = 50): Promise<BenchmarkRunItem[]> {
    const res = await fetch(`${API_BASE}/benchmarks/runs?limit=${limit}`);
    return handleResponse<BenchmarkRunItem[]>(res);
  },

  async runAblationStudy(sampleSize: number = 10): Promise<AblationStudyReport> {
    const res = await fetch(`${API_BASE}/benchmarks/ablation?sample_size=${sampleSize}`, {
      method: 'POST',
    });
    return handleResponse<AblationStudyReport>(res);
  },

  async runModelComparison(sampleSize: number = 5): Promise<ModelComparisonReport> {
    const res = await fetch(`${API_BASE}/benchmarks/model-comparison?sample_size=${sampleSize}`, {
      method: 'POST',
    });
    return handleResponse<ModelComparisonReport>(res);
  },

  async runSecurityBenchmark(): Promise<SecurityBenchmarkReport> {
    const res = await fetch(`${API_BASE}/benchmarks/security`, {
      method: 'POST',
    });
    return handleResponse<SecurityBenchmarkReport>(res);
  },

  async getSWEBenchStatus(): Promise<SWEBenchStatus> {
    const res = await fetch(`${API_BASE}/benchmarks/swe-bench/status`);
    return handleResponse<SWEBenchStatus>(res);
  },

  async runSWEBenchFixture(instanceId: string = 'psf__requests-2317'): Promise<any> {
    const res = await fetch(`${API_BASE}/benchmarks/swe-bench/run-fixture?instance_id=${encodeURIComponent(instanceId)}`, {
      method: 'POST',
    });
    return handleResponse<any>(res);
  },

  exportBenchmarkUrl(format: string = 'json'): string {
    return `${API_BASE}/benchmarks/export?format=${format}`;
  },

  // System Settings
  async getSettings(): Promise<SettingsResponse> {
    const res = await fetch(`${API_BASE}/settings/`);
    return handleResponse<SettingsResponse>(res);
  },

  async updateSettings(data: {
    llm_provider?: string;
    llm_model?: string;
    openai_api_key?: string;
    anthropic_api_key?: string;
    gemini_api_key?: string;
    ollama_base_url?: string;
  }): Promise<SettingsResponse> {
    const res = await fetch(`${API_BASE}/settings/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<SettingsResponse>(res);
  },

  // Authentication & RBAC
  async register(data: { email: string; password: string; full_name?: string; role?: string; tenant_id?: string }): Promise<UserResponse> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<UserResponse>(res);
  },

  async login(data: { email: string; password: string }): Promise<TokenResponse> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const tokens = await handleResponse<TokenResponse>(res);
    if (tokens && tokens.access_token) {
      setAuthToken(tokens.access_token);
    }
    return tokens;
  },

  async getCurrentUser(): Promise<UserResponse> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders(),
    });
    return handleResponse<UserResponse>(res);
  },

  async getAuditLogs(limit: number = 50): Promise<AuditLogItem[]> {
    const res = await fetch(`${API_BASE}/auth/audit-logs?limit=${limit}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse<AuditLogItem[]>(res);
  },
};
