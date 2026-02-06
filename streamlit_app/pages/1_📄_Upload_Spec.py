"""
Upload Spec Page - Upload or paste OpenAPI specifications.
"""

import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.openapi_parser import parse_and_normalize, OpenAPIParseError
from app.storage.db import get_database
from app.config import config

st.set_page_config(page_title="Upload Spec", page_icon="📄", layout="wide")

st.title("📄 Upload OpenAPI Specification")

# Load example spec
EXAMPLE_SPEC_PATH = (
    Path(__file__).parent.parent.parent / "openapi_specs" / "example_openapi.yaml"
)


def load_example_spec() -> str:
    """Load the example OpenAPI spec"""
    if EXAMPLE_SPEC_PATH.exists():
        return EXAMPLE_SPEC_PATH.read_text()
    return ""


# Input methods
st.subheader("Input Method")
input_method = st.radio(
    "Choose how to provide your OpenAPI spec:",
    ["Paste Content", "Upload File", "Load Example"],
    horizontal=True,
)

spec_content = ""
spec_name = ""

if input_method == "Paste Content":
    spec_name = st.text_input("Spec Name", placeholder="My API Spec")
    spec_content = st.text_area(
        "Paste your OpenAPI YAML or JSON here:",
        height=400,
        placeholder="openapi: '3.0.0'\ninfo:\n  title: My API\n  version: '1.0.0'\npaths: {}",
    )

elif input_method == "Upload File":
    spec_name = st.text_input("Spec Name", placeholder="My API Spec")
    uploaded_file = st.file_uploader(
        "Upload OpenAPI YAML or JSON file", type=["yaml", "yml", "json"]
    )
    if uploaded_file:
        spec_content = uploaded_file.read().decode("utf-8")
        if not spec_name:
            spec_name = uploaded_file.name.rsplit(".", 1)[0]
        st.code(
            spec_content[:500] + "..." if len(spec_content) > 500 else spec_content,
            language="yaml",
        )

elif input_method == "Load Example":
    spec_name = "Example Items API"
    spec_content = load_example_spec()
    if spec_content:
        st.info("Loaded example OpenAPI spec for the Items API")
        with st.expander("View Example Spec"):
            st.code(spec_content, language="yaml")
    else:
        st.error("Example spec file not found")

# Preview and Save
if spec_content:
    st.divider()
    st.subheader("Preview")

    try:
        normalized = parse_and_normalize(spec_content)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Title", normalized.title)
        with col2:
            st.metric("Version", normalized.version)
        with col3:
            st.metric("Endpoints", len(normalized.endpoints))

        # Show endpoints table
        st.subheader("Endpoints")
        endpoints_data = [
            {
                "Method": ep.method,
                "Path": ep.path,
                "Operation ID": ep.operation_id or "-",
                "Summary": ep.summary or "-",
            }
            for ep in normalized.endpoints
        ]
        st.dataframe(endpoints_data, use_container_width=True)

        # Save button
        st.divider()
        if st.button("💾 Save Specification", type="primary", disabled=not spec_name):
            if not spec_name:
                st.error("Please provide a name for the specification")
            else:
                try:
                    db = get_database(config.DATABASE_PATH)
                    spec = db.create_spec(
                        name=spec_name,
                        raw_content=spec_content,
                        title=normalized.title,
                        version=normalized.version,
                        endpoint_count=len(normalized.endpoints),
                    )
                    st.session_state["current_spec_id"] = spec.id
                    st.success(f"✅ Saved! Spec ID: `{spec.id}`")
                    st.info(
                        "Navigate to **Generate Tests** page to create tests for this spec."
                    )
                except Exception as e:
                    st.error(f"Failed to save: {e}")

    except OpenAPIParseError as e:
        st.error(f"Invalid OpenAPI specification: {e}")

# Show existing specs
st.divider()
st.subheader("Existing Specifications")

db = get_database(config.DATABASE_PATH)
specs = db.list_specs()

if specs:
    for spec in specs:
        with st.expander(f"📄 {spec.name} ({spec.title} v{spec.version})"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**ID:** `{spec.id}`")
                st.write(f"**Endpoints:** {spec.endpoint_count}")
                st.write(f"**Created:** {spec.created_at}")
            with col2:
                if st.button("Select", key=f"select_{spec.id}"):
                    st.session_state["current_spec_id"] = spec.id
                    st.success(f"Selected spec: {spec.name}")
                    st.rerun()
else:
    st.info("No specifications saved yet. Upload one above!")
