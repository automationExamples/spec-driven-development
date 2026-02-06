"""
JUnit XML Parser - Parse pytest JUnit XML output.

Extracts test results, failures, and metrics from JUnit XML format.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class JUnitTestCase:
    """Result of a single test case"""

    name: str
    classname: str
    time: float
    status: str  # "passed", "failed", "skipped", "error"
    failure_message: Optional[str] = None
    failure_type: Optional[str] = None
    failure_text: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None


@dataclass
class TestSuiteResult:
    """Result of a test suite"""

    name: str
    tests: int
    failures: int
    errors: int
    skipped: int
    time: float
    test_cases: list[JUnitTestCase] = field(default_factory=list)


@dataclass
class JUnitReport:
    """Complete JUnit report"""

    suites: list[TestSuiteResult] = field(default_factory=list)
    total_tests: int = 0
    total_passed: int = 0
    total_failures: int = 0
    total_errors: int = 0
    total_skipped: int = 0
    total_time: float = 0.0

    @property
    def success(self) -> bool:
        """True if all tests passed"""
        return self.total_failures == 0 and self.total_errors == 0


def parse_junit_xml(xml_content: str) -> JUnitReport:
    """
    Parse JUnit XML content into a structured report.

    Args:
        xml_content: Raw XML content as string

    Returns:
        JUnitReport with parsed results
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {e}")

    suites = []

    # Handle both <testsuites> and <testsuite> as root
    if root.tag == "testsuites":
        suite_elements = root.findall("testsuite")
    elif root.tag == "testsuite":
        suite_elements = [root]
    else:
        raise ValueError(f"Unexpected root element: {root.tag}")

    for suite_elem in suite_elements:
        suite = _parse_suite(suite_elem)
        suites.append(suite)

    # Calculate totals
    total_tests = sum(s.tests for s in suites)
    total_failures = sum(s.failures for s in suites)
    total_errors = sum(s.errors for s in suites)
    total_skipped = sum(s.skipped for s in suites)
    total_time = sum(s.time for s in suites)
    total_passed = total_tests - total_failures - total_errors - total_skipped

    return JUnitReport(
        suites=suites,
        total_tests=total_tests,
        total_passed=total_passed,
        total_failures=total_failures,
        total_errors=total_errors,
        total_skipped=total_skipped,
        total_time=total_time,
    )


def parse_junit_file(file_path: Path) -> JUnitReport:
    """
    Parse JUnit XML from a file.

    Args:
        file_path: Path to the JUnit XML file

    Returns:
        JUnitReport with parsed results
    """
    content = file_path.read_text()
    return parse_junit_xml(content)


def _parse_suite(elem: ET.Element) -> TestSuiteResult:
    """Parse a testsuite element"""
    test_cases = []
    for tc_elem in elem.findall("testcase"):
        test_cases.append(_parse_testcase(tc_elem))

    return TestSuiteResult(
        name=elem.get("name", ""),
        tests=int(elem.get("tests", 0)),
        failures=int(elem.get("failures", 0)),
        errors=int(elem.get("errors", 0)),
        skipped=int(elem.get("skipped", 0)),
        time=float(elem.get("time", 0)),
        test_cases=test_cases,
    )


def _parse_testcase(elem: ET.Element) -> JUnitTestCase:
    """Parse a testcase element"""
    status = "passed"
    failure_message = None
    failure_type = None
    failure_text = None

    # Check for failure
    failure = elem.find("failure")
    if failure is not None:
        status = "failed"
        failure_message = failure.get("message", "")
        failure_type = failure.get("type", "")
        failure_text = failure.text

    # Check for error
    error = elem.find("error")
    if error is not None:
        status = "error"
        failure_message = error.get("message", "")
        failure_type = error.get("type", "")
        failure_text = error.text

    # Check for skipped
    skipped = elem.find("skipped")
    if skipped is not None:
        status = "skipped"
        failure_message = skipped.get("message", "")

    # Get stdout/stderr
    stdout_elem = elem.find("system-out")
    stderr_elem = elem.find("system-err")

    return JUnitTestCase(
        name=elem.get("name", ""),
        classname=elem.get("classname", ""),
        time=float(elem.get("time", 0)),
        status=status,
        failure_message=failure_message,
        failure_type=failure_type,
        failure_text=failure_text,
        stdout=stdout_elem.text if stdout_elem is not None else None,
        stderr=stderr_elem.text if stderr_elem is not None else None,
    )


def get_failures(report: JUnitReport) -> list[JUnitTestCase]:
    """
    Extract all failed test cases from a report.

    Args:
        report: The JUnit report

    Returns:
        List of failed test cases
    """
    failures = []
    for suite in report.suites:
        for tc in suite.test_cases:
            if tc.status in ("failed", "error"):
                failures.append(tc)
    return failures
