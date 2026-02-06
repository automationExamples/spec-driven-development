"""
Unit tests for JUnit XML parser.
"""

import pytest
from app.runner.junit_parser import (
    parse_junit_xml,
    get_failures,
    JUnitReport,
    JUnitTestCase,
)


class TestParseJunitXml:
    """Tests for parse_junit_xml function"""

    def test_parse_empty_testsuite(self):
        """Should parse empty test suite"""
        xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="0" failures="0" errors="0" skipped="0" time="0.001">
</testsuite>"""

        report = parse_junit_xml(xml)

        assert report.total_tests == 0
        assert report.total_passed == 0
        assert report.total_failures == 0
        assert report.success is True

    def test_parse_all_passing(self):
        """Should parse test suite with all passing tests"""
        xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="3" failures="0" errors="0" skipped="0" time="1.234">
    <testcase name="test_one" classname="tests.test_example" time="0.100"></testcase>
    <testcase name="test_two" classname="tests.test_example" time="0.200"></testcase>
    <testcase name="test_three" classname="tests.test_example" time="0.300"></testcase>
</testsuite>"""

        report = parse_junit_xml(xml)

        assert report.total_tests == 3
        assert report.total_passed == 3
        assert report.total_failures == 0
        assert report.success is True
        assert len(report.suites) == 1
        assert len(report.suites[0].test_cases) == 3

    def test_parse_with_failures(self):
        """Should parse test suite with failures"""
        xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="2" failures="1" errors="0" skipped="0" time="0.500">
    <testcase name="test_pass" classname="tests.test_example" time="0.100"></testcase>
    <testcase name="test_fail" classname="tests.test_example" time="0.200">
        <failure message="AssertionError: assert 1 == 2">
def test_fail():
    assert 1 == 2
AssertionError: assert 1 == 2
        </failure>
    </testcase>
</testsuite>"""

        report = parse_junit_xml(xml)

        assert report.total_tests == 2
        assert report.total_passed == 1
        assert report.total_failures == 1
        assert report.success is False

        failures = get_failures(report)
        assert len(failures) == 1
        assert failures[0].name == "test_fail"
        assert "assert 1 == 2" in failures[0].failure_message

    def test_parse_with_errors(self):
        """Should parse test suite with errors"""
        xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="1" failures="0" errors="1" skipped="0" time="0.100">
    <testcase name="test_error" classname="tests.test_example" time="0.100">
        <error message="ValueError: something went wrong" type="ValueError">
Traceback...
        </error>
    </testcase>
</testsuite>"""

        report = parse_junit_xml(xml)

        assert report.total_tests == 1
        assert report.total_errors == 1
        assert report.success is False

        failures = get_failures(report)
        assert len(failures) == 1
        assert failures[0].status == "error"

    def test_parse_with_skipped(self):
        """Should parse test suite with skipped tests"""
        xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="2" failures="0" errors="0" skipped="1" time="0.200">
    <testcase name="test_pass" classname="tests.test_example" time="0.100"></testcase>
    <testcase name="test_skip" classname="tests.test_example" time="0.001">
        <skipped message="Skipped: not implemented yet"></skipped>
    </testcase>
</testsuite>"""

        report = parse_junit_xml(xml)

        assert report.total_tests == 2
        assert report.total_passed == 1
        assert report.total_skipped == 1
        assert report.success is True

    def test_parse_testsuites_root(self):
        """Should parse XML with testsuites as root element"""
        xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
    <testsuite name="suite1" tests="1" failures="0" errors="0" skipped="0" time="0.100">
        <testcase name="test_one" classname="tests.suite1" time="0.100"></testcase>
    </testsuite>
    <testsuite name="suite2" tests="1" failures="0" errors="0" skipped="0" time="0.100">
        <testcase name="test_two" classname="tests.suite2" time="0.100"></testcase>
    </testsuite>
</testsuites>"""

        report = parse_junit_xml(xml)

        assert len(report.suites) == 2
        assert report.total_tests == 2

    def test_parse_invalid_xml_raises_error(self):
        """Should raise error for invalid XML"""
        xml = "not valid xml <<<"

        with pytest.raises(ValueError, match="Invalid XML"):
            parse_junit_xml(xml)

    def test_parse_unexpected_root_raises_error(self):
        """Should raise error for unexpected root element"""
        xml = """<?xml version="1.0"?><something></something>"""

        with pytest.raises(ValueError, match="Unexpected root element"):
            parse_junit_xml(xml)

    def test_extracts_stdout_stderr(self):
        """Should extract system-out and system-err"""
        xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="1" failures="0" errors="0" skipped="0" time="0.100">
    <testcase name="test_output" classname="tests.test_example" time="0.100">
        <system-out>This is stdout</system-out>
        <system-err>This is stderr</system-err>
    </testcase>
</testsuite>"""

        report = parse_junit_xml(xml)

        tc = report.suites[0].test_cases[0]
        assert tc.stdout == "This is stdout"
        assert tc.stderr == "This is stderr"

    def test_calculates_duration(self):
        """Should calculate total duration from suites"""
        xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
    <testsuite name="suite1" tests="1" failures="0" errors="0" skipped="0" time="1.5">
        <testcase name="test_one" classname="tests" time="1.5"></testcase>
    </testsuite>
    <testsuite name="suite2" tests="1" failures="0" errors="0" skipped="0" time="2.5">
        <testcase name="test_two" classname="tests" time="2.5"></testcase>
    </testsuite>
</testsuites>"""

        report = parse_junit_xml(xml)

        assert report.total_time == 4.0


class TestGetFailures:
    """Tests for get_failures function"""

    def test_returns_empty_for_all_passing(self):
        """Should return empty list when all tests pass"""
        report = JUnitReport(total_tests=2, total_passed=2)
        assert get_failures(report) == []

    def test_returns_failed_tests(self):
        """Should return failed test cases"""
        from app.runner.junit_parser import TestSuiteResult

        report = JUnitReport(
            suites=[
                TestSuiteResult(
                    name="test",
                    tests=2,
                    failures=1,
                    errors=0,
                    skipped=0,
                    time=1.0,
                    test_cases=[
                        JUnitTestCase(
                            name="test_pass", classname="t", time=0.1, status="passed"
                        ),
                        JUnitTestCase(
                            name="test_fail",
                            classname="t",
                            time=0.1,
                            status="failed",
                            failure_message="assertion failed",
                        ),
                    ],
                )
            ],
            total_tests=2,
            total_failures=1,
        )

        failures = get_failures(report)

        assert len(failures) == 1
        assert failures[0].name == "test_fail"
        assert failures[0].failure_message == "assertion failed"


class TestJUnitReport:
    """Tests for JUnitReport dataclass"""

    def test_success_property_true(self):
        """success should be True when no failures or errors"""
        report = JUnitReport(
            total_tests=5, total_passed=5, total_failures=0, total_errors=0
        )
        assert report.success is True

    def test_success_property_false_with_failures(self):
        """success should be False when there are failures"""
        report = JUnitReport(
            total_tests=5, total_passed=4, total_failures=1, total_errors=0
        )
        assert report.success is False

    def test_success_property_false_with_errors(self):
        """success should be False when there are errors"""
        report = JUnitReport(
            total_tests=5, total_passed=4, total_failures=0, total_errors=1
        )
        assert report.success is False
