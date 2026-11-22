import time
import resource
import threading
from typing import Dict, Any

class PrometheusMetricsRegistry:
    """Thread-safe Prometheus metrics registry for AETHER ENGINEER application monitoring."""
    def __init__(self):
        self._lock = threading.Lock()
        self.http_requests_total: Dict[str, int] = {}  # "method:path:status" -> count
        self.http_request_durations: Dict[str, float] = {}  # "method:path" -> total duration
        self.active_tasks: int = 0
        self.tasks_completed_total: int = 0
        self.tasks_failed_total: int = 0
        self.llm_tokens_total: Dict[str, int] = {}  # provider -> tokens
        self.llm_cost_dollars: Dict[str, float] = {}  # provider -> cost
        self.security_violations_total: Dict[str, int] = {}  # vector -> count

    def record_request(self, method: str, path: str, status_code: int, duration_sec: float) -> None:
        key = f"{method}:{path}:{status_code}"
        dur_key = f"{method}:{path}"
        with self._lock:
            self.http_requests_total[key] = self.http_requests_total.get(key, 0) + 1
            self.http_request_durations[dur_key] = self.http_request_durations.get(dur_key, 0.0) + duration_sec

    def set_active_tasks(self, count: int) -> None:
        with self._lock:
            self.active_tasks = max(0, count)

    def record_task_outcome(self, success: bool) -> None:
        with self._lock:
            if success:
                self.tasks_completed_total += 1
            else:
                self.tasks_failed_total += 1

    def record_llm_usage(self, provider: str, tokens: int, cost: float) -> None:
        with self._lock:
            self.llm_tokens_total[provider] = self.llm_tokens_total.get(provider, 0) + tokens
            self.llm_cost_dollars[provider] = self.llm_cost_dollars.get(provider, 0.0) + cost

    def record_security_violation(self, vector: str) -> None:
        with self._lock:
            self.security_violations_total[vector] = self.security_violations_total.get(vector, 0) + 1

    def generate_prometheus_output(self) -> str:
        """Formats collected metrics in standard Prometheus exposition format."""
        lines = []

        # System Memory RSS
        usage = resource.getrusage(resource.RUSAGE_SELF)
        rss_bytes = usage.ru_maxrss
        # macOS returns bytes in ru_maxrss
        lines.append("# HELP aether_process_resident_memory_bytes Resident memory size in bytes.")
        lines.append("# TYPE aether_process_resident_memory_bytes gauge")
        lines.append(f"aether_process_resident_memory_bytes {rss_bytes}")

        # Active tasks
        lines.append("# HELP aether_active_tasks Number of engineering tasks currently executing.")
        lines.append("# TYPE aether_active_tasks gauge")
        lines.append(f"aether_active_tasks {self.active_tasks}")

        # Task completion counts
        lines.append("# HELP aether_tasks_completed_total Total successfully resolved engineering tasks.")
        lines.append("# TYPE aether_tasks_completed_total counter")
        lines.append(f"aether_tasks_completed_total {self.tasks_completed_total}")

        lines.append("# HELP aether_tasks_failed_total Total failed engineering tasks.")
        lines.append("# TYPE aether_tasks_failed_total counter")
        lines.append(f"aether_tasks_failed_total {self.tasks_failed_total}")

        # HTTP Requests
        lines.append("# HELP aether_http_requests_total Total HTTP requests handled.")
        lines.append("# TYPE aether_http_requests_total counter")
        for k, v in self.http_requests_total.items():
            parts = k.split(":")
            method, path, st = parts[0], parts[1], parts[2]
            lines.append(f'aether_http_requests_total{{method="{method}",path="{path}",status="{st}"}} {v}')

        # LLM Tokens and Cost
        lines.append("# HELP aether_llm_tokens_total Cumulative LLM tokens consumed.")
        lines.append("# TYPE aether_llm_tokens_total counter")
        for p, tokens in self.llm_tokens_total.items():
            lines.append(f'aether_llm_tokens_total{{provider="{p}"}} {tokens}')

        lines.append("# HELP aether_llm_cost_dollars Cumulative estimated LLM inference cost.")
        lines.append("# TYPE aether_llm_cost_dollars counter")
        for p, cost in self.llm_cost_dollars.items():
            lines.append(f'aether_llm_cost_dollars{{provider="{p}"}} {round(cost, 5)}')

        # Security Violations
        lines.append("# HELP aether_security_violations_total Total prevented security attack vectors.")
        lines.append("# TYPE aether_security_violations_total counter")
        for vec, count in self.security_violations_total.items():
            lines.append(f'aether_security_violations_total{{vector="{vec}"}} {count}')

        return "\n".join(lines) + "\n"

metrics = PrometheusMetricsRegistry()

