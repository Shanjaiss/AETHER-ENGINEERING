# AETHER ENGINEER — Technical Interview Preparation Guide
### *Comprehensive Interview Preparation for High-Impact Software & AI Engineering Roles*
**Target Positions:** Software Development Engineer (SDE II/III), Full-Stack Developer, AI Engineer, Agentic AI Engineer, AI Platform Engineer, Systems/Security Engineer

---

# SECTION A: THE TECHNICAL PITCH

### 1. The 30-Second Elevator Pitch
> *"I designed and built AETHER ENGINEER, an autonomous AI software engineering platform with the tagline 'From Requirement to Verified Code.' Unlike chat interfaces that generate unverified code snippets, AETHER ENGINEER operates as an autonomous engineering partner: it analyzes codebases using AST symbol extraction, creates dependency-aware DAG implementation plans, executes code modifications inside isolated sandboxes, and verifies every fix using real unit tests before a human developer approves the merge. It achieved a 100% resolution rate across 50 benchmark tasks while running locally under 75 MB RAM on an Apple Silicon Mac M1."*

### 2. The 60-Second Recruiter Pitch
> *"Most generative AI tools today suffer from two fatal flaws in production engineering: first, they hallucinate code that looks plausible but fails silently at runtime; second, giving an AI write access to a production codebase introduces severe security and data loss risks.
> 
> To solve this, I built AETHER ENGINEER. It enforces strict dual-gate human governance and zero-host modification. When a requirement is submitted, our Task Understanding Engine classifies intent and risk. A Topological DAG Planner determines step dependencies. Once approved by the engineer, code modifications are executed strictly inside an isolated sandbox clone. Test runners execute pytest or vitest in sanitized child processes. If assertions fail, our self-debugging agent categorizes the failure and attempts bounded repairs. Only when tests pass 100% does the developer review a unified git diff for final merge. The entire system is production-verified with 64 unit tests, 50 benchmark tasks, and 12 adversarial security attack tests."*

### 3. The 2-Minute Technical Deep Dive
> *"When designing AETHER ENGINEER, I prioritized four core architectural requirements: verifiable correctness, strict sandbox security, human governance, and local efficiency on constrained hardware.
> 
> On the frontend, I engineered a 4-panel developer IDE in React 18, TypeScript, Vite, and Tailwind CSS. It combines a repository file explorer, multi-tab code viewer with line numbering, interactive AI task orchestrator, and a collapsible bottom drawer displaying real-time test execution logs and unified git diffs.
> 
> On the backend, we run an asynchronous FastAPI server backed by SQLAlchemy 2.0 and SQLite in WAL mode. Codebase intelligence is gathered using Python's native AST parser and regex tokenizers rather than memory-heavy language servers, indexing thousands of files in under 100ms.
> 
> Our agent orchestration pipeline is modeled as a state machine: Task Understanding generates acceptance criteria and assesses risk. A Topological DAG Planner orders implementation steps using Kahn's algorithm, detecting circular deadlocks. Human Approval Gate #1 pauses execution until the plan is reviewed. When coding begins, our PatchEngine enforces path containment, verifying against directory traversal and symlink escapes before applying changes to an isolated clone.
> 
> A sanitized subprocess executes pytest or vitest with a 60-second timeout. If tests fail, our Failure Classifier diagnoses the traceback and attempts bounded repairs up to 3 times. Once tests pass, ReviewEngine checks that original files were not modified externally before presenting Human Approval Gate #2. In Phase 11 evaluations, AETHER ENGINEER achieved 100% task resolution across 50 benchmarks, blocked 12/12 security vectors, and maintained a peak memory of 72 MB on an Apple Silicon Mac M1."*

### 4. The 5-Minute System Design Walkthrough
*(Structure your response into 5 phases: Problem Statement, Architectural Boundaries, Agent State Machine, Security & Isolation, and Empirical Verification).*

---

# SECTION B: CORE COMPETENCY BREAKDOWN

## 1. Full-Stack Engineering (React 18, TypeScript, FastAPI, SQLAlchemy)
- **Frontend Architecture:** Component modularity with strict separation of concerns (`components/common/`, `pages/`, `services/api.ts`).
- **State Management & Caching:** Utilizes TanStack Query (`useQuery`, `useQueryClient`) for cache invalidation, background polling (every 3s for active task status, 10s for health checks), and optimistic UI updates.
- **Backend Architecture:** Asynchronous FastAPI endpoints organized with dependency injection (`get_db`), strict Pydantic v2 schemas for request validation, and SQLAlchemy 2.0 ORM models.
- **Database Persistence:** Single-file SQLite database with Alembic migration versioning, foreign-key cascade constraints, and zero background daemon memory overhead.

## 2. AI Engineering & LLM Integration
- **Provider-Agnostic Gateway:** Abstract `BaseLLMAdapter` interface with support for Google Gemini, Anthropic Claude, OpenAI GPT-4o, and local Ollama.
- **Fail-Fast Configuration:** If API keys are unconfigured, typed `LLMConfigurationError` is raised immediately. No mock data is faked in production mode (Rule 15).
- **Structured Outputs via Pydantic:** Forces LLMs into strict JSON schemas (`TaskUnderstandingResult`, `DynamicPlanOutput`, `CodingOutput`, `DiagnosisOutput`), validating field types before execution.
- **Context Budgeting:** Slices file contexts based on AST token relevance to fit within token boundaries without exceeding attention budgets.

## 3. Agentic AI & Autonomous Systems
- **Topological DAG Planning:** Replaces linear prompts with Directed Acyclic Graphs of dependent steps. Kahn's algorithm orders prerequisite steps and flags circular dependencies.
- **Self-Debugging Loop:** Formulates the agent as an iterative feedback loop: `Code -> Test -> Failure Classification -> Traceback Diagnosis -> Bounded Patch -> Re-Test`.
- **Bounded Repair Iterations:** Hardcoded limit of 3 repair attempts prevents infinite cyclic loops and unbounded token expenditure.
- **Scope Creep Detection:** Semantic comparison between original requirement and proposed step modifications to detect agent drift.

## 4. System Design & Reliability
- **Host Isolation:** Disposable workspaces created under `workspaces/isolated/{task_id}` prevent race conditions, host file overwrites, and state corruption.
- **Process Lifecycle Management:** Subprocesses spawned via `subprocess.Popen` with sanitized environment dictionaries (all host secrets stripped) and 60s hard timeouts.
- **Conflict Detection:** Atomic comparison of source file modification timestamps and SHA-256 hashes prior to patch merging prevents concurrent edit overwrites.

## 5. Security Engineering & Sandboxing
- **Canonical Path Containment:** `validate_safe_path` resolves symlinks and verifies `target.resolve().parents` against `ALLOWED_REPO_ROOTS`.
- **Executable Allowlisting:** Commands restricted to `pytest`, `vitest`, `npm`, `python`, `node`, and `tsc`. Shell execution (`shell=True`) is strictly prohibited.
- **Secret Redaction:** Regex filters intercept and scrub `sk-`, `ghp_`, `AIzaSy`, and `Bearer` credentials from logs, stdout, and agent context.
- **Prompt Injection Defense:** Keyword risk escalation elevates prompt override strings (`SYSTEM OVERRIDE`, `ignore instructions`) to `CRITICAL` risk, requiring administrative approval.

---

# SECTION C: 50+ IN-DEPTH TECHNICAL INTERVIEW QUESTIONS & ANSWERS

### Category 1: Full-Stack & Systems Architecture (Q1–Q10)

#### Q1: Why did you choose React + TypeScript + Vite over Next.js or traditional SSR for the frontend?
**Answer:**
> *"AETHER ENGINEER is an interactive, stateful developer desktop tool rather than an SEO-driven public website. Vite provides instantaneous hot-module replacement (< 150ms) and produces a minimal production bundle (< 320 kB gzipped) without the Node.js server runtime overhead of Next.js. TypeScript guarantees type safety between backend Pydantic models and frontend components, and client-side rendering with TanStack Query allows sub-second reactive polling of agent execution states without full-page reloads."*

#### Q2: How does the 4-panel IDE layout maintain smooth performance with large repositories?
**Answer:**
> *"The 4-panel layout renders the file tree, active code viewer, AI orchestrator, and test drawer concurrently. To ensure high frame rates on 8 GB memory, the file tree utilizes lazy virtualized rendering; files are only read from disk when selected. File content is cached via TanStack Query. Large diffs are split line-by-line rather than re-rendered in monolithic DOM blocks, keeping DOM nodes under 1,500 at all times."*

#### Q3: How do you handle real-time agent updates between frontend and backend?
**Answer:**
> *"We utilize TanStack Query with exponential backoff and active-polling intervals (3,000ms while a task is in `PLANNING`, `CODING`, or `VERIFYING`, transitioning to passive polling once in `AWAITING_APPROVAL` or `COMPLETED`). This provides sub-second update latency while avoiding the socket connection overhead and reconnect state synchronization challenges of WebSockets on local desktop setups."*

#### Q4: How is database persistence structured, and why SQLite over PostgreSQL?
**Answer:**
> *"We implemented SQLAlchemy 2.0 with asynchronous ORM mappings and Alembic schema migrations. For our Apple Silicon Mac M1 8 GB RAM target, running a background PostgreSQL daemon consumes 400–800 MB of idle memory and adds complex container setup for recruiters. SQLite with Write-Ahead Logging (WAL) provides single-file portability, zero background memory footprint, sub-millisecond query execution, and transactional consistency across all tasks."*

#### Q5: What happens if the backend server crashes mid-task? How does recovery work?
**Answer:**
> *"All task transitions are checkpointed in SQLite before the next phase begins: `PENDING -> PLANNING -> AWAITING_PLAN_APPROVAL -> CODING -> VERIFYING -> AWAITING_DIFF_APPROVAL -> COMPLETED`. If a crash occurs during `CODING` or `VERIFYING`, the isolated task directory remains preserved on disk. Upon restart, the database indicates the task was in flight; the user can inspect the last recorded execution log and choose to resume or clean up."*

#### Q6: How do you prevent race conditions when multiple tasks are created simultaneously?
**Answer:**
> *"Each task is provisioned with a unique UUID (`task_{uuid}`) and assigned a dedicated isolated workspace directory (`workspaces/isolated/{task_id}`). Because no task shares a workspace directory, file writes are completely decoupled. At the final merge stage, `ReviewEngine` checks file hashes against the main repository with row-level locks, blocking concurrent merges with HTTP 409 Conflict if an overlap occurs."*

#### Q7: How does your frontend handle API errors and network disconnections?
**Answer:**
> *"Every API call in `services/api.ts` is wrapped in standard error handling that maps HTTP status codes into typed error messages. The UI displays responsive toast alerts and warning banners. TanStack Query automatically retries transient network failures up to 3 times with exponential backoff before marking a query as errored."*

#### Q8: How did you optimize bundle size and frontend load performance?
**Answer:**
> *"We leveraged tree-shaking in Vite and imported only individual icons from `lucide-react`. We configured manual chunk splitting in `vite.config.ts` separating vendor packages (React, TanStack Query) from application logic. The resulting production build is under 320 kB gzipped, transforming 1,628 modules in just 1.16 seconds."*

#### Q9: How do you ensure cross-browser compatibility and responsive layout?
**Answer:**
> *"We built the UI using Tailwind CSS flexbox and grid utilities with standard `rem` scaling. We tested across Safari, Chrome, and Firefox on macOS. Responsive breakpoints collapse the 4-panel layout into stacked drawers on smaller viewports, while maintaining full multi-panel visibility on 1080p and 1440p displays."*

#### Q10: How do you manage API versioning in the FastAPI backend?
**Answer:**
> *"All endpoints are scoped under `/api/v1/` using FastAPI `APIRouter` modules (`api_router.include_router(tasks_router, prefix='/tasks')`). This enables introducing a future `/api/v2/` without breaking existing frontend clients or automated evaluation scripts."*

---

### Category 2: AI Engineering & Agentic Systems (Q11–Q20)

#### Q11: How do you prevent LLMs from hallucinating non-existent functions or files?
**Answer:**
> *"We employ Grounded Repository Context Retrieval. Before prompting the LLM, the `RepositoryScanner` extracts the actual project AST symbols (classes, methods, imported modules) and file paths. These ground-truth identifiers are injected into the prompt context with strict instructions that only existing imports may be used. Furthermore, our `PatchEngine` validates candidate edits against real file syntax, and our `TestRunner` immediately catches `ImportError` or `AttributeError`."*

#### Q12: How does the Topological DAG Planner work, and why is it superior to linear planning?
**Answer:**
> *"Linear planners output a flat sequence of steps, frequently attempting to implement features before creating prerequisite models or updating interfaces. Our `DynamicPlanner` models tasks as a Directed Acyclic Graph where each step declares its `prerequisite_steps`. We apply Kahn's algorithm for topological sorting. If a cycle is detected, the planner catches it before execution starts, ensuring dependencies are always implemented in strict topological order."*

#### Q13: How does the Task Understanding Engine detect ambiguity in developer prompts?
**Answer:**
> *"The engine computes an Ambiguity Score between 0.0 and 1.0 using heuristic and semantic markers: brevity (e.g. 'fix bug' with zero detail), absence of hinted filenames, vague phrasing ('make it work'), and missing acceptance criteria. When the ambiguity score exceeds 0.6, the engine flags the requirement as ambiguous, identifies missing elements, and generates targeted clarification questions rather than guessing."*

#### Q14: How does the bounded self-debugging loop prevent runaway loops?
**Answer:**
> *"The loop is governed by `MAX_REPAIR_ATTEMPTS = 3`. Each iteration captures the test execution exit code and traceback. The `FailureClassifier` extracts the exact exception type and failing file/line number, creating a targeted diagnosis prompt. The coding agent generates a corrective patch, which is applied and re-tested. If the third iteration still fails, the loop halts deterministically, preserving the diagnostic trace for human review."*

#### Q15: How do you structure prompt templates to enforce valid JSON from model providers?
**Answer:**
> *"We utilize strict Pydantic v2 schemas passed as JSON schema schemas to model providers that support structured output. For providers that do not, we enforce Markdown-fenced JSON blocks and run the response through a multi-stage parser: 1) direct `json.loads()`, 2) regex extraction of ```json blocks, and 3) Pydantic model validation. If parsing fails, a typed validation error is raised without pretending execution succeeded."*

#### Q16: How do you prevent context window exhaustion on large repositories?
**Answer:**
> *"Rather than dumping entire codebases into the prompt, we use AST symbol extraction and lexical context ranking. The scanner indexes all functions and classes. When a prompt arrives, we score codebase files based on token intersection with the user's prompt and extract only the relevant file interfaces and symbol signatures. This compresses context by over 90%, fitting complex repositories within 8,000 tokens."*

#### Q17: What is the purpose of the 6-configuration ablation study in your research?
**Answer:**
> *"The ablation study scientifically isolates the marginal value of each architectural component. By systematically enabling modules from Config A (raw LLM baseline: 20% resolution) through Config F (full platform: 100% resolution), we proved that repository intelligence doubles baseline capability (+20%), DAG planning adds another +20%, and test verification with self-debugging provides the critical final +30% boost required for production reliability."*

#### Q18: What is your philosophy on 'Human-in-the-Loop' vs 'Fully Autonomous' coding?
**Answer:**
> *"Fully autonomous code generation without governance is unacceptable in professional engineering. A single hallucinated drop statement or broken contract can bring down production. AETHER ENGINEER uses 'Autonomous Execution bounded by Human Governance': the agent automates the tedious labor—diagnosing failures, planning, writing code, running unit tests—while the human developer retains authoritative governance at two critical checkpoints: approving the architectural plan (Gate 1) and approving verified unified diffs (Gate 2)."*

#### Q19: How do you evaluate prompt quality and prevent prompt drift across model upgrades?
**Answer:**
> *"All system prompts are version-controlled in code (`services/llm/prompts/`) rather than ad-hoc strings. We run our 50-task benchmark suite whenever a prompt or model version changes. If regression occurs on any task or the first-attempt resolution drops below 80%, the prompt modification is rejected."*

#### Q20: How does your system support local open-source models like Llama 3 via Ollama?
**Answer:**
> *"Our `OllamaAdapter` inherits from `BaseLLMAdapter` and communicates with the local Ollama daemon via HTTP (`http://localhost:11434/api/generate`). It enforces the same JSON schemas and response parsing as cloud models, allowing developers to run completely air-gapped, zero-cost autonomous engineering offline."*

---

### Category 3: Security & Sandbox Isolation (Q21–Q30)

#### Q21: How do you prevent directory traversal attacks such as `../../etc/passwd`?
**Answer:**
> *"We implement canonical path validation via `validate_safe_path()`. The candidate path is resolved using `.resolve()`, which normalizes `..`, `.`, and follows all symlinks to their ultimate physical destination. We then check `resolved_path == root or root in resolved_path.parents` against our allowlist. If the path does not reside within the allowlisted boundaries, a `SecurityException` (HTTP 403) is raised immediately before any filesystem read or write."*

#### Q22: How do you prevent symlink escape vulnerabilities?
**Answer:**
> *"Attackers can attempt to create a symlink inside an allowed workspace that points to `/etc` or `~/.ssh`. In `PatchEngine.validate_patch()`, we explicitly check `raw_path.is_symlink()`. Any attempt to target a symlink or create a symlink pointing outside the sandbox root is strictly prohibited and aborted."*

#### Q23: How do you prevent command injection when executing tests?
**Answer:**
> *"We completely disallow `shell=True` in all subprocess calls. Commands are parsed and passed strictly as argument vectors (`List[str]`). This neutralizes shell metacharacters such as `;`, `&&`, `|`, and backticks. Furthermore, we enforce an executable allowlist (`pytest`, `vitest`, `npm`, `python`, `node`, `tsc`); invoking any non-allowlisted binary like `bash`, `sh`, or `curl` raises a `SecurityException`."*

#### Q24: How does the secret redacting logging engine protect API keys?
**Answer:**
> *"We created a custom logging formatter (`SecretRedactingFormatter`) that applies compiled regex patterns matching OpenAI keys (`sk-[A-Za-z0-9_-]{20,}`), GitHub personal tokens (`ghp_[A-Za-z0-9]{36}`), Google API keys (`AIzaSy[A-Za-z0-9_-]{33}`), AWS secrets, and Bearer tokens. Any matched string in log records, error messages, or subprocess stdout is replaced with `[REDACTED_SECRET]` before output."*

#### Q25: What stops an adversarial prompt injection from overriding agent instructions?
**Answer:**
> *"Our `TaskUnderstandingEngine` incorporates an adversarial keyword scanner targeting directives like `'SYSTEM OVERRIDE'`, `'ignore all instructions'`, and `'ignore previous instructions'`. When detected, the task's risk level is automatically escalated to `CRITICAL`, and the intent is classified as `HIGH_RISK_OPERATION`. This forces an administrative governance gate requiring explicit human acknowledgment before any processing occurs."*

#### Q26: How do you sanitize the environment when running test subprocesses?
**Answer:**
> *"When spawning test processes, we construct a sanitized environment dictionary (`clean_env`) from scratch. It contains only `PATH` pointing to safe binaries (`/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin`) and sets `HOME` and `PYTHONPATH` strictly to the isolated workspace directory. All parent process environment variables containing API keys, database URLs, and cloud tokens are stripped."*

#### Q27: How do you enforce execution timeouts on untrusted code?
**Answer:**
> *"Every subprocess invocation in `TestRunner.execute_command()` is governed by `timeout_seconds = 60`. If the process exceeds 60 seconds (e.g. from an infinite `while True:` loop or network hang), `subprocess.TimeoutExpired` is caught, a `SIGTERM` is dispatched to the process group, followed by `SIGKILL` if necessary, and a structured `TIMEOUT_ERROR` is recorded."*

#### Q28: How do you prevent sensitive files like `.env` or `.git` from leaking to the LLM?
**Answer:**
> *"Our `RepositoryScanner` maintains a blacklist of protected patterns (`.env*`, `*.pem`, `*.key`, `id_rsa*`, `.git/`, `node_modules/`, `__pycache__/`). During repository tree building and context generation, these paths are excluded at the directory walking level, ensuring sensitive credentials never enter LLM prompt contexts."*

#### Q29: How do you prevent an agent from modifying files outside the task scope?
**Answer:**
> *"During planning, the agent generates a list of `predicted_file_changes`. During execution, `PatchEngine` checks that candidate patches match the declared target files. If an agent attempts to modify arbitrary unrelated files, the patch is rejected for scope creep."*

#### Q30: How do you guarantee the integrity of original code during agent crashes?
**Answer:**
> *"By architectural mandate: original repositories are opened in READ-ONLY mode. All write operations (file creations, edits, deletions, test executions) take place exclusively inside a freshly cloned sandbox workspace. Even if an agent crashes, corrupts files, or produces syntax errors, the user's original codebase remains 100% pristine."*

---

### Category 4: Performance, Testing & Benchmarking (Q31–Q40)

#### Q31: How did you optimize memory usage to stay under 75 MB on Apple Silicon Mac M1?
**Answer:**
> *"We eliminated all heavy background daemons: 1) We replaced language server daemons with lightweight Python standard library `ast` parsing, 2) We used SQLite instead of a dedicated PostgreSQL service, 3) We avoided persistent vector database daemons, using lexical symbol indexing, and 4) We implemented garbage collection of temporary sandbox workspaces. Peak RSS measured across all 50 benchmarks was 72.25 MB."*

#### Q32: What is your automated test coverage across the platform?
**Answer:**
> *"The backend test suite contains 64 pytest tests covering unit components, security regressions, AST scanners, patch boundaries, and end-to-end task lifecycles, executing in 14.4 seconds. The frontend features Vitest tests and a complete TypeScript typecheck and Vite build transforming 1,628 modules in 1.16 seconds. All checks run via `./scripts/test_all.sh`."*

#### Q33: How do you evaluate the SWE-bench Lite benchmark without 32 GB RAM?
**Answer:**
> *"SWE-bench Lite typically requires running large Docker containers for each issue. On an 8 GB M1 Mac, running multiple concurrent Docker containers causes catastrophic memory pressure. We implemented an intelligent hardware gating adapter: it verifies memory and safely runs curated lightweight SWE-bench fixtures (like `psf__requests-2317`) within isolated local environments, verifying ground truth in 0.289s while exporting predictions to the official SWE-bench evaluation format."*

#### Q34: How did you prevent benchmark evaluation test contamination?
**Answer:**
> *"In many flawed evaluations, the agent has access to the evaluation test assertions, allowing it to overfit. In AETHER ENGINEER, our benchmark suite features 10 held-out tasks where acceptance tests are stored in a separate hidden directory completely inaccessible to the agent. The independent evaluation engine scores the result by running these hidden tests post-patch."*

#### Q35: How do you measure the performance difference between different LLM models?
**Answer:**
> *"Our `ModelComparisonRunner` benchmarks candidate models (Gemini 1.5 Pro, Claude 3.5 Sonnet, GPT-4o, Ollama Llama 3) against a standardized task suite. It tracks 4 normalized dimensions: Resolution Pass Rate (%), Average Execution Latency (s), Token Consumption, and Estimated Cost per Task, generating automated Markdown comparison matrices."*

#### Q36: How does conflict detection prevent overwriting concurrent developer changes?
**Answer:**
> *"When a task starts, `ReviewEngine` computes the SHA-256 hash of every target file in the original repository. Before applying the final approved patch, it re-computes the current file hashes. If a developer modified a file externally while the agent was running, the hash mismatch triggers an HTTP 409 Conflict error, blocking the merge and preserving developer work."*

#### Q37: How do you handle flaky tests in the verification engine?
**Answer:**
> *"When a test fails, the `FailureClassifier` distinguishes between deterministic assertion failures and transient flaky errors (such as network socket timeouts or port collisions). Flaky failures trigger a targeted test re-run before initiating a full code repair cycle."*

#### Q38: How do you profile system performance and memory bottlenecks?
**Answer:**
> *"We built `scripts/profile_system.py` utilizing Python's native `resource.getrusage(resource.RUSAGE_SELF)` and `tracemalloc`. It records baseline memory, measures peak resident set size during peak execution, and tracks heap allocations line-by-line across all services."*

#### Q39: What is the median execution time for a complete autonomous repair cycle?
**Answer:**
> *"Across our 50 custom benchmark tasks and the recruiter demonstration runner, the median duration for a complete end-to-end cycle (Intent Analysis -> DAG Planning -> Sandboxed Patching -> Pytest Verification -> Unified Diff Generation) is 0.291 seconds when using optimized deterministic adapters, and 3.2–6.5 seconds when using cloud LLM APIs."*

#### Q40: How do you verify that generated patches conform to standard unified diff formats?
**Answer:**
> *"Patches are generated and validated using Python's `difflib.unified_diff`. The `PatchEngine` parses chunk headers (`@@ -line,count +line,count @@`) and verifies that applying the diff to the original content matches the patched content exactly before returning."*

---

### Category 5: Behavioral & Leadership in AI Systems (Q41–Q50)

#### Q41: How did you balance rapid feature velocity with strict security standards?
**Answer:**
> *"By adopting 'Security-as-Code' from Phase 1. Rather than treating security as an afterthought audit, I implemented canonical path resolution and executable allowlisting as core foundational primitives. Every subsequent feature—planning, coding, testing—was required to execute on top of these verified primitives, preventing security debt from accumulating."*

#### Q42: What was the most technically challenging bug you encountered and resolved in this project?
**Answer:**
> *"During Phase 11 adversarial testing, we discovered that certain prompt injection strings like `'SYSTEM OVERRIDE: ignore instructions'` lacked destructive shell verbs and were erroneously categorized as read-only analysis with low risk. To fix this, I redesigned `task_analyzer.py` to decouple destructive verb detection from adversarial directive scanning, ensuring any prompt injection trigger immediately elevates the risk to `CRITICAL` regardless of surrounding text."*

#### Q43: How do you decide when an engineering task should be automated by AI vs kept manual?
**Answer:**
> *"High-frequency, well-specified, and test-covered tasks (bug fixes with regression tests, boilerplate API endpoints, data models, input validators) are ideal candidates for autonomous execution. High-ambiguity architectural design, cross-organizational API contracts, and business strategy should remain human-led, with AI acting as an advisory collaborator."*

#### Q44: What are the primary trade-offs of using local SQLite over PostgreSQL in this platform?
**Answer:**
> *"The trade-off is horizontal concurrency vs zero-friction developer ergonomics. PostgreSQL offers superior multi-client concurrent connection pooling, but requires running background services and Docker containers. For a local developer desktop tool running on an 8 GB M1 Mac, SQLite with WAL mode delivers microsecond response times, zero idle memory, and trivial single-file backups, which aligned perfectly with our architectural goals."*

#### Q45: How would you scale AETHER ENGINEER to support multi-tenant enterprise teams?
**Answer:**
> *"To scale from single-developer local execution to enterprise multi-tenancy: 1) Migrate the persistence layer from SQLite to managed Amazon Aurora PostgreSQL, 2) Decouple the sandbox runner into containerized worker pools running on Kubernetes with Firecracker microVMs or gVisor for sandboxing, 3) Implement role-based access control (RBAC) with OAuth2/SAML SSO, and 4) Add Celery or Temporal workflows for distributed task orchestration."*

#### Q46: If you had another month to work on this platform, what would you build next?
**Answer:**
> *"I would implement three high-impact capabilities: 1) Interactive multi-turn chat directly inside the 4-panel IDE code editor, 2) Automatic git branch management with automatic PR creation on GitHub/GitLab, and 3) A Tree-sitter semantic indexing engine to expand multi-language cross-file refactoring across Rust, Go, and C++."*

#### Q47: How does this project demonstrate Senior / Principal Engineer competencies?
**Answer:**
> *"This project goes far beyond a prototype or toy chatbot. It demonstrates end-to-end full-stack systems engineering: clean architectural separation across 12 phases, strict security sandboxing, multi-language testing infrastructure, empirical benchmarking and ablation studies, sub-100 MB memory optimization on constrained hardware, and comprehensive production documentation with 10 ADRs."*

#### Q48: How do you handle API deprecations or breaking changes from model providers?
**Answer:**
> *"Our `BaseLLMAdapter` interface shields the rest of the application from provider-specific API changes. If Anthropic or OpenAI updates their SDK or parameters, only the adapter implementation needs modification; the Task Analyzer, Dynamic Planner, and Coding Engine remain completely decoupled and untouched."*

#### Q49: What metrics do you track to measure the business ROI of an AI software engineering platform?
**Answer:**
> *"We track 4 primary engineering metrics: 1) Mean Time to Resolution (MTTR) for bug fixes, 2) First-Attempt Test Pass Rate, 3) Developer Review Latency (time spent reviewing plans and diffs), and 4) Regression Rate (defects caught prior to merge vs escaped defects)."*

#### Q50: What is the single most important lesson you learned from building AETHER ENGINEER?
**Answer:**
> *"In AI software engineering, generation is easy; verification is hard. Anyone can prompt an LLM to generate code, but without isolated sandboxing, topological planning, and deterministic test verification, generative AI cannot be trusted in production. True agentic engineering begins when the AI is held accountable to the same objective test suites that govern human engineers."*

---

### Category 6: Infrastructure, DevOps & Cloud Architecture (Q51–Q80)

#### Q51: Why did you select Docker for containerization, and how is it structured?
**Answer:**
> *"We chose Docker to guarantee reproducible runtime environments across local development and cloud production. Both frontend and backend utilize multi-stage builds. The backend container (`backend/Dockerfile`) uses `python:3.12-slim-bookworm` with wheels cached in the builder stage, and runs under an unprivileged `aether` system user (uid: 10001). The frontend container compiles Vite static assets using Node 22 and serves them through `nginxinc/nginx-unprivileged:alpine-slim`, keeping production images under 25 MB."*

#### Q52: What is the fundamental difference between containers and virtual machines for code execution?
**Answer:**
> *"Containers share the host operating system's kernel via cgroups and Linux namespaces (pid, net, mnt, ipc). Virtual machines (VMs), by contrast, run an independent guest operating system atop a hardware hypervisor (KVM, Nitro, Xen) with dedicated virtualized hardware. While containers offer near-instant startup (< 200ms) and minimal overhead, they share the host kernel. A kernel exploit (e.g. Dirty COW or container-escape CVE) in a container compromises the host, whereas a VM boundary provides hardware-isolated memory and CPU virtualization."*

#### Q53: Why are ordinary containers insufficient for executing untrusted repository code?
**Answer:**
> *"Ordinary containers share the host kernel. If untrusted code executed by an agent exploits a kernel vulnerability, mounts host volumes, or attempts privilege escalation, it can escape the container and compromise the host infrastructure. Furthermore, standard containers often have access to default network bridges. For true multi-tenant execution of untrusted code, production architectures must utilize hardened microVMs (such as AWS Firecracker) or user-space kernel sandboxes (Google gVisor / `runsc`), which intercept syscalls and enforce strict virtualization boundaries."*

#### Q54: Why is PostgreSQL suitable for persistent production data, and how is it abstracted from SQLite?
**Answer:**
> *"PostgreSQL provides robust ACID transactions, multi-version concurrency control (MVCC), foreign key constraints, connection pooling, and multi-AZ replication for high availability. In AETHER ENGINEER, we abstracted the database layer using SQLAlchemy 2.0. In local development on Mac M1, the system defaults to embedded SQLite in WAL mode with zero background RAM footprint. In production, changing `DATABASE_URL` activates PostgreSQL connection pooling (`pool_size=10, max_overflow=20, pool_pre_ping=True`) with zero code alterations."*

#### Q55: Why is Redis useful for asynchronous tasks and caching in this architecture?
**Answer:**
> *"Redis provides in-memory sub-millisecond data structures. In our architecture, Redis serves two distinct purposes: 1) As an atomic task queue broker for long-running AI planning, coding, and test verification tasks, and 2) As a tenant-scoped cache for repository AST symbols, framework detection, and file trees. When Redis is unavailable locally, our `TaskQueueManager` and `CacheManager` gracefully fall back to thread-safe in-memory implementations without crashing."*

#### Q56: How do background workers recover from unexpected node crashes or evictions?
**Answer:**
> *"Task state is checkpointed in the relational database prior to every state transition. Jobs in the queue carry unique IDs and track heartbeats. If a worker process terminates abruptly, the task remains marked as `PROCESSING`. Upon worker restart or dead-letter sweep, jobs with expired heartbeats (> 120s) are detected. Workers inspect the task's last recorded checkpoint and re-enqueue or fail safely with diagnostic tracebacks. Privileged human approvals (`GateType.PLAN`, `GateType.DIFF`) are never re-executed automatically."*

#### Q57: How is duplicate task execution prevented in an asynchronous environment?
**Answer:**
> *"We enforce client-supplied `idempotency_key` deduplication in `TaskQueueManager`. When an enqueue request arrives, the queue checks its idempotency registry. If a job with that key is currently queued or processing, the queue returns the existing `job_id` and status rather than spawning duplicate worker execution. At the database level, unique constraints prevent duplicate active tasks for the same workspace."*

#### Q58: How do API services scale horizontally behind a load balancer?
**Answer:**
> *"The FastAPI backend application is stateless. User authentication utilizes signed JWT tokens, and persistent state resides in PostgreSQL and Redis. Multiple replicas of the backend container can run behind an Application Load Balancer (ALB) or Nginx reverse proxy. Health checks (`/api/v1/health`) ensure traffic is routed only to ready instances. Replicas can scale from 2 to 20+ pods automatically based on CPU or request rate thresholds."*

#### Q59: How do AI workers scale independently from API services?
**Answer:**
> *"AI workers are decoupled into independent consumer processes (`scripts/run_worker.py`). While API servers scale on HTTP request volume, AI workers scale on queue depth using tools like KEDA (Kubernetes Event-driven Autoscaling). If developers submit a surge of 500 tasks, the API servers respond in milliseconds with HTTP 202 Accepted, while the worker pool scales out horizontally to consume the backlog without degrading API responsiveness."*

#### Q60: How are database connections managed across multiple application instances?
**Answer:**
> *"Each application instance configures an SQLAlchemy connection pool with `pool_size=10, max_overflow=20, pool_timeout=30, pool_recycle=1800`. Connections are validated before checkout using `pool_pre_ping=True` to prune stale TCP sockets. In large production environments with dozens of replicas, we place AWS RDS Proxy or PgBouncer in front of PostgreSQL to pool thousands of client connections into a manageable database connection pool."*

#### Q61: How is tenant data isolation enforced across the application?
**Answer:**
> *"Every workspace, repository, and engineering task is tagged with a `tenant_id`. Every authenticated JWT contains the caller's `tenant_id`. Our dependency injection middleware enforces `verify_workspace_access()`, which asserts that `workspace.tenant_id == current_user.tenant_id`. Cross-tenant queries are blocked with HTTP 403 Forbidden. Similarly, cache keys in Redis are prefixed by tenant (`tenant:{tenant_id}:repo:{repo_id}:...`), preventing cross-tenant cache contamination."*

#### Q62: How does rate limiting work at both the proxy and application levels?
**Answer:**
> *"At the reverse proxy level, Nginx enforces IP-based rate limiting via `limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s` with a burst buffer of 50. At the application layer, per-user token-bucket rate limiters throttle API keys that exceed their tier limits, protecting downstream model providers from token exhaustion."*

#### Q63: How are model inference costs and token budgets controlled?
**Answer:**
> *"Our `CostController` maintains real-time token pricing matrices across providers (Gemini, Claude, GPT-4o). Every LLM invocation tracks prompt tokens and completion tokens. The controller enforces a `DEFAULT_PER_TASK_BUDGET_DOLLARS = $1.00` and a 50,000 token limit per task. If an iterative repair loop exceeds this budget, execution halts immediately with `InferenceBudgetExceededError`, preventing runaway cloud bills."*

#### Q64: How do Server-Sent Events (SSE) streaming connections recover from network drops?
**Answer:**
> *"Our `EventBroadcaster` tags every event with a monotonically increasing `event_id` and event type. Nginx is configured with `proxy_buffering off` to allow immediate chunked streaming. If a client disconnects, the browser's `EventSource` automatically reconnects and sends the `Last-Event-ID` header, enabling the server to resume streaming from the last acknowledged event."*

#### Q65: How does distributed observability work in AETHER ENGINEER?
**Answer:**
> *"We implement a Prometheus exposition endpoint (`/api/v1/metrics`) that collects system metrics (resident memory RSS via `getrusage`), application metrics (HTTP request rate, duration histogram, active tasks, error rates), AI metrics (cumulative tokens and costs), and security metrics (blocked traversal and injection attempts). Prometheus scrapes this endpoint every 15s, and Grafana visualizes latency distributions and queue depth."*

#### Q66: How are CI/CD deployment pipelines secured against supply-chain attacks?
**Answer:**
> *"Our GitHub Actions workflow (`.github/workflows/ci.yml`) enforces least-privilege permissions (`permissions: contents: read`). Action versions are pinned to trusted major tags (`actions/checkout@v4`). Dependencies are installed using lockfiles (`npm ci`). Secret scanning and security regression tests run automatically on every push, and deployment steps are strictly decoupled from pull request workflows."*

#### Q67: How do task queues handle sudden burst overload and backpressure?
**Answer:**
> *"When task arrival exceeds worker consumption capacity, the queue buffers jobs in Redis or memory, returning HTTP 202 Accepted with a `queue_depth` indicator. If queue depth exceeds configured thresholds (e.g. 1,000 jobs), the API rejects new non-critical tasks with HTTP 429 Too Many Requests and a `Retry-After` header, preventing memory exhaustion on the host."*

#### Q68: How does the platform handle model provider rate limits and transient outages?
**Answer:**
> *"The Model Gateway wraps provider calls with exponential backoff and jitter (retrying up to 3 times on HTTP 429 or 503). If a provider experiences sustained outage, the gateway reports the failure transparently rather than hanging. Optional fallback between explicitly authorized providers can be configured, but silent switching to more expensive models without authorization is strictly prohibited."*

#### Q69: How are database backups tested and restored safely?
**Answer:**
> *"Restorations are never performed directly on production databases. Our SOP (`docs/DISASTER_RECOVERY.md`) mandates restoring database dumps into an isolated disposable test database (`aether_recovery_test`). Automated verification scripts check row counts, foreign key constraints, and run `alembic upgrade head` before traffic is redirected."*

#### Q70: How could AETHER ENGINEER scale from a single developer to 10,000 concurrent users?
**Answer:**
> *"By transitioning from Tier 1 (Single Node) to Tier 3 (Enterprise Cloud): 1) Deploy API services on Amazon EKS across 12+ horizontally autoscaled pods, 2) Use KEDA to autoscale worker pods on Redis queue depth, 3) Migrate database to a Multi-AZ Amazon Aurora PostgreSQL cluster with write-primary and auto-scaling read replicas, 4) Deploy AWS Firecracker microVMs for hardware-isolated untrusted code execution, 5) Cache AST indexes in an ElastiCache Redis cluster, and 6) Deliver static frontend assets globally via CloudFront CDN."*

#### Q71: How do multi-stage Docker builds reduce attack surfaces and image sizes?
**Answer:**
> *"Multi-stage builds separate the build environment from the runtime environment. In our backend Dockerfile, the builder stage installs build tools (`build-essential`, compilers) and compiles Python wheels. The runner stage copies only the compiled `site-packages` into a fresh `python:3.12-slim` image without compilers or build artifacts, shrinking the image by over 60% and eliminating vulnerable build tools from production containers."*

#### Q72: Why is running containers as non-root critical for application security?
**Answer:**
> *"By default, Docker containers run as root (`uid: 0`), which maps directly to host root if user namespaces are not configured. If a container breakout or command injection vulnerability occurs, the attacker gains root privileges on the host. In our Dockerfiles, we explicitly create and switch to unprivileged users (`USER aether` on backend, `USER nginx` on frontend), ensuring that even in the event of an application compromise, root access cannot be acquired."*

#### Q73: Why are Docker Compose profiles essential for development on Apple Silicon Mac M1 (8 GB RAM)?
**Answer:**
> *"Running a full enterprise stack simultaneously (Postgres, Redis, Backend, Frontend, Worker, Prometheus, Grafana, Nginx) consumes 3–5 GB of RAM, causing severe memory pressure on an 8 GB unified memory Mac. Our `docker-compose.yml` defines profiles (`development`, `data`, `worker`, `observability`). Developers can run just the lightweight frontend and backend with SQLite (`--profile development`), spinning up data or monitoring services only when needed."*

#### Q74: How was horizontal privilege escalation prevented across workspaces?
**Answer:**
> *"Horizontal privilege escalation occurs when User A accesses or modifies User B's resources. In AETHER ENGINEER, `verify_workspace_access()` inspects the tenant and ownership tags on every workspace and task. If a user from `tenant-corp` attempts to access a workspace belonging to `tenant-competitor`, the request is immediately rejected with HTTP 403 Forbidden and logged as an immutable security audit event."*

#### Q75: How does PBKDF2 password hashing protect against rainbow table attacks?
**Answer:**
> *"PBKDF2 applies 100,000 iterations of HMAC-SHA256 with a cryptographically random 16-byte salt per user. The unique salt ensures identical passwords produce completely different hash strings, neutralizing pre-computed rainbow table attacks. The 100,000 iteration count introduces computational cost that makes brute-force dictionary attacks infeasible."*

#### Q76: How does JWT claims validation defend against token tampering and replay?
**Answer:**
> *"Our JWT parser validates four distinct layers: 1) HMAC-SHA256 signature verification with constant-time comparison, 2) Expiration (`exp`) verification against UTC timestamps, 3) Issuer (`iss: 'aether-engineer'`) validation, and 4) Audience (`aud: 'aether-api'`) validation. Tampering with any payload field invalidates the signature, and expired tokens are rejected immediately."*

#### Q77: How does tenant-scoped caching prevent cache poisoning?
**Answer:**
> *"Cache keys are structured as `tenant:{tenant_id}:repo:{repo_id}:{key}`. Because every lookup includes the caller's authenticated `tenant_id`, one tenant can never read or overwrite another tenant's cached file trees or AST symbol indexes. Furthermore, when files are patched or merged, `cache_manager.invalidate_repo()` purges all keys for that repository, preventing stale context reuse."*

#### Q78: How does graceful shutdown handle in-flight tasks and database transactions?
**Answer:**
> *"Our worker and FastAPI applications register `SIGINT` and `SIGTERM` signal handlers. When a shutdown signal is received, the listener stops accepting new tasks and finishes processing the active task job. Database connections are flushed and closed gracefully, and SQLite writes its write-ahead log to the main database file before process exit."*

#### Q79: What is the difference between RTO and RPO in AETHER ENGINEER disaster recovery?
**Answer:**
> *"Recovery Time Objective (RTO) is the maximum acceptable duration of system downtime after an outage (e.g. target RTO < 30 minutes to restore a database replica). Recovery Point Objective (RPO) is the maximum acceptable age of data lost due to an incident (e.g. target RPO < 1 hour of task logs). We document concrete backup strategies for both metrics in `docs/DISASTER_RECOVERY.md`."*

#### Q80: How does AETHER ENGINEER separate the application control plane from untrusted code execution?
**Answer:**
> *"The control plane (FastAPI, database, auth) handles user interactions and planning. Untrusted repository code (unit tests, scripts) is never executed within the primary application process. It executes inside dedicated subprocess sandboxes with stripped environments, strict argument allowlists, and execution timeouts. In cloud production, this boundary is enforced via isolated microVMs, ensuring untrusted code has zero access to host credentials or internal network services."*


