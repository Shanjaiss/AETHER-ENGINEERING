import re
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from backend.app.schemas.task_understanding import (
    IntentType,
    TaskCategory,
    RiskLevel,
    AcceptanceCriterion,
    AmbiguityAssessment,
    TaskUnderstandingResult
)

class TaskUnderstandingEngine:
    """Analyzes natural-language software engineering requirements to extract intent,

    category, ambiguity, risk, and structured acceptance criteria.
    """

    HIGH_RISK_KEYWORDS = [
        "drop table", "truncate", "rm -rf", "delete database", "drop database",
        "purge", "wipe", "force push", "production", "kill process", "eval(",
        "chmod 777", "sudo", "privilege", "system override", "ignore all instructions",
        "ignore previous instructions", "override instructions"
    ]

    SECURITY_KEYWORDS = [
        "auth", "jwt", "token", "password", "hash", "secret", "timing attack",
        "csrf", "xss", "sql injection", "encryption", "sanitiz", "credential"
    ]

    BUG_KEYWORDS = [
        "fix", "bug", "error", "broken", "fail", "failing", "crash", "issue",
        "500", "404", "exception", "traceback", "incorrect", "defect", "flaky"
    ]

    FEATURE_KEYWORDS = [
        "add", "implement", "create", "support", "new", "feature", "endpoint",
        "route", "handler", "service", "capability"
    ]

    REFACTOR_KEYWORDS = [
        "refactor", "cleanup", "clean up", "restructure", "simplify", "decouple",
        "optimize", "modularize", "reorganize", "rename"
    ]

    TEST_KEYWORDS = [
        "test", "tests", "unit test", "pytest", "vitest", "coverage", "mock",
        "regression test", "assert", "spec"
    ]

    INFO_KEYWORDS = [
        "what", "how", "where", "why", "explain", "describe", "overview",
        "summarize", "list files", "tell me"
    ]

    VAGUE_PHRASES = [
        "make it work", "fix it", "it is broken", "something is wrong",
        "do it", "fix the error", "help me with this", "update code"
    ]

    @classmethod
    def analyze(
        cls,
        title: str,
        description: str,
        repo_files: Optional[List[str]] = None,
        task_id: Optional[str] = None
    ) -> TaskUnderstandingResult:
        full_text = f"{title}\n{description}".strip()
        lower_text = full_text.lower()

        # 1. Determine Intent
        intent = cls._classify_intent(lower_text)

        # 2. Determine Category
        category = cls._classify_category(lower_text, intent)

        # 3. Detect Ambiguity
        ambiguity = cls._detect_ambiguity(title, description, full_text, repo_files)

        # 4. Detect Hinted Target Files
        hinted_files = cls._extract_hinted_files(full_text, repo_files)

        # 5. Detect Dependencies / Tech
        tech, deps = cls._detect_technologies(lower_text)

        # 6. Assess Risk Level
        risk_level, risk_reasons, requires_approval = cls._assess_risk(lower_text, intent, hinted_files)

        # 7. Generate Acceptance Criteria
        criteria = cls._generate_acceptance_criteria(title, description, category, hinted_files)

        summary = cls._generate_summary(intent, category, title, hinted_files, risk_level)

        return TaskUnderstandingResult(
            task_id=task_id,
            intent=intent,
            category=category,
            primary_technology=tech,
            summary=summary,
            target_files_hinted=hinted_files,
            detected_dependencies=deps,
            risk_level=risk_level,
            risk_reasons=risk_reasons,
            requires_approval_gate=requires_approval,
            ambiguity=ambiguity,
            acceptance_criteria=criteria,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

    @classmethod
    def _classify_intent(cls, text: str) -> IntentType:
        if any(k in text for k in cls.HIGH_RISK_KEYWORDS):
            return IntentType.HIGH_RISK_OPERATION

        is_info = any(text.startswith(k) or f" {k} " in text for k in cls.INFO_KEYWORDS)
        has_question_mark = "?" in text

        if is_info and not any(k in text for k in ["fix", "implement", "add", "refactor", "create"]):
            return IntentType.INFORMATION_REQUEST

        if any(k in text for k in ["analyze", "inspect", "audit", "scan", "check structure", "review repo"]) and not any(
            k in text for k in ["fix", "modify", "implement", "apply", "patch", "repair", "refactor", "create", "write"]
        ):
            return IntentType.READONLY_ANALYSIS

        if any(k in text for k in ["run tests", "execute tests", "verify tests", "run pytest", "run vitest"]) and not any(
            k in text for k in ["fix", "write", "create", "implement", "patch", "modify", "repair"]
        ):
            return IntentType.TEST_EXECUTION

        return IntentType.CODE_MODIFICATION

    @classmethod
    def _classify_category(cls, text: str, intent: IntentType) -> TaskCategory:
        if intent == IntentType.INFORMATION_REQUEST or intent == IntentType.READONLY_ANALYSIS:
            return TaskCategory.GENERAL_QUERY

        # Check for Security
        if any(k in text for k in cls.SECURITY_KEYWORDS):
            if any(k in text for k in cls.BUG_KEYWORDS):
                return TaskCategory.BUG_FIX
            return TaskCategory.SECURITY_HARDENING

        # Check for Bug Fix
        if any(k in text for k in cls.BUG_KEYWORDS):
            return TaskCategory.BUG_FIX

        # Check for Test Generation
        if any(k in text for k in cls.TEST_KEYWORDS) and any(k in text for k in ["write", "generate", "create", "add test"]):
            return TaskCategory.TEST_GENERATION

        # Check for Refactoring
        if any(k in text for k in cls.REFACTOR_KEYWORDS):
            return TaskCategory.REFACTORING

        # Check for Dependency Update
        if any(k in text for k in ["requirements.txt", "package.json", "upgrade dep", "bump version"]):
            return TaskCategory.DEPENDENCY_UPDATE

        # Check for Documentation
        if any(k in text for k in ["readme", "docstring", "documentation", "document"]):
            return TaskCategory.DOCUMENTATION

        # Default to Feature Implementation if modification
        if intent == IntentType.CODE_MODIFICATION:
            return TaskCategory.FEATURE_IMPLEMENTATION

        return TaskCategory.GENERAL_QUERY

    @classmethod
    def _detect_ambiguity(
        cls,
        title: str,
        description: str,
        full_text: str,
        repo_files: Optional[List[str]] = None
    ) -> AmbiguityAssessment:
        missing_elements = []
        clarifications = []
        score = 0.0

        words = full_text.split()
        if len(words) < 6:
            score += 0.4
            missing_elements.append("Requirement is extremely brief (< 6 words)")
            clarifications.append("Can you provide more detail on the desired behavior or expected outcome?")
        elif len(words) < 15:
            score += 0.2
            missing_elements.append("Requirement has limited context (< 15 words)")

        lower = full_text.lower()
        for phrase in cls.VAGUE_PHRASES:
            if phrase in lower:
                score += 0.3
                missing_elements.append(f"Contains ambiguous phrase: '{phrase}'")
                clarifications.append("What specific error message, behavior, or file should be targeted?")
                break

        # Check if any file is hinted
        has_file_mention = bool(re.search(r"[\w/\-]+\.(py|ts|tsx|js|jsx|json|yaml|yml|md|html)", full_text))
        if not has_file_mention and repo_files and len(repo_files) > 10:
            score += 0.2
            missing_elements.append("No specific target file or component specified in a multi-file repository")
            clarifications.append("Which file or module is responsible for this functionality?")

        # Check for expected outcome
        has_outcome = any(k in lower for k in ["should", "must", "expected", "return", "pass", "so that", "assert"])
        if not has_outcome:
            score += 0.2
            missing_elements.append("No explicit expected behavior or acceptance outcome described")
            clarifications.append("What is the expected output or assertion that defines success?")

        score = min(round(score, 2), 1.0)
        is_ambiguous = score >= 0.4

        return AmbiguityAssessment(
            is_ambiguous=is_ambiguous,
            ambiguity_score=score,
            missing_elements=missing_elements,
            clarification_questions=clarifications
        )

    @classmethod
    def _extract_hinted_files(cls, text: str, repo_files: Optional[List[str]] = None) -> List[str]:
        hints = set()
        file_regex = re.compile(r"([a-zA-Z0-9_\-./]+\.(py|ts|tsx|js|jsx|json|yaml|yml|md|html|css|sql))")
        for match in file_regex.finditer(text):
            hints.add(match.group(1).lstrip("./"))

        if repo_files:
            # Match bare names without path
            for rf in repo_files:
                name = Path(rf).name
                if f" {name} " in f" {text} " or f"'{name}'" in text or f'"{name}"' in text:
                    hints.add(rf)

        return sorted(list(hints))

    @classmethod
    def _detect_technologies(cls, text: str) -> Tuple[Optional[str], List[str]]:
        deps = []
        primary = None

        tech_map = {
            "fastapi": "FastAPI",
            "react": "React",
            "typescript": "TypeScript",
            "python": "Python",
            "pytest": "Pytest",
            "vitest": "Vitest",
            "sqlalchemy": "SQLAlchemy",
            "pydantic": "Pydantic",
            "tailwind": "Tailwind CSS",
            "sqlite": "SQLite",
            "docker": "Docker",
            "node": "Node.js"
        }

        for kw, name in tech_map.items():
            if kw in text:
                deps.append(name)
                if not primary and name in ["FastAPI", "React", "TypeScript", "Python"]:
                    primary = name

        return primary or ("Python" if "py" in text else None), deps

    @classmethod
    def _assess_risk(
        cls,
        text: str,
        intent: IntentType,
        hinted_files: List[str]
    ) -> Tuple[RiskLevel, List[str], bool]:
        reasons = []

        if intent == IntentType.HIGH_RISK_OPERATION or any(k in text for k in cls.HIGH_RISK_KEYWORDS):
            reasons.append("Contains destructive or privileged system commands")
            return RiskLevel.CRITICAL, reasons, True

        # Read-only or information requests carry zero filesystem mutation risk
        if intent in [IntentType.INFORMATION_REQUEST, IntentType.READONLY_ANALYSIS]:
            reasons.append("Read-only or informational request with zero filesystem mutation risk")
            return RiskLevel.LOW, reasons, False

        is_auth_security = any(k in text for k in cls.SECURITY_KEYWORDS) or any(
            "auth" in f or "security" in f for f in hinted_files
        )
        if is_auth_security:
            reasons.append("Affects authentication, cryptography, or security boundaries")

        affects_db = any(k in text for k in ["database", "migration", "alembic", "schema", "table"])
        if affects_db:
            reasons.append("Affects database schema or data persistence")

        if is_auth_security or affects_db:
            return RiskLevel.HIGH, reasons, True

        if intent == IntentType.CODE_MODIFICATION:
            reasons.append("Modifies source files in the codebase")
            return RiskLevel.MEDIUM, reasons, True

        if intent == IntentType.TEST_EXECUTION:
            reasons.append("Executes test commands inside sandboxed environment")
            return RiskLevel.LOW, reasons, False

        reasons.append("Low risk operation")
        return RiskLevel.LOW, reasons, False

    @classmethod
    def _generate_acceptance_criteria(
        cls,
        title: str,
        description: str,
        category: TaskCategory,
        hinted_files: List[str]
    ) -> List[AcceptanceCriterion]:
        criteria = []
        idx = 1

        if category == TaskCategory.BUG_FIX:
            criteria.append(AcceptanceCriterion(
                id=f"AC-{idx:02d}",
                description=f"Identify and isolate the root cause of the reported defect: '{title}'",
                verification_type="CODE_INSPECTION",
                target_area=hinted_files[0] if hinted_files else "Application logic"
            ))
            idx += 1
            criteria.append(AcceptanceCriterion(
                id=f"AC-{idx:02d}",
                description="Implement regression test case reproducing the bug that passes after fix",
                verification_type="TEST",
                target_area="Test suite"
            ))
            idx += 1
            criteria.append(AcceptanceCriterion(
                id=f"AC-{idx:02d}",
                description="All existing test suites execute and pass with exit code 0",
                verification_type="TEST",
                target_area="Complete test suite"
            ))
        elif category == TaskCategory.FEATURE_IMPLEMENTATION:
            criteria.append(AcceptanceCriterion(
                id=f"AC-{idx:02d}",
                description=f"Implement feature requirements for '{title}' with clean typing and validation",
                verification_type="CODE_INSPECTION",
                target_area=hinted_files[0] if hinted_files else "Feature module"
            ))
            idx += 1
            criteria.append(AcceptanceCriterion(
                id=f"AC-{idx:02d}",
                description="Add unit and integration tests covering positive and edge case scenarios",
                verification_type="TEST",
                target_area="Test suite"
            ))
            idx += 1
            criteria.append(AcceptanceCriterion(
                id=f"AC-{idx:02d}",
                description="Ensure zero regressions across existing functionality",
                verification_type="TEST",
                target_area="Complete test suite"
            ))
        elif category == TaskCategory.REFACTORING:
            criteria.append(AcceptanceCriterion(
                id=f"AC-{idx:02d}",
                description="Refactor code structure while preserving exact external API contracts",
                verification_type="CODE_INSPECTION",
                target_area=hinted_files[0] if hinted_files else "Refactored module"
            ))
            idx += 1
            criteria.append(AcceptanceCriterion(
                id=f"AC-{idx:02d}",
                description="All existing regression tests pass with zero behavioral divergence",
                verification_type="TEST",
                target_area="Test suite"
            ))
        else:
            criteria.append(AcceptanceCriterion(
                id=f"AC-{idx:02d}",
                description=f"Fulfill objective: '{title}'",
                verification_type="CODE_INSPECTION",
                target_area="Target component"
            ))

        return criteria

    @classmethod
    def _generate_summary(
        cls,
        intent: IntentType,
        category: TaskCategory,
        title: str,
        hinted_files: List[str],
        risk_level: RiskLevel
    ) -> str:
        file_part = f" targeting {', '.join(hinted_files)}" if hinted_files else ""
        return (
            f"Detected {intent.value} ({category.value}){file_part} with {risk_level.value} risk level. "
            f"Requirement: {title}."
        )
