# AETHER ENGINEER — Engineering Case Studies
### *Real-World Autonomous Software Engineering in Practice*

This document provides three end-to-end technical case studies detailing how AETHER ENGINEER autonomously inspects codebases, identifies defects, plans topological changes, applies sandboxed patches, and verifies fixes with real test execution.

---

# Case Study 1: Resolving a Critical Authentication Defect in FastAPI

## 1. Context & Problem Statement
In a FastAPI microservice (`auth_service.py`), tokens were decoded using a simulated JWT decoder. However, the author failed to validate the `exp` (expiration timestamp) claim against current wall-clock time (`time.time()`). Consequently:
- Expired tokens were erroneously treated as valid.
- The unit test `test_expired_token_rejected` failed with:
  ```
  FAILED test_auth.py::test_expired_token_rejected - Failed: DID NOT RAISE <class 'ValueError'>
  ```

## 2. Agentic Workflow Execution

### Step 1: Intelligent Task Understanding
The user entered the requirement:
> *"Fix JWT expiration validation bug in auth_service.py so expired tokens raise ValueError('Token has expired')."*

The `TaskUnderstandingEngine` analyzed the prompt and codebase:
- **Intent:** `CODE_MODIFICATION`
- **Category:** `BUG_FIX`
- **Risk Level:** `HIGH` (due to security keywords `jwt`, `token`, `auth`)
- **Target File Identified:** `auth_service.py`
- **Acceptance Criteria Synthesized:**
  - `[AC-01]`: Isolate root cause in `auth_service.py`.
  - `[AC-02]`: Ensure expired tokens raise `ValueError("Token has expired")`.
  - `[AC-03]`: All pytest unit tests pass with exit code 0.

### Step 2: Dynamic Topological Planning
The `DynamicPlanner` ordered the implementation into a 3-step DAG:
1. `Step 1`: Inspect token decoding logic in `auth_service.py`.
2. `Step 2`: Implement `payload["exp"] < time.time()` check in `verify_token()`.
3. `Step 3`: Run `pytest test_auth.py` and verify all assertions pass.

### Step 3: Human Governance Gate #1 (Plan Approval)
The plan was submitted to the developer via the 4-panel IDE. The developer reviewed the steps and clicked **Approve Plan**.

### Step 4: Sandboxed Code Modification
The `PatchEngine` generated a patch and applied it strictly within an isolated sandbox clone (`workspaces/isolated/demo_auth_task`):

```diff
--- a/auth_service.py
+++ b/auth_service.py
@@ -14,6 +14,8 @@
 def verify_token(token: str) -> Dict[str, Any]:
     payload = decode_token(token)
     if not payload:
         raise ValueError("Invalid token")
+    if payload["exp"] < time.time():
+        raise ValueError("Token has expired")
     return payload
```

### Step 5: Test Execution & Verification
The `TestRunner` executed `pytest test_auth.py` in a sanitized subprocess:
```
============================== test session starts ==============================
test_auth.py ..                                                           [100%]
=============================== 2 passed in 0.23s ===============================
```

### Step 6: Human Governance Gate #2 (Diff Approval & Merge)
The developer inspected the unified diff and confirmed the test pass. The patch was safely merged back to the repository. Total time: **0.51 seconds**.

## 3. Engineering Lesson
Without test-driven verification, raw generative AI models often hallucinate that a bug is fixed simply by outputting plausible code. By executing real `pytest` assertions inside a sandboxed clone, AETHER ENGINEER provides empirical proof that the defect is eliminated before any code touches the developer's source repository.

---

# Case Study 2: Implementing Cursor Pagination in a REST API

## 1. Context & Problem Statement
A FastAPI items catalog endpoint (`api_service.py`) returned all 50 items in memory without pagination parameters. As dataset sizes grew, this risked performance degradation and payload bloat. The engineering requirement was to add query parameter validation and pagination metadata.

Initial test failure:
```
TypeError: get_items() got unexpected keyword argument 'limit'
```

## 2. Agentic Workflow Execution

### Step 1: Task Understanding & Acceptance Criteria
- **Intent:** `CODE_MODIFICATION`
- **Category:** `FEATURE_IMPLEMENTATION`
- **Risk Level:** `MEDIUM`
- **Acceptance Criteria:**
  - `[AC-01]`: Accept `limit: int = 10` (must be $> 0$) and `offset: int = 0` (must be $\ge 0$).
  - `[AC-02]`: Return structured dictionary `{ "items": [...], "total": 50, "offset": offset, "limit": limit, "has_more": bool }`.
  - `[AC-03]`: Reject negative offsets or zero/negative limits with `ValueError`.

### Step 2: Multi-Step DAG Planning
The planner structured the feature into dependency-ordered steps:
1. Update function signature to accept `limit` and `offset` with defaults.
2. Add input validation guards.
3. Compute slice indices `offset : offset + limit` and `has_more` boolean flag.
4. Execute test suite asserting slice bounds and metadata.

### Step 3: Sandboxed Patch Application
```diff
--- a/api_service.py
+++ b/api_service.py
@@ -4,4 +4,18 @@
 ITEMS_DB = [{"id": i, "name": f"item_{i}"} for i in range(1, 51)]
 
-def get_items() -> List[Dict[str, Any]]:
-    return ITEMS_DB
+def get_items(limit: int = 10, offset: int = 0) -> Dict[str, Any]:
+    """Return paginated items with metadata."""
+    if limit <= 0:
+        raise ValueError("Limit must be greater than zero")
+    if offset < 0:
+        raise ValueError("Offset cannot be negative")
+
+    total = len(ITEMS_DB)
+    items = ITEMS_DB[offset : offset + limit]
+    has_more = (offset + limit) < total
+
+    return {
+        "items": items,
+        "total": total,
+        "offset": offset,
+        "limit": limit,
+        "has_more": has_more
+    }
```

### Step 4: Verification Result
```
test_api.py ..                                                           [100%]
2 passed in 0.22s (Exit code: 0)
```
Total execution time: **0.47 seconds**. Peak memory: **69.56 MB**.

## 3. Engineering Lesson
Adding features to existing endpoints requires coordinating parameter defaults, validation guards, and return data structures simultaneously. The Topological DAG planner prevents incomplete edits by treating input validation, business logic, and test coverage as prerequisite dependencies.

---

# Case Study 3: Cross-Language Frontend Input Sanitization

## 1. Context & Problem Statement
In a full-stack application, an authentication utility module (`email_utils.js`) contained an input sanitization function that failed to strip leading/trailing whitespace or normalize uppercase characters. When users submitted `"  User.Name@Example.COM  "`, subsequent database lookups failed.

Initial Node.js assertion failure:
```
FAIL: Should trim and lowercase email
AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
'  User.Name@Example.COM  ' !== 'user.name@example.com'
```

## 2. Agentic Workflow Execution

### Step 1: Multi-Language Runtime Detection
The `RepositoryScanner` detected Node.js ESM configuration via `package.json`. The `TestRunner` selected `node test_email.js` using the strict executable allowlist.

### Step 2: Task Understanding & Safety Isolation
- **Intent:** `CODE_MODIFICATION`
- **Category:** `BUG_FIX`
- **Risk Level:** `HIGH` (authentication area)
- The agent was granted access only to the isolated frontend directory; all other system files remained inaccessible.

### Step 3: Candidate Patch Generation & Application
```diff
--- a/email_utils.js
+++ b/email_utils.js
@@ -1,7 +1,6 @@
 export function sanitizeEmail(email) {
-  if (!email || typeof email !== 'string') return '';
-  return email;
+  if (!email || typeof email !== 'string') return '';
+  return email.trim().toLowerCase();
 }
```

### Step 4: Cross-Language Test Execution
```
$ node test_email.js
PASS: Email sanitization tests passed
```
Exit code: `0`. Duration: **0.25 seconds**.

## 3. Engineering Lesson
Modern software stacks are inherently polyglot. A robust AI engineering platform must support cross-language testing (Python `pytest` alongside Node.js/TypeScript `vitest`) with identical security sandboxing, environment scrubbing, and timeout enforcement across both ecosystems.

