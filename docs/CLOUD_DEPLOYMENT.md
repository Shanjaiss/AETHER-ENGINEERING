# AETHER ENGINEER — Cloud Deployment & Scalability Architecture
### *Production Cloud Infrastructure, Multi-Cloud Topology & Capacity Planning*

**Platform Target:** Apple Silicon Mac M1 (Local Development) | Multi-Cloud Production (AWS, GCP, Azure)  
**Date:** November 2026

---

## 1. Executive Summary

This document specifies the multi-cloud production deployment architecture for AETHER ENGINEER across three distinct maturity tiers:
1. **Tier 1: Portfolio Demonstration Tier** (Low-cost, single-tenant, managed container runner)
2. **Tier 2: Startup MVP Tier** (High-availability API, decoupled worker queues, managed PostgreSQL & Redis)
3. **Tier 3: Enterprise Scalable Production Tier** (Multi-region Kubernetes, distributed worker auto-scaling, Firecracker microVM execution sandboxes, multi-AZ database clustering)

---

## 2. Three-Tier Infrastructure Architecture

### Tier 1 — Portfolio Demonstration
- **Target Audience:** Technical recruiters, open-source portfolio reviewers, individual developers.
- **Compute:** AWS ECS Fargate or Google Cloud Run (1 vCPU, 1 GB RAM container for FastAPI backend; Cloudflare Pages / AWS S3 + CloudFront for static frontend).
- **Database:** AWS RDS PostgreSQL (db.t4g.micro) or embedded SQLite in persistent volume.
- **Queue & Workers:** In-memory async worker queue; local concurrency capped at 1.
- **Sandboxing:** Restricted demonstration repositories with execution sandboxing; untrusted public repository code execution disabled.
- **Estimated Cost:** \$0 – \$15 / month (often eligible for AWS Free Tier).

### Tier 2 — Startup MVP
- **Target Audience:** Small engineering teams, closed beta customers (10–100 active developers).
- **Compute:** Decoupled container architecture:
  - *API Plane:* 2–4 replicas of FastAPI application container behind Application Load Balancer (ALB).
  - *Worker Plane:* 2 dedicated Celery / TaskQueue worker containers running on AWS Fargate.
- **Database:** AWS RDS PostgreSQL (Multi-AZ db.t4g.small) with automated daily snapshots and 7-day point-in-time recovery.
- **Cache & Queue Broker:** AWS ElastiCache Redis (cache.t4g.micro, Redis 7.x, cluster disabled).
- **Execution Sandboxing:** Ephemeral AWS Fargate tasks spawned on-demand for untrusted test executions, terminating immediately after test completion.
- **Estimated Cost:** \$120 – \$280 / month.

### Tier 3 — Enterprise Scalable Production
- **Target Audience:** Enterprise organizations, multi-tenant SaaS (1,000 – 10,000+ active developers).
- **Compute:** Kubernetes cluster (Amazon EKS / Google GKE):
  - *Control Plane:* Horizontally Auto-Scaled Pods (HPA based on CPU/RPS).
  - *Worker Plane:* KEDA (Kubernetes Event-driven Autoscaling) scaling workers based on Redis queue depth.
- **Sandboxed Execution:** AWS Firecracker microVMs or gVisor sandbox runtimes (`runsc`), providing hardware-isolated virtual machine boundaries for executing untrusted customer code with zero host escape risks.
- **Database:** Multi-AZ Amazon Aurora PostgreSQL cluster with write-primary and auto-scaling read replicas.
- **Cache & Queue:** Multi-AZ Redis Cluster with automatic failover.
- **Object Storage:** Amazon S3 / Google Cloud Storage for repository snapshots, patch artifacts, and audit logs.
- **Estimated Cost:** \$1,500 – \$4,200 / month.

---

## 3. Multi-Cloud Provider Comparison Matrix

| Dimension | Amazon Web Services (AWS) | Google Cloud Platform (GCP) | Microsoft Azure |
|---|---|---|---|
| **Container Runtime** | Amazon ECS Fargate / EKS | Cloud Run / GKE Autopilot | Azure Container Apps / AKS |
| **Managed Database** | Amazon Aurora PostgreSQL | Cloud SQL for PostgreSQL | Azure Database for PostgreSQL |
| **Queue / Cache** | ElastiCache Redis | Memorystore for Redis | Azure Cache for Redis |
| **Object Storage** | Amazon S3 | Google Cloud Storage (GCS) | Azure Blob Storage |
| **Sandboxed Compute** | Firecracker MicroVMs / Fargate | gVisor on GKE | Azure Container Instances |
| **Monitoring & Tracing** | CloudWatch & AWS X-Ray | Cloud Monitoring & Cloud Trace | Azure Monitor & App Insights |
| **Identity & Access** | AWS Cognito / IAM | Firebase Auth / Cloud IAM | Microsoft Entra ID |

---

## 4. Capacity Planning & Load Projections

Empirical testing on Apple Silicon Mac M1 established a baseline throughput of **486.8 req/sec** at **1.51 ms** median latency. Based on real response distributions, the following capacity models project infrastructure requirements across user scales:

```
+-----------------------------------------------------------------------------------------+
|                               CAPACITY PLANNING PROJECTIONS                             |
+-----------------------------------------------------------------------------------------+
| Concurrent Users | Est. RPS | Target P95 Latency | Required Compute & Database Nodes    |
+-----------------------------------------------------------------------------------------+
| 10 Users         | 15 req/s | < 25 ms            | 1 vCPU, 1 GB RAM (Single Node / M1)  |
| 100 Users        | 120 req/s| < 50 ms            | 2 vCPU, 4 GB RAM, 1 API + 1 Worker   |
| 1,000 Users      | 850 req/s| < 120 ms           | 3 API Replicas, Redis, RDS Postgres  |
| 10,000 Users     | 6,500 rps| < 200 ms           | 12 Pods (EKS), Aurora Multi-AZ, KEDA |
+-----------------------------------------------------------------------------------------+
```

### Resource Sizing Mathematical Model:
$$\text{Required Workers} = \left\lceil \frac{\text{Active Tasks} \times \text{Avg Task Duration (s)}}{\text{Target Queue SLA (s)}} \right\rceil$$

For 100 concurrent developers submitting tasks taking on average 3 seconds with a target queue wait time $< 2$ seconds:
$$\text{Required Workers} = \left\lceil \frac{100 \times 3.0}{2.0} \right\rceil = 150 \text{ worker task slots (distributed)}$$

