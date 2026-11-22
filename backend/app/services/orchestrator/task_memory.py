import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.core.logging import logger

class MemoryFact(BaseModel):
    statement: str
    verified_source: str  # e.g. "FILE_INSPECTION", "TEST_EXECUTION", "COMPILER"
    recorded_at: str

class ModelHypothesis(BaseModel):
    hypothesis: str
    confidence: float = 0.5
    status: str = "UNVERIFIED"  # UNVERIFIED | CONFIRMED | REFUTED
    recorded_at: str

class ToolExecutionRecord(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    exit_code: int
    duration_ms: int
    output_summary: str
    recorded_at: str

class RepairAttemptRecord(BaseModel):
    attempt_number: int
    failure_signature: str
    proposed_patch_summary: str
    outcome: str  # SUCCESS | FAILED | REVERTED
    recorded_at: str

class TaskMemory(BaseModel):
    task_id: str
    user_requirement: str
    relevant_files: List[str] = Field(default_factory=list)
    relevant_symbols: List[str] = Field(default_factory=list)
    verified_facts: List[MemoryFact] = Field(default_factory=list)
    model_hypotheses: List[ModelHypothesis] = Field(default_factory=list)
    tool_executions: List[ToolExecutionRecord] = Field(default_factory=list)
    implemented_patches: List[Dict[str, Any]] = Field(default_factory=list)
    repair_history: List[RepairAttemptRecord] = Field(default_factory=list)
    attempted_command_hashes: Set[str] = Field(default_factory=set)
    attempted_patch_hashes: Set[str] = Field(default_factory=set)
    last_checkpoint_at: Optional[str] = None

class TaskMemoryManager:
    """Manages task-scoped persistent memory, separating verified empirical facts

    from model hypotheses, tracking repair history, and compacting context budgets.
    """

    _memory_cache: Dict[str, TaskMemory] = {}

    @classmethod
    def _get_storage_path(cls, task_id: str) -> Path:
        mem_dir = settings.resolved_workspace_root / "task_memory"
        mem_dir.mkdir(parents=True, exist_ok=True)
        return mem_dir / f"{task_id}.json"

    @classmethod
    def get_or_create(cls, task_id: str, requirement: str = "") -> TaskMemory:
        if task_id in cls._memory_cache:
            return cls._memory_cache[task_id]

        storage_file = cls._get_storage_path(task_id)
        if storage_file.exists():
            try:
                data = json.loads(storage_file.read_text(encoding="utf-8"))
                mem = TaskMemory(**data)
                cls._memory_cache[task_id] = mem
                return mem
            except Exception as e:
                logger.warning(f"Failed to restore task memory for {task_id}: {e}")

        mem = TaskMemory(task_id=task_id, user_requirement=requirement)
        cls._memory_cache[task_id] = mem
        return mem

    @classmethod
    def record_fact(cls, task_id: str, statement: str, source: str = "EMPIRICAL_CHECK"):
        mem = cls.get_or_create(task_id)
        # Avoid duplicate statements
        if not any(f.statement == statement for f in mem.verified_facts):
            mem.verified_facts.append(MemoryFact(
                statement=statement,
                verified_source=source,
                recorded_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
            ))
            cls.persist_checkpoint(task_id)

    @classmethod
    def record_hypothesis(cls, task_id: str, hypothesis: str, confidence: float = 0.5):
        mem = cls.get_or_create(task_id)
        mem.model_hypotheses.append(ModelHypothesis(
            hypothesis=hypothesis,
            confidence=confidence,
            status="UNVERIFIED",
            recorded_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
        ))
        cls.persist_checkpoint(task_id)

    @classmethod
    def confirm_hypothesis(cls, task_id: str, hypothesis_substring: str):
        mem = cls.get_or_create(task_id)
        for h in mem.model_hypotheses:
            if hypothesis_substring in h.hypothesis:
                h.status = "CONFIRMED"
                cls.record_fact(task_id, f"Confirmed: {h.hypothesis}", source="VERIFIED_HYPOTHESIS")
        cls.persist_checkpoint(task_id)

    @classmethod
    def record_tool_call(
        cls,
        task_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        exit_code: int,
        duration_ms: int,
        output_summary: str
    ):
        mem = cls.get_or_create(task_id)
        mem.tool_executions.append(ToolExecutionRecord(
            tool_name=tool_name,
            arguments=arguments,
            exit_code=exit_code,
            duration_ms=duration_ms,
            output_summary=output_summary[:300],
            recorded_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
        ))
        # Hash command or action to prevent duplicate loops
        cmd_repr = f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"
        mem.attempted_command_hashes.add(str(hash(cmd_repr)))
        cls.persist_checkpoint(task_id)

    @classmethod
    def is_duplicate_action(cls, task_id: str, tool_name: str, arguments: Dict[str, Any]) -> bool:
        mem = cls.get_or_create(task_id)
        cmd_repr = f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"
        return str(hash(cmd_repr)) in mem.attempted_command_hashes

    @classmethod
    def record_repair(
        cls,
        task_id: str,
        failure_sig: str,
        patch_summary: str,
        outcome: str
    ):
        mem = cls.get_or_create(task_id)
        mem.repair_history.append(RepairAttemptRecord(
            attempt_number=len(mem.repair_history) + 1,
            failure_signature=failure_sig,
            proposed_patch_summary=patch_summary,
            outcome=outcome,
            recorded_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
        ))
        patch_hash = str(hash(patch_summary))
        mem.attempted_patch_hashes.add(patch_hash)
        cls.persist_checkpoint(task_id)

    @classmethod
    def is_duplicate_patch(cls, task_id: str, patch_content: str) -> bool:
        mem = cls.get_or_create(task_id)
        return str(hash(patch_content)) in mem.attempted_patch_hashes

    @classmethod
    def compact_context(cls, task_id: str, max_chars: int = 4000) -> str:
        """Compress memory into structured markdown prompt context adhering to token budget."""
        mem = cls.get_or_create(task_id)
        sections = [
            f"### TASK CONTEXT & MEMORY FOR {task_id}",
            f"Requirement: {mem.user_requirement}"
        ]

        if mem.verified_facts:
            sections.append("Verified Facts (Ground Truth):")
            for f in mem.verified_facts[-8:]:
                sections.append(f" - [{f.verified_source}] {f.statement}")

        if mem.relevant_files:
            sections.append(f"Relevant Files: {', '.join(mem.relevant_files)}")

        if mem.repair_history:
            sections.append("Previous Repair Attempts (Do NOT repeat identical failures):")
            for r in mem.repair_history[-3:]:
                sections.append(f" - Attempt #{r.attempt_number} ({r.outcome}): {r.failure_signature} -> {r.proposed_patch_summary}")

        combined = "\n".join(sections)
        if len(combined) > max_chars:
            return combined[:max_chars] + "\n...[Context compacted to fit budget]..."
        return combined

    @classmethod
    def persist_checkpoint(cls, task_id: str):
        mem = cls.get_or_create(task_id)
        mem.last_checkpoint_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        storage_file = cls._get_storage_path(task_id)
        try:
            storage_file.write_text(mem.model_dump_json(indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Error persisting checkpoint for task {task_id}: {e}")

    @classmethod
    def clear_memory(cls, task_id: str):
        cls._memory_cache.pop(task_id, None)
        storage_file = cls._get_storage_path(task_id)
        if storage_file.exists():
            storage_file.unlink()

