# AETHER ENGINEER — Technical Interview Guide & Architecture FAQ

This guide explains key engineering decisions, security trade-offs, and design patterns for technical interviews.

---

## 1. Core Architectural Questions

### Q1: Why use an isolated workspace sandbox rather than directly editing files?
**Answer:**
Direct filesystem modifications by autonomous agents carry catastrophic risks: half-applied changes, corrupted codebases, broken Git states, and lost developer uncommitted work. 
AETHER ENGINEER enforces a **two-tier isolation model**:
1. All changes, builds, and tests run inside `workspaces/isolated/{task_id}`.
2. The user's original repository is read-only during planning, coding, and debugging.
3. Only after the code passes automated tests and the developer explicitly approves the diff is the patch safely merged into the source repository.

### Q2: How do you prevent arbitrary code execution and command injection?
**Answer:**
1. **Command Allowlist**: Only explicitly permitted binaries (`pytest`, `vitest`, `npm test`, `python`) can run in verification. Shell metacharacters (`&&`, `;`, `|`, `sudo`, `eval`) are blocked.
2. **Environment Sanitization**: Sensitive environment variables (`API_KEY`, `TOKEN`, `SECRET`, `PASSWORD`) are stripped from subprocess environments.
3. **Execution Timeouts**: Subprocesses are bounded by strict timeouts (`ISOLATED_SANDBOX_TIMEOUT_SECONDS=60`) to terminate hanging or runaway processes.
4. **Boundary Checks**: Patches attempting directory traversal (`../`) or targeting sensitive files (`.env`, `id_rsa`) are rejected by `PatchEngine` with a `SecurityException`.

### Q3: How did you optimize for the 8 GB unified memory limit on Apple Silicon M1?
**Answer:**
1. **Lightweight Parsing**: Replaced heavy language servers with Python's built-in `ast` module and targeted regex parsers.
2. **No Heavy Vector DB by Default**: Utilized symbol-aware lexical indexing and token budgeting for repository context, avoiding running heavy Docker containers or separate vector databases.
3. **Pydantic v2 & SQLAlchemy 2.0**: Zero-copy JSON parsing with Rust-backed `pydantic-core` and connection pooling in SQLite.
4. **Clean Vite Frontend**: Production build is only ~248 kB, using minimal browser memory.

### Q4: How does the Self-Debugging loop avoid infinite recursion and hallucinated repairs?
**Answer:**
1. **Bounded Iterations**: Governed by `MAX_REPAIR_ATTEMPTS=3`. If tests do not pass within 3 iterations, execution halts and the task is marked `FAILED`.
2. **Failure Classifier**: Categorizes errors (`ASSERTION_ERROR`, `SYNTAX_ERROR`, `IMPORT_ERROR`, `TYPE_ERROR`, `TIMEOUT_ERROR`) so the LLM receives structured, actionable diagnostic feedback rather than raw stack traces.
3. **Ground Truth Verification**: Success is determined exclusively by subprocess exit codes (`returncode == 0`), never by the model's subjective self-evaluation.

### Q5: How do you detect and handle external merge conflicts?
**Answer:**
Before applying an approved patch, `ReviewEngine.detect_conflicts()` compares the current content of the source repository with `PatchDiff.original_content`. If an external developer modified any target file while the agent was running, the merge is blocked with HTTP 409 Conflict, requiring manual developer reconciliation.

### Q6: Why did you build custom model adapters instead of relying on heavy third-party agent frameworks?
**Answer:**
Heavy agent bundles pull in hundreds of transitive dependencies, bloat memory on an 8 GB machine, and obscure raw prompt and token flows. Building clean, provider-independent adapters (`OpenAIAdapter`, `GeminiAdapter`, `AnthropicAdapter`, `OllamaAdapter`) with standard `httpx` and `pydantic` guarantees:
- Complete provider portability.
- Transparent structured JSON schemas.
- Immediate fail-fast behavior with `UnconfiguredAdapter` when keys are missing.
- Zero unnecessary memory overhead.

