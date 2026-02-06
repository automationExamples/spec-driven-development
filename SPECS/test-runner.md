# Feature Spec: Test Runner

## Goal
Execute generated pytest tests and parse results.

## Scope
- In: pytest execution, JUnit XML parsing, result summary
- Out: Parallel execution, distributed testing

## Requirements
- Run pytest programmatically with JUnit XML output
- Capture stdout/stderr
- Parse JUnit XML for pass/fail counts
- Extract failure details (test name, message, traceback)

## Acceptance Criteria
- [ ] run_tests() executes pytest on given directory
- [ ] Returns RunResult with exit_code, passed, failed, skipped
- [ ] JUnit XML file is generated
- [ ] parse_junit_xml() extracts test counts
- [ ] Failure details include test name and traceback
- [ ] Duration captured in seconds
