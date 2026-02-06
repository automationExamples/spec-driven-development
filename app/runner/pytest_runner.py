"""
Pytest Runner - Execute pytest tests programmatically.

Runs generated tests and captures results including JUnit XML output.
"""

import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .junit_parser import parse_junit_file, get_failures


@dataclass
class FailedTest:
    """Information about a failed test"""

    name: str
    classname: str
    message: Optional[str] = None
    traceback: Optional[str] = None


@dataclass
class RunResult:
    """Result of a test run"""

    success: bool
    exit_code: int
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    total: int = 0
    duration: float = 0.0
    junit_xml_path: Optional[Path] = None
    stdout: str = ""
    stderr: str = ""
    failures: list[FailedTest] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "total": self.total,
            "duration": self.duration,
            "junit_xml_path": str(self.junit_xml_path) if self.junit_xml_path else None,
            "failures": [
                {
                    "name": f.name,
                    "classname": f.classname,
                    "message": f.message,
                    "traceback": f.traceback,
                }
                for f in self.failures
            ],
        }


def run_tests(
    test_dir: Path,
    base_url: str,
    output_dir: Optional[Path] = None,
    timeout: int = 300,
    verbose: bool = True,
) -> RunResult:
    """
    Run pytest on a test directory.

    Args:
        test_dir: Directory containing test files
        base_url: Base URL for the API under test
        output_dir: Directory to store artifacts (defaults to test_dir)
        timeout: Maximum execution time in seconds
        verbose: Enable verbose output

    Returns:
        RunResult with test execution details
    """
    if not test_dir.exists():
        return RunResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr=f"Test directory does not exist: {test_dir}",
        )

    output_dir = output_dir or test_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    junit_xml_path = output_dir / "junit.xml"

    # Build pytest command
    cmd = [
        "python",
        "-m",
        "pytest",
        str(test_dir),
        f"--junitxml={junit_xml_path}",
        "--tb=short",
    ]

    if verbose:
        cmd.append("-v")

    # Set up environment
    env = os.environ.copy()
    env["TARGET_BASE_URL"] = base_url
    env["PYTHONPATH"] = str(test_dir.parent)

    # Run pytest
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=str(test_dir.parent),
        )
        exit_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired:
        return RunResult(
            success=False,
            exit_code=-1,
            stdout="",
            stderr=f"Test execution timed out after {timeout} seconds",
            duration=timeout,
        )
    except Exception as e:
        return RunResult(
            success=False, exit_code=-1, stdout="", stderr=f"Failed to run tests: {e}"
        )

    duration = time.time() - start_time

    # Parse JUnit XML if it exists
    passed = 0
    failed = 0
    skipped = 0
    errors = 0
    total = 0
    failures = []

    if junit_xml_path.exists():
        try:
            report = parse_junit_file(junit_xml_path)
            passed = report.total_passed
            failed = report.total_failures
            skipped = report.total_skipped
            errors = report.total_errors
            total = report.total_tests

            # Extract failure details
            for tc in get_failures(report):
                failures.append(
                    FailedTest(
                        name=tc.name,
                        classname=tc.classname,
                        message=tc.failure_message,
                        traceback=tc.failure_text,
                    )
                )
        except Exception as e:
            stderr += f"\nFailed to parse JUnit XML: {e}"

    return RunResult(
        success=exit_code == 0,
        exit_code=exit_code,
        passed=passed,
        failed=failed,
        skipped=skipped,
        errors=errors,
        total=total,
        duration=duration,
        junit_xml_path=junit_xml_path if junit_xml_path.exists() else None,
        stdout=stdout,
        stderr=stderr,
        failures=failures,
    )


def get_junit_xml(run_result: RunResult) -> Optional[str]:
    """
    Get the raw JUnit XML content from a run result.

    Args:
        run_result: The run result

    Returns:
        Raw XML content or None if not available
    """
    if run_result.junit_xml_path and run_result.junit_xml_path.exists():
        return run_result.junit_xml_path.read_text()
    return None
