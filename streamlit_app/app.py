"""
Streamlit App - Main entry point for the web UI.
"""

import streamlit as st

st.set_page_config(page_title="OpenAPI Test Generator", page_icon="🧪", layout="wide")

st.title("🧪 OpenAPI Test Generator")

st.markdown("""
Welcome to the OpenAPI Test Generator! This tool helps you:

1. **Upload** an OpenAPI specification
2. **Generate** pytest test files automatically
3. **Run** the tests against your API
4. **View** detailed results and failures

### Getting Started

Use the sidebar to navigate between pages:

- **📄 Upload Spec** - Upload or paste your OpenAPI specification
- **⚙️ Generate Tests** - Generate pytest files from your spec
- **▶️ Run Tests** - Execute tests and view results

### Quick Links

- [OpenAPI Specification](https://swagger.io/specification/)
- [Pytest Documentation](https://docs.pytest.org/)
""")

# Show quick stats if we have data
st.divider()
st.subheader("Current Session")

col1, col2, col3 = st.columns(3)

with col1:
    spec_id = st.session_state.get("current_spec_id")
    if spec_id:
        st.metric("Current Spec", spec_id[:8] + "...")
    else:
        st.metric("Current Spec", "None")

with col2:
    gen_id = st.session_state.get("current_generation_id")
    if gen_id:
        st.metric("Current Generation", gen_id[:8] + "...")
    else:
        st.metric("Current Generation", "None")

with col3:
    run_id = st.session_state.get("last_run_id")
    if run_id:
        st.metric("Last Run", run_id[:8] + "...")
    else:
        st.metric("Last Run", "None")
