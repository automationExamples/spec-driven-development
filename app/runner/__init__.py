# Runner package
from .pytest_runner import run_tests, RunResult
from .junit_parser import parse_junit_xml, JUnitReport, JUnitTestCase

# Keep TestCaseResult as alias for backwards compatibility
TestCaseResult = JUnitTestCase

__all__ = ["run_tests", "RunResult", "parse_junit_xml", "JUnitReport", "JUnitTestCase", "TestCaseResult"]
