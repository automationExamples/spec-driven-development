# Feature Spec: Streamlit UI

## Goal
Provide web interface for the test generator workflow.

## Scope
- In: Upload spec, generate tests, run tests, view results
- Out: User auth, team features, history browsing

## Requirements
- Page 1: Upload/paste OpenAPI spec, preview endpoints
- Page 2: Select spec, generate tests, view generated code
- Page 3: Run tests, display pass/fail summary, show failures

## Acceptance Criteria
- [ ] Home page with navigation to all features
- [ ] Upload page accepts YAML/JSON text or file upload
- [ ] Upload page shows parsed endpoints in table
- [ ] Upload page has "Load Example" button
- [ ] Generate page lists saved specs in dropdown
- [ ] Generate page shows generated test files with syntax highlighting
- [ ] Run page has input for target base URL
- [ ] Run page shows pass/fail/skipped counts with colors
- [ ] Run page shows expandable failure details
- [ ] Download buttons for generated tests and JUnit XML
