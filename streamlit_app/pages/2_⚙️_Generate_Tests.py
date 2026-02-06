"""
Generate Tests Page - Generate pytest files from specifications.
"""

import os
import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.openapi_parser import parse_and_normalize
from app.generator import TestGenerator, get_llm_client, MockLLMClient
from app.storage.db import get_database
from app.config import config

st.set_page_config(page_title="Generate Tests", page_icon="⚙️", layout="wide")

st.title("⚙️ Generate Tests")

# Get database and specs
db = get_database(config.DATABASE_PATH)
specs = db.list_specs()

if not specs:
    st.warning("No specifications found. Please upload a spec first.")
    st.page_link("pages/1_📄_Upload_Spec.py", label="Go to Upload Spec", icon="📄")
    st.stop()

# Spec selection
st.subheader("Select Specification")

spec_options = {f"{s.name} ({s.title} v{s.version})": s.id for s in specs}
default_index = 0

# Try to select current spec from session state
if "current_spec_id" in st.session_state:
    for i, (name, sid) in enumerate(spec_options.items()):
        if sid == st.session_state["current_spec_id"]:
            default_index = i
            break

selected_name = st.selectbox(
    "Choose a specification:", options=list(spec_options.keys()), index=default_index
)
selected_spec_id = spec_options[selected_name]

# Get spec details
spec = db.get_spec(selected_spec_id)
if spec:
    normalized = parse_and_normalize(spec.raw_content)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Title", normalized.title)
    with col2:
        st.metric("Version", normalized.version)
    with col3:
        st.metric("Endpoints", len(normalized.endpoints))

# Generation options
st.divider()
st.subheader("LLM Configuration")

# Provider selection
provider_options = {
    "Mock (Deterministic - No API needed)": "mock",
    "OpenAI (GPT-4, GPT-3.5)": "openai",
    "Anthropic (Claude)": "anthropic",
}

selected_provider_name = st.selectbox(
    "Select LLM Provider:",
    options=list(provider_options.keys()),
    index=0,
    help="Mock mode generates tests deterministically without any API calls. OpenAI and Anthropic require API keys.",
)
selected_provider = provider_options[selected_provider_name]

# API Key and Model configuration (only show if not mock)
api_key = None
model = None

if selected_provider != "mock":
    st.info(
        f"**{selected_provider_name}** requires an API key. "
        "Your key is only used for this session and not stored."
    )

    col1, col2 = st.columns(2)

    with col1:
        # Check for existing env var
        env_key_name = (
            "OPENAI_API_KEY" if selected_provider == "openai" else "ANTHROPIC_API_KEY"
        )
        existing_key = os.environ.get(env_key_name) or os.environ.get("LLM_API_KEY")

        if existing_key:
            st.success(f"API key found in environment ({env_key_name})")
            use_env_key = st.checkbox("Use environment variable key", value=True)
            if use_env_key:
                api_key = existing_key
            else:
                api_key = st.text_input(
                    "Enter API Key:",
                    type="password",
                    help="Enter your API key",
                )
        else:
            api_key = st.text_input(
                f"Enter {selected_provider.title()} API Key:",
                type="password",
                help=f"Get your key from {'https://platform.openai.com/api-keys' if selected_provider == 'openai' else 'https://console.anthropic.com/settings/keys'}",
            )

    with col2:
        if selected_provider == "openai":
            model_options = [
                "gpt-4o-mini",
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-3.5-turbo",
            ]
            model = st.selectbox(
                "Select Model:",
                options=model_options,
                index=0,
                help="gpt-4o-mini is fast and cost-effective. gpt-4o is more capable.",
            )
        else:
            model_options = [
                "claude-3-haiku-20240307",
                "claude-3-sonnet-20240229",
                "claude-3-opus-20240229",
            ]
            model = st.selectbox(
                "Select Model:",
                options=model_options,
                index=0,
                help="Haiku is fast and cost-effective. Opus is most capable.",
            )

    # Validate API key
    if not api_key:
        st.warning("Please enter an API key to use this provider.")

# Mock mode info
if selected_provider == "mock":
    st.info(
        "**Mock Mode**: Generates tests deterministically based on endpoint structure. "
        "No external API calls are made. Ideal for CI/CD pipelines."
    )

# Generate button
st.divider()

can_generate = selected_provider == "mock" or (api_key and len(api_key) > 10)

if st.button("🚀 Generate Tests", type="primary", disabled=not can_generate):
    with st.spinner("Generating tests..."):
        try:
            # Get LLM client based on selection
            if selected_provider == "mock":
                llm_client = MockLLMClient()
                st.info("Using Mock LLM (deterministic)")
            else:
                llm_client = get_llm_client(
                    provider=selected_provider, api_key=api_key, model=model
                )
                st.info(f"Using {selected_provider.title()} ({model})")

            # Generate tests
            generator = TestGenerator(
                llm_client=llm_client, output_dir=config.GENERATED_TESTS_DIR
            )
            generated_files = generator.generate(normalized, selected_spec_id)

            # Save generation record
            generation = db.create_generation(
                spec_id=selected_spec_id,
                test_dir=str(config.GENERATED_TESTS_DIR / selected_spec_id),
                files=[str(f) for f in generated_files],
            )

            st.session_state["current_generation_id"] = generation.id
            st.success(f"✅ Generated {len(generated_files)} test files!")

            # Show generated files
            st.subheader("Generated Files")
            for file_path in generated_files:
                with st.expander(f"📄 {file_path.name}"):
                    content = file_path.read_text()
                    st.code(content, language="python")

            st.info("Navigate to **Run Tests** page to execute these tests.")

        except Exception as e:
            st.error(f"Failed to generate tests: {e}")
            import traceback

            st.code(traceback.format_exc())

if not can_generate and selected_provider != "mock":
    st.warning("Please enter a valid API key to generate tests with this provider.")

# Show existing generations
st.divider()
st.subheader("Previous Generations")

generations = db.list_generations(spec_id=selected_spec_id)
if generations:
    for gen in generations:
        with st.expander(f"Generation {gen.id[:8]}... ({gen.status})"):
            st.write(f"**ID:** `{gen.id}`")
            st.write(f"**Created:** {gen.created_at}")
            st.write(f"**Files:** {len(gen.files)}")

            if st.button("Select", key=f"select_gen_{gen.id}"):
                st.session_state["current_generation_id"] = gen.id
                st.success(f"Selected generation: {gen.id[:8]}...")
                st.rerun()

            # Show files
            for f in gen.files:
                file_path = Path(f)
                if file_path.exists():
                    with st.expander(f"📄 {file_path.name}"):
                        st.code(file_path.read_text(), language="python")
else:
    st.info("No generations found for this spec.")
