export type TaskStatus =
  | 'PENDING'
  | 'ANALYZING'
  | 'PLANNING'
  | 'AWAITING_PLAN_APPROVAL'
  | 'CODING'
  | 'VERIFYING'
  | 'DEBUGGING'
  | 'AWAITING_DIFF_APPROVAL'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

export type GateType = 'PLAN' | 'DIFF' | 'COMMAND';
export type ApprovalStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  database_connected: boolean;
  llm_configured: boolean;
  llm_provider: string;
  details: Record<string, any>;
}

export interface Repository {
  id: string;
  workspace_id: string;
  name: string;
  path: string;
  is_git: boolean;
  default_branch: string;
  languages: Record<string, number>;
  frameworks: string[];
  file_count: string;
  created_at: string;
}

export interface Workspace {
  id: string;
  name: string;
  path: string;
  is_active: boolean;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
  repositories: Repository[];
}

export interface PlanStep {
  id: string;
  task_id: string;
  step_order: number;
  title: string;
  description: string;
  target_files: string[];
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  status: string;
  created_at: string;
}

export interface ApprovalGate {
  id: string;
  task_id: string;
  gate_type: GateType;
  proposed_payload: Record<string, any>;
  status: ApprovalStatus;
  decision_notes?: string;
  decided_at?: string;
  created_at: string;
}

export interface PatchDiff {
  id: string;
  task_id: string;
  file_path: string;
  original_content?: string;
  patched_content?: string;
  diff_text: string;
  status: string;
  created_at: string;
}

export interface ExecutionRun {
  id: string;
  task_id: string;
  phase: string;
  command: string;
  stdout: string;
  stderr: string;
  exit_code: number;
  duration_ms: number;
  status: 'SUCCESS' | 'FAILURE' | 'TIMEOUT' | 'ERROR';
  created_at: string;
}

export interface Task {
  id: string;
  workspace_id: string;
  title: string;
  description: string;
  status: TaskStatus;
  current_phase: string;
  model_used?: string;
  isolated_workspace_path?: string;
  repair_attempts: number;
  error_summary?: string;
  created_at: string;
  updated_at: string;
  plan_steps: PlanStep[];
  approvals: ApprovalGate[];
  patches: PatchDiff[];
  executions: ExecutionRun[];
}

export interface FileTreeNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size_bytes: number;
  language?: string;
  children?: FileTreeNode[];
}

export interface FileContentResponse {
  file_path: string;
  relative_path: string;
  language: string;
  line_count: number;
  size_bytes: number;
  content: string;
  truncated: boolean;
}

export interface SearchMatch {
  line_number: number;
  line_text: string;
}

export interface SearchResultItem {
  file_path: string;
  relative_path: string;
  language: string;
  matches: SearchMatch[];
}

export interface CodeSearchResponse {
  query: string;
  total_matches: number;
  results: SearchResultItem[];
}

export interface QualityReportResponse {
  task_id: string;
  total_files_changed: number;
  total_lines_added: number;
  total_lines_removed: number;
  overall_risk: 'LOW' | 'MEDIUM' | 'HIGH';
  security_warnings: string[];
  static_analysis_passed: boolean;
  test_evidence: Record<string, any>;
  summary: string;
}

export interface ConflictCheckResponse {
  has_conflicts: boolean;
  conflicted_files: string[];
  message: string;
}

export interface BenchmarkDefinition {
  id: string;
  name: string;
  language?: string;
  difficulty?: string;
  category: string;
  subcategory?: string;
  description: string;
  expected_files: string[];
  is_held_out?: boolean;
}

export interface BenchmarkTaskResult {
  task_id: string;
  name: string;
  category: string;
  subcategory: string;
  language: string;
  difficulty: string;
  model_name: string;
  outcome: 'RESOLVED' | 'UNRESOLVED' | 'PARTIAL' | 'TIMEOUT' | 'INFRASTRUCTURE_BLOCKED' | 'MODEL_ERROR' | 'POLICY_VIOLATION';
  test_passed: boolean;
  patch_applied: boolean;
  build_passed: boolean;
  original_tests_passed: boolean;
  acceptance_tests_passed: boolean;
  unrelated_files_modified: number;
  security_violations: number;
  repair_attempts: number;
  first_attempt_resolved: boolean;
  duration_seconds: number;
  model_latency_seconds: number;
  tool_latency_seconds: number;
  model_calls: number;
  tool_calls: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_usd: number;
  failure_category: string;
  failure_reason?: string;
  verification_evidence?: string;
  diff_summary?: string;
}

export interface BenchmarkRunItem {
  id: string;
  benchmark_id: string;
  name: string;
  category: string;
  model_name: string;
  test_passed: boolean;
  duration_seconds: number;
  repair_attempts: number;
  unnecessary_file_changes: number;
  security_violations: number;
  outcome?: string;
  failure_category?: string;
  created_at: string;
}

export interface BenchmarkSummaryReport {
  suite_id?: string;
  version?: string;
  timestamp?: string;
  total_tasks?: number;
  attempted_tasks?: number;
  resolved_tasks?: number;
  unresolved_tasks?: number;
  blocked_tasks?: number;
  resolution_rate_percent?: number;
  first_attempt_rate_percent?: number;
  repair_success_rate_percent?: number;
  patch_apply_rate_percent?: number;
  total_benchmarks_run?: number;
  verified_pass_rate_percent?: number;
  task_completion_rate_percent?: number;
  avg_duration_seconds: number;
  median_duration_seconds?: number;
  avg_model_latency_seconds?: number;
  total_model_calls?: number;
  total_tool_calls?: number;
  total_input_tokens?: number;
  total_output_tokens?: number;
  total_cost_usd?: number;
  avg_repair_attempts?: number;
  total_security_violations: number;
  model_name: string;
  environment: string;
  category_metrics?: Record<string, any>;
  category_breakdown?: Record<string, any>;
  failure_breakdown?: Record<string, number>;
  task_results?: BenchmarkTaskResult[];
  runs: BenchmarkRunItem[];
}

export interface AblationStudyResult {
  config_id: string;
  config_name: string;
  description: string;
  tasks_attempted: number;
  tasks_resolved: number;
  resolution_rate_percent: number;
  retrieval_accuracy_percent: number;
  regression_rate_percent: number;
  avg_duration_seconds: number;
  total_tokens: number;
  estimated_cost_usd: number;
}

export interface AblationStudyReport {
  timestamp: string;
  benchmark_suite: string;
  model_name: string;
  configurations: AblationStudyResult[];
  key_findings: string[];
}

export interface ModelComparisonEntry {
  model_identifier: string;
  provider: string;
  resolved_tasks: number;
  total_tasks: number;
  resolution_rate_percent: number;
  avg_duration_seconds: number;
  avg_model_latency_seconds: number;
  total_cost_usd: number;
  security_violations: number;
}

export interface ModelComparisonReport {
  timestamp: string;
  suite_id: string;
  models: ModelComparisonEntry[];
  summary_verdict: string;
}

export interface SecurityTestFixture {
  id: string;
  name: string;
  attack_vector: string;
  description: string;
  payload_or_command: string;
  expected_defense: string;
  prevented: boolean;
  evidence: string;
}

export interface SecurityBenchmarkReport {
  timestamp: string;
  total_fixtures: number;
  prevented_count: number;
  breached_count: number;
  prevention_rate_percent: number;
  all_prevented: boolean;
  fixtures: SecurityTestFixture[];
}

export interface SWEBenchStatus {
  system: string;
  architecture: string;
  memory_gb: number;
  docker_daemon_detected: boolean;
  is_apple_silicon_8gb: boolean;
  official_docker_harness_supported: boolean;
  adapter_mode: string;
  blocker_explanation?: string;
}

export interface SettingsResponse {
  app_name: string;
  app_version: string;
  app_env: string;
  llm_provider: string;
  llm_model: string;
  ollama_base_url: string;
  has_openai_key: boolean;
  has_anthropic_key: boolean;
  has_gemini_key: boolean;
  allowed_repo_roots: string[];
  isolated_sandbox_timeout_seconds: number;
  max_repair_attempts: number;
}

export interface AcceptanceCriterion {
  id: string;
  description: string;
  verification_type: string;
  target_area?: string;
  passed: boolean;
}

export interface AmbiguityAssessment {
  is_ambiguous: boolean;
  ambiguity_score: number;
  missing_elements: string[];
  clarification_questions: string[];
}

export interface TaskUnderstandingResult {
  task_id?: string;
  intent: 'INFORMATION_REQUEST' | 'READONLY_ANALYSIS' | 'CODE_MODIFICATION' | 'TEST_EXECUTION' | 'HIGH_RISK_OPERATION';
  category: string;
  primary_technology?: string;
  summary: string;
  target_files_hinted: string[];
  detected_dependencies: string[];
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_reasons: string[];
  requires_approval_gate: boolean;
  ambiguity: AmbiguityAssessment;
  acceptance_criteria: AcceptanceCriterion[];
  created_at?: string;
}

export interface DependencyGraphResponse {
  nodes: string[];
  edges: Array<{ source: string; target: string }>;
  dependency_counts: Record<string, number>;
  isolated_files: string[];
}

export interface CallSiteItem {
  calling_file: string;
  line_number: number;
  line_text: string;
  callee_symbol: string;
}

export interface CrossFileSymbolMap {
  symbol_name: string;
  defining_file: string;
  kind: string;
  line: number;
  docstring?: string;
  call_sites: CallSiteItem[];
}

export interface ChangeImpactReport {
  target_file: string;
  directly_impacted_files: string[];
  transitively_impacted_files: string[];
  associated_test_files: string[];
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  summary: string;
}

export interface DynamicPlanStep {
  step_order: number;
  title: string;
  description: string;
  target_files: string[];
  prerequisite_steps: number[];
  risk_level: string;
  acceptance_criteria: string[];
  verification_strategy: string;
  status: string;
}

export interface DynamicPlanOutput {
  objective: string;
  existing_implementation_analysis: string;
  required_files: string[];
  proposed_modifications: DynamicPlanStep[];
  dependencies: string[];
  acceptance_criteria: string[];
  verification_strategy: string;
  risk_level: string;
  expected_limitations: string[];
  revision_count: number;
}
