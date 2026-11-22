import re
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import deque

from backend.app.schemas.planning import (
    DynamicPlanStep,
    DynamicPlanOutput,
    PlanValidationResult,
    ScopeCreepEvaluation
)
from backend.app.schemas.task_understanding import TaskUnderstandingResult, TaskCategory, RiskLevel
from backend.app.services.repo_intelligence.scanner import RepositoryScanner
from backend.app.services.orchestrator.task_memory import TaskMemoryManager

class DynamicPlanner:
    """Dependency-aware engineering planner capable of topological task ordering,

    plan validation, and scope-creep detection.
    """

    @classmethod
    def create_plan(
        cls,
        task_id: str,
        requirement: str,
        understanding: TaskUnderstandingResult,
        scanner: RepositoryScanner,
        existing_plan: Optional[DynamicPlanOutput] = None
    ) -> DynamicPlanOutput:
        # 1. Analyze existing implementation & change impact
        target_files = list(understanding.target_files_hinted)
        if not target_files:
            all_files = scanner.list_repo_files()
            # Try to find file matching requirement tokens
            for f in all_files:
                stem = f.split(".")[0]
                if stem in requirement.lower():
                    target_files.append(f)
            if not target_files and all_files:
                target_files = [all_files[0]]

        impact_summaries = []
        for tf in target_files[:3]:
            try:
                imp = scanner.analyze_change_impact(tf)
                impact_summaries.append(imp.summary)
            except Exception:
                pass

        existing_analysis = " | ".join(impact_summaries) if impact_summaries else "Initial implementation inspection."

        # 2. Build structured steps based on category
        steps: List[DynamicPlanStep] = []
        step_counter = 1

        # Step 1: Pre-modification verification or test isolation
        test_file = f"test_{target_files[0]}" if target_files and not target_files[0].startswith("test_") else "test_suite.py"
        steps.append(DynamicPlanStep(
            step_order=step_counter,
            title="Inspect context and isolate regression test baseline",
            description=f"Inspect {target_files[0] if target_files else 'target files'} and ensure isolated workspace test discovery passes.",
            target_files=target_files[:2],
            prerequisite_steps=[],
            risk_level="LOW",
            acceptance_criteria=["TestRunner discovers valid test suite in isolated workspace"],
            verification_strategy="Automated test discovery"
        ))
        step_counter += 1

        # Step 2: Source modification
        steps.append(DynamicPlanStep(
            step_order=step_counter,
            title=f"Implement changes for {understanding.category.value}",
            description=f"Apply targeted patches to {', '.join(target_files)} adhering to requirement specifications.",
            target_files=target_files,
            prerequisite_steps=[1],
            risk_level=understanding.risk_level.value,
            acceptance_criteria=[c.description for c in understanding.acceptance_criteria[:2]],
            verification_strategy="AST syntax validation and diff inspection"
        ))
        step_counter += 1

        # Step 3: Verification & regression execution
        steps.append(DynamicPlanStep(
            step_order=step_counter,
            title="Run verification suite and self-debugging validation",
            description="Execute sandboxed tests. If failures occur, trigger bounded self-debugging repair loop.",
            target_files=target_files + ([test_file] if test_file not in target_files else []),
            prerequisite_steps=[2],
            risk_level="LOW",
            acceptance_criteria=["All tests execute with exit code 0"],
            verification_strategy="Sandboxed pytest/vitest execution"
        ))

        # 3. Validate and order steps
        val_result = cls.validate_and_order_steps(steps)
        ordered_steps = val_result.ordered_steps if val_result.is_valid else steps

        # 4. Acceptance criteria from understanding
        ac_list = [c.description for c in understanding.acceptance_criteria]

        plan = DynamicPlanOutput(
            objective=requirement,
            existing_implementation_analysis=existing_analysis,
            required_files=target_files,
            proposed_modifications=ordered_steps,
            dependencies=understanding.detected_dependencies,
            acceptance_criteria=ac_list,
            verification_strategy="Isolated execution sandbox with automated timeout and allowlist enforcement",
            risk_level=understanding.risk_level.value,
            expected_limitations=[
                "Modifications restricted strictly to isolated working directory until developer approval",
                "Subprocess execution limited to permitted executables without host network access"
            ],
            revision_count=(existing_plan.revision_count + 1) if existing_plan else 0
        )

        # Record in task memory
        TaskMemoryManager.record_fact(task_id, f"Plan generated with {len(ordered_steps)} steps and risk {plan.risk_level}")
        return plan

    @classmethod
    def validate_and_order_steps(cls, steps: List[DynamicPlanStep]) -> PlanValidationResult:
        """Topological sort of plan steps to ensure all prerequisite steps execute first.

        Detects cycles or invalid step references.
        """
        errors = []
        warnings = []
        step_map: Dict[int, DynamicPlanStep] = {s.step_order: s for s in steps}

        # Check references
        adj: Dict[int, List[int]] = {s.step_order: [] for s in steps}
        in_degree: Dict[int, int] = {s.step_order: 0 for s in steps}

        for s in steps:
            for prereq in s.prerequisite_steps:
                if prereq not in step_map:
                    errors.append(f"Step {s.step_order} references non-existent prerequisite step {prereq}")
                elif prereq == s.step_order:
                    errors.append(f"Step {s.step_order} cannot depend on itself")
                else:
                    adj[prereq].append(s.step_order)
                    in_degree[s.step_order] += 1

        if errors:
            return PlanValidationResult(is_valid=False, errors=errors, warnings=warnings, ordered_steps=steps)

        # Kahn's algorithm for topological sort
        queue = deque([s_order for s_order, deg in in_degree.items() if deg == 0])
        ordered_orders = []

        while queue:
            curr = queue.popleft()
            ordered_orders.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered_orders) != len(steps):
            errors.append("Circular dependency detected among plan steps")
            return PlanValidationResult(is_valid=False, errors=errors, warnings=warnings, ordered_steps=steps)

        # Re-index step orders cleanly
        ordered_steps = []
        order_translation = {old_order: new_order for new_order, old_order in enumerate(ordered_orders, start=1)}
        for old_order in ordered_orders:
            orig_step = step_map[old_order]
            reordered = orig_step.model_copy()
            reordered.step_order = order_translation[old_order]
            reordered.prerequisite_steps = [order_translation[p] for p in orig_step.prerequisite_steps if p in order_translation]
            ordered_steps.append(reordered)

        return PlanValidationResult(is_valid=True, errors=[], warnings=warnings, ordered_steps=ordered_steps)

    @classmethod
    def detect_scope_creep(
        cls,
        original_plan: DynamicPlanOutput,
        revised_plan: DynamicPlanOutput
    ) -> ScopeCreepEvaluation:
        """Detects whether replanning introduced substantial scope expansion requiring

        re-submission to the human approval gate.
        """
        reasons = []

        # 1. New target files added
        orig_files = set(original_plan.required_files)
        new_files = set(revised_plan.required_files)
        added_files = new_files - orig_files
        if added_files:
            reasons.append(f"Plan introduces new unapproved files: {', '.join(added_files)}")

        # 2. Step count expansion > 30%
        orig_step_count = len(original_plan.proposed_modifications)
        new_step_count = len(revised_plan.proposed_modifications)
        if orig_step_count > 0 and (new_step_count - orig_step_count) / orig_step_count > 0.3:
            reasons.append(f"Step count increased by {new_step_count - orig_step_count} steps (> 30% expansion)")

        # 3. Elevated risk level
        risk_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        if risk_rank.get(revised_plan.risk_level, 1) > risk_rank.get(original_plan.risk_level, 1):
            reasons.append(f"Plan risk level elevated from {original_plan.risk_level} to {revised_plan.risk_level}")

        has_creep = len(reasons) > 0
        return ScopeCreepEvaluation(
            has_scope_creep=has_creep,
            reasons=reasons,
            requires_renewed_approval=has_creep
        )

