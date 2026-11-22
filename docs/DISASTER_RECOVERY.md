# AETHER ENGINEER — Disaster Recovery & Maintenance Runbook
### *Business Continuity, Backup/Restore Procedures & Incident Response*

**System:** AETHER ENGINEER Platform  
**Target Environments:** Local Apple Silicon Mac M1 | Cloud (PostgreSQL / Docker / Kubernetes)  
**Classification:** Standard Operating Procedure (SOP)

---

## 1. Service Level Objectives (SLOs) & Recovery Targets

| Tier | Recovery Time Objective (RTO) | Recovery Point Objective (RPO) | Backup Frequency | Target Redundancy |
|---|:---:|:---:|:---:|---|
| **Tier 1 (Local / Demo)** | 1 Hour | 24 Hours | Daily file copy | Local persistent volume |
| **Tier 2 (Startup MVP)** | 30 Minutes | 1 Hour | Continuous WAL + Daily Snapshot | Multi-AZ RDS |
| **Tier 3 (Enterprise SaaS)** | **< 5 Minutes** | **< 1 Minute** | Synchronous Multi-AZ + 5-min PITR | Cross-Region Read Replicas |

---

## 2. Database Backup Procedures

### 2.1 SQLite (Local Development & Edge Execution)
SQLite utilizes Write-Ahead Logging (WAL) mode. Safe backups must use SQLite's native online backup API:

```bash
# Execute safe online backup without database locking
sqlite3 aether_engineer.db ".backup 'workspaces/backups/aether_backup_$(date +%Y%m%d_%H%M%S).db'"

# Verify backup integrity
sqlite3 "workspaces/backups/aether_backup_$(date +%Y%m%d_%H%M%S).db" "PRAGMA integrity_check;"
```

### 2.2 PostgreSQL (Production Deployment)
PostgreSQL utilizes custom-format compressed dumps with table data, constraints, and sequences:

```bash
# 1. Perform online logical backup
pg_dump -Fc -h "$DB_HOST" -U "$DB_USER" -d aether_engineer > "/var/backups/aether_db_$(date +%Y%m%d_%H%M%S).dump"

# 2. Upload encrypted backup to cold object storage
aws s3 cp "/var/backups/aether_db_$(date +%Y%m%d_%H%M%S).dump" s3://aether-enterprise-backups/database/ --sse aws:kms
```

---

## 3. Database Restoration Procedures

> [!CAUTION]
> Never restore a backup directly onto a live production database. Always verify restore procedures on an isolated disposable test database before redirecting application traffic.

### Step-by-Step Restoration Verification:
1. **Provision Disposable Test Database:**
   ```bash
   createdb -h "$DB_HOST" -U "$DB_USER" aether_recovery_test
   ```
2. **Restore Archive:**
   ```bash
   pg_restore -v -h "$DB_HOST" -U "$DB_USER" -d aether_recovery_test "/var/backups/aether_db_target.dump"
   ```
3. **Verify Row Counts & Foreign Key Integrity:**
   ```bash
   psql -h "$DB_HOST" -U "$DB_USER" -d aether_recovery_test -c "
     SELECT 'workspaces' as table_name, count(*) from workspaces
     UNION ALL
     SELECT 'tasks', count(*) from tasks
     UNION ALL
     SELECT 'users', count(*) from users;
   "
   ```
4. **Apply Pending Migrations:**
   ```bash
   alembic upgrade head
   ```

---

## 4. In-Flight Task & Worker Recovery

If a worker crashes mid-task (e.g. out-of-memory or node eviction):
1. **State Preservation:** The task record remains checkpointed in PostgreSQL/SQLite in status `CODING` or `VERIFYING`.
2. **Idempotency Key Verification:** The background queue checks `TaskJob.idempotency_key`. Duplicate submissions return the existing job rather than creating redundant runs.
3. **Approval Protection:** Privileged approval decisions (`GateType.PLAN`, `GateType.DIFF`) are recorded in `approval_gates` table and **never** auto-replayed.
4. **Automatic Re-enqueueing:** On worker restart, jobs in `PROCESSING` whose heartbeat exceeded 120 seconds are automatically reassigned or marked `FAILED` with actionable recovery logs.

---

## 5. Temporary Workspace Garbage Collection

Isolated sandboxes (`workspaces/isolated/{task_id}`) and demonstration repositories must be periodically pruned to maintain the sub-100 MB disk footprint on 8 GB development machines:

```bash
# Prune isolated workspaces older than 24 hours
find workspaces/isolated -mindepth 1 -maxdepth 1 -type d -mtime +1 -exec rm -rf {} +

# Prune recruiter demo scratch folders
find workspaces/recruiter_demos -mindepth 1 -maxdepth 1 -type d -mtime +1 -exec rm -rf {} +
```

---

## 6. Secret Rotation Runbook

### 6.1 JWT Secret Key Rotation
1. Update `AETHER_JWT_SECRET` in environment/secrets manager with dual-signing capability (verifying with old secret, signing with new).
2. Existing access tokens expire within 60 minutes; clients automatically obtain new tokens using refresh tokens.
3. Deprecate and purge old signing secret after 7 days (matching `REFRESH_TOKEN_EXPIRE_DAYS`).

### 6.2 Database Credential Rotation
1. Create secondary database user credentials in PostgreSQL.
2. Update application configuration to reference secondary credentials via rolling container deployment.
3. Verify connection pool re-establishment via `/api/v1/health`.
4. Drop old user credentials.

