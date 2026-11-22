import re
from typing import Dict, Any, List, Optional

class FailureClassifier:
    """Classifies test and build failures, parses stack traces, localizes defect lines,

    and generates evidence-based root-cause hypotheses and regression test templates.
    """

    @staticmethod
    def classify(stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
        combined = f"{stdout}\n{stderr}"
        stack_frames = FailureClassifier._parse_stack_frames(combined)

        culprit_file = None
        culprit_line = None
        culprit_func = None

        # Localize defect: find the highest application frame (non-pytest internal)
        for frame in reversed(stack_frames):
            fpath = frame["file"]
            if not any(ignore in fpath for ignore in ["pytest", "pluggy", "unittest", "site-packages", "_pytest"]):
                culprit_file = fpath
                culprit_line = frame["line"]
                culprit_func = frame.get("function")
                break

        # 1. Timeout
        if exit_code == -1 or "timed out" in combined.lower():
            return {
                "category": "TIMEOUT_ERROR",
                "summary": "Execution exceeded maximum allowed runtime.",
                "failing_file": culprit_file,
                "failing_line": culprit_line,
                "offending_symbol": culprit_func,
                "stack_frames": stack_frames,
                "hypothesis": "Possible infinite loop, deadlock, or unhandled blocking I/O operation.",
                "suggested_regression_test": "def test_timeout_regression():\n    # Test with bounded execution\n    pass\n"
            }

        # 2. Syntax Error
        if "SyntaxError" in combined:
            match = re.search(r'File "([^"]+)", line (\d+)', combined)
            f_file = match.group(1) if match else culprit_file
            f_line = int(match.group(2)) if match else culprit_line
            return {
                "category": "SYNTAX_ERROR",
                "summary": f"Source code contains invalid syntax at {f_file}:{f_line}.",
                "failing_file": f_file,
                "failing_line": f_line,
                "offending_symbol": None,
                "stack_frames": stack_frames,
                "hypothesis": "Malformed code patch, unclosed brackets, or invalid language construct.",
                "suggested_regression_test": ""
            }

        # 3. Import / Module Error
        if "ModuleNotFoundError" in combined or "ImportError" in combined:
            match = re.search(r"No module named '([^']+)'", combined) or re.search(r"cannot import name '([^']+)'", combined)
            missing = match.group(1) if match else "unknown"
            return {
                "category": "IMPORT_ERROR",
                "summary": f"Missing module or invalid import: '{missing}'",
                "failing_file": culprit_file,
                "failing_line": culprit_line,
                "offending_symbol": missing,
                "stack_frames": stack_frames,
                "hypothesis": f"Required dependency or symbol '{missing}' is not available in the execution environment.",
                "suggested_regression_test": f"def test_import_regression():\n    import {missing}\n"
            }

        # 4. ZeroDivisionError
        if "ZeroDivisionError" in combined:
            return {
                "category": "ZERO_DIVISION_ERROR",
                "summary": f"ZeroDivisionError detected at {culprit_file}:{culprit_line}",
                "failing_file": culprit_file,
                "failing_line": culprit_line,
                "offending_symbol": culprit_func,
                "stack_frames": stack_frames,
                "hypothesis": f"Arithmetic division by zero at {culprit_file}:{culprit_line}. Denominator evaluated to 0 without guard.",
                "suggested_regression_test": f"def test_zero_division_guard():\n    # Assert function returns 0 or raises handled error when denominator is 0\n    pass\n"
            }

        # 5. KeyError
        if "KeyError" in combined:
            match = re.search(r"KeyError:\s*['\"]?([^'\"\n]+)['\"]?", combined)
            missing_key = match.group(1) if match else "unknown"
            return {
                "category": "KEY_ERROR",
                "summary": f"KeyError: missing key '{missing_key}' at {culprit_file}:{culprit_line}",
                "failing_file": culprit_file,
                "failing_line": culprit_line,
                "offending_symbol": missing_key,
                "stack_frames": stack_frames,
                "hypothesis": f"Dictionary access for key '{missing_key}' failed without .get() fallback.",
                "suggested_regression_test": f"def test_missing_key_fallback():\n    # Test dictionary without '{missing_key}' key\n    pass\n"
            }

        # 6. Type Error
        if "TypeError" in combined:
            match = re.search(r"TypeError:\s*([^\n]+)", combined)
            msg = match.group(1) if match else "Type mismatch"
            return {
                "category": "TYPE_ERROR",
                "summary": f"TypeError: {msg} at {culprit_file}:{culprit_line}",
                "failing_file": culprit_file,
                "failing_line": culprit_line,
                "offending_symbol": culprit_func,
                "stack_frames": stack_frames,
                "hypothesis": f"Type mismatch or invalid parameter invocation at {culprit_file}:{culprit_line}: {msg}.",
                "suggested_regression_test": "def test_type_error_regression():\n    pass\n"
            }

        # 7. Assertion Error
        if "AssertionError" in combined or "assert " in combined:
            test_match = re.search(r'def (test_[a-zA-Z0-9_]+)', combined)
            test_name = test_match.group(1) if test_match else "test assertion"
            return {
                "category": "ASSERTION_ERROR",
                "summary": f"Verification test failed assertion: {test_name}",
                "failing_file": culprit_file,
                "failing_line": culprit_line,
                "offending_symbol": test_name,
                "stack_frames": stack_frames,
                "hypothesis": f"Logic mismatch between implementation in {culprit_file or 'target'} and assertions in {test_name}.",
                "suggested_regression_test": f"def test_{test_name}_regression():\n    # Re-verify assertion failure conditions\n    pass\n"
            }

        # Default: Runtime Error
        return {
            "category": "RUNTIME_ERROR",
            "summary": "Non-zero exit code during verification.",
            "failing_file": culprit_file,
            "failing_line": culprit_line,
            "offending_symbol": culprit_func,
            "stack_frames": stack_frames,
            "hypothesis": f"Unclassified runtime exception at {culprit_file or 'unknown'}:{culprit_line or '0'}.",
            "suggested_regression_test": ""
        }

    @staticmethod
    def _parse_stack_frames(trace_text: str) -> List[Dict[str, Any]]:
        frames = []
        frame_pattern = re.compile(r'File "([^"]+)", line (\d+)(?:, in ([^\n]+))?(?:\n\s+(.+))?')
        for match in frame_pattern.finditer(trace_text):
            frames.append({
                "file": match.group(1),
                "line": int(match.group(2)),
                "function": match.group(3) if match.group(3) else "module",
                "code_line": match.group(4).strip() if match.group(4) else ""
            })
        return frames
