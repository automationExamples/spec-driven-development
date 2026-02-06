"""
Run Tests Page - Execute tests and view results.
"""

import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.runner import run_tests
from app.storage.db import get_database
from app.config import config
import json

st.set_page_config(page_title="Run Tests", page_icon="▶️", layout="wide")

st.title("▶️ Run Tests")

# Get database and generations
db = get_database(config.DATABASE_PATH)
generations = db.list_generations()

if not generations:
    st.warning("No test generations found. Please generate tests first.")
    st.page_link("pages/2_⚙️_Generate_Tests.py", label="Go to Generate Tests", icon="⚙️")
    st.stop()

# Generation selection
st.subheader("Select Test Generation")

gen_options = {}
for g in generations:
    spec = db.get_spec(g.spec_id)
    spec_name = spec.name if spec else "Unknown"
    gen_options[
        f"{spec_name} - {g.id[:8]}... ({g.created_at.strftime('%Y-%m-%d %H:%M')})"
    ] = g.id

default_index = 0
if "current_generation_id" in st.session_state:
    for i, (name, gid) in enumerate(gen_options.items()):
        if gid == st.session_state["current_generation_id"]:
            default_index = i
            break

selected_name = st.selectbox(
    "Choose a test generation:", options=list(gen_options.keys()), index=default_index
)
selected_gen_id = gen_options[selected_name]

# Get generation details
generation = db.get_generation(selected_gen_id)
if generation:
    st.write(f"**Test Directory:** `{generation.test_dir}`")
    st.write(f"**Files:** {len(generation.files)}")

# Run configuration
st.divider()
st.subheader("Run Configuration")

target_url = st.text_input(
    "Target Base URL",
    value=config.DEFAULT_TARGET_URL,
    help="The base URL of the API to test against",
)

# Run button
st.divider()
if st.button("▶️ Run Tests", type="primary"):
    with st.spinner("Running tests..."):
        try:
            # Create run record
            run = db.create_run(generation_id=selected_gen_id, target_url=target_url)

            # Execute tests
            test_dir = Path(generation.test_dir)
            result = run_tests(
                test_dir=test_dir, base_url=target_url, timeout=config.TEST_TIMEOUT
            )

            # Update run with results
            status_str = "completed" if result.success else "failed"
            db.update_run(
                run_id=run.id,
                status=status_str,
                passed=result.passed,
                failed=result.failed,
                skipped=result.skipped,
                errors=result.errors,
                total=result.total,
                duration=result.duration,
                junit_xml_path=str(result.junit_xml_path)
                if result.junit_xml_path
                else None,
                results_json=json.dumps(result.to_dict()),
            )

            st.session_state["last_run_id"] = run.id

            # Show results
            if result.success:
                st.success("✅ All tests passed!")
            else:
                st.error("❌ Some tests failed")

            # Results summary
            st.subheader("Results Summary")

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Passed", result.passed, delta_color="normal")
            with col2:
                st.metric(
                    "Failed",
                    result.failed,
                    delta_color="inverse" if result.failed > 0 else "off",
                )
            with col3:
                st.metric("Skipped", result.skipped)
            with col4:
                st.metric(
                    "Errors",
                    result.errors,
                    delta_color="inverse" if result.errors > 0 else "off",
                )
            with col5:
                st.metric("Duration", f"{result.duration:.2f}s")

            # Show failures
            if result.failures:
                st.subheader("Failures")
                for failure in result.failures:
                    with st.expander(f"❌ {failure.name}", expanded=True):
                        st.write(f"**Class:** {failure.classname}")
                        if failure.message:
                            st.error(failure.message)
                        if failure.traceback:
                            st.code(failure.traceback, language="python")

            # Show stdout/stderr
            with st.expander("📋 Test Output"):
                tab1, tab2 = st.tabs(["stdout", "stderr"])
                with tab1:
                    st.code(result.stdout or "No output", language="text")
                with tab2:
                    st.code(result.stderr or "No errors", language="text")

            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                if result.junit_xml_path and result.junit_xml_path.exists():
                    junit_content = result.junit_xml_path.read_text()
                    st.download_button(
                        "📥 Download JUnit XML",
                        data=junit_content,
                        file_name="junit.xml",
                        mime="application/xml",
                    )
            with col2:
                st.download_button(
                    "📥 Download Results JSON",
                    data=json.dumps(result.to_dict(), indent=2),
                    file_name="results.json",
                    mime="application/json",
                )

        except Exception as e:
            st.error(f"Failed to run tests: {e}")
            import traceback

            st.code(traceback.format_exc())

# Show previous runs
st.divider()
st.subheader("Previous Runs")

runs = db.list_runs(generation_id=selected_gen_id)
if runs:
    for run in runs:
        status_icon = "✅" if run.status == "completed" and run.failed == 0 else "❌"
        with st.expander(f"{status_icon} Run {run.id[:8]}... ({run.status})"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Passed", run.passed)
            with col2:
                st.metric("Failed", run.failed)
            with col3:
                st.metric("Duration", f"{run.duration:.2f}s")
            with col4:
                st.write(f"**Created:** {run.created_at}")

            if run.results_json:
                try:
                    results = json.loads(run.results_json)
                    failures = results.get("failures", [])
                    if failures:
                        st.subheader("Failures")
                        for f in failures:
                            st.error(
                                f"**{f['name']}**: {f.get('message', 'No message')}"
                            )
                except json.JSONDecodeError:
                    pass
else:
    st.info("No previous runs for this generation.")
