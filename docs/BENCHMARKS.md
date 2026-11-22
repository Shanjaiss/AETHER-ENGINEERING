# AETHER ENGINEER — AI Evaluation Lab & Benchmark Suite

The AETHER ENGINEER evaluation system consists of **20 reproducible coding benchmark scenarios** spanning 10 core software engineering categories.

---

## 1. Benchmark Scenarios Overview

| ID | Category | Scenario Name | Primary Verification |
|---|---|---|---|
| `bench-01` | Bug Fixing | FastAPI JWT Expiry Check | Expired timestamp returns `False` |
| `bench-02` | Bug Fixing | Pagination Off-By-One Slice | Page 1 returns indices `0` to `limit` |
| `bench-03` | Unit-Test Generation | Slugify Helper Unit Tests | Tests spaces and special characters |
| `bench-04` | Unit-Test Generation | Currency Formatter Tests | Tests cents-to-dollars formatting |
| `bench-05` | Endpoint Implementation | System Health Status Route | Endpoint returns `healthy` and `version` |
| `bench-06` | Endpoint Implementation | User Profile Calculation | Computes profile completion percentage |
| `bench-07` | Refactoring | Refactor Dict Params to Class | Accepts structured `UserConfig` |
| `bench-08` | Refactoring | Consolidate String Cleaners | Strips whitespace and null bytes |
| `bench-09` | TypeScript Errors | Discriminated Union Safety | Type narrowing on event kind |
| `bench-10` | TypeScript Errors | Optional Property Null Safety | Handles missing nickname fallback |
| `bench-11` | Python Exceptions | ZeroDivisionError Guard | Returns `0.0` when divisor is `0` |
| `bench-12` | Python Exceptions | KeyError Fallback Handling | Provides default timeout when key absent |
| `bench-13` | Validation Failures | Email Format Validation | Regex validates standard email format |
| `bench-14` | Validation Failures | Password Strength Verification | Enforces 8+ characters and a digit |
| `bench-15` | Dependency Issues | Timezone-Aware UTC Datetime | Replaces deprecated `utcnow()` |
| `bench-16` | Dependency Issues | JSON Serialization Fallback | Serializes datetime objects safely |
| `bench-17` | Authentication Defects | Timing-Safe Secret Comparison | Uses `hmac.compare_digest` |
| `bench-18` | Authentication Defects | Bearer Token Header Extraction | Strips `Bearer ` prefix from headers |
| `bench-19` | Frontend Bugs | Immutable State Reducer Update | Ensures pure immutable state updates |
| `bench-20` | Frontend Bugs | Query Param Sanitizer | Strips null and empty query values |

---

## 2. Evaluation Metrics & Formulae

1. **Verified Test Pass Rate (%)**:
   $$\text{Pass Rate} = \left( \frac{\text{Benchmarks with exit\_code == 0}}{\text{Total Benchmarks Evaluated}} \right) \times 100$$
   *Note: Success is verified by independent pytest execution; model self-evaluations are never counted.*

2. **Task Completion Rate (%)**: Percentage of benchmarks reaching the final verification stage without unhandled exceptions.

3. **Average Latency**: Wall-clock seconds from plan generation to verified patch.

4. **Average Repair Attempts**: Number of self-debugging iterations required before passing (0 to 3).

5. **Security Policy Violations**: Total attempts to escape sandbox boundaries or access forbidden files.

