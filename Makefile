.PHONY: dev ui example test e2e lint install clean

# Install dependencies
install:
	pip install -r requirements.txt

# Run the FastAPI backend
dev:
	uvicorn app.main:app --reload --port 8000

# Run the Streamlit UI
ui:
	streamlit run streamlit_app/app.py --server.port 8501

# Run the example target API
example:
	uvicorn example_api.main:app --reload --port 8001

# Run all tests
test:
	pytest tests/ -v --junitxml=test-results/junit.xml

# Run only unit tests
test-unit:
	pytest tests/unit/ -v

# Run only integration tests
test-integration:
	pytest tests/integration/ -v

# Run E2E tests (requires example API to be running or will start it)
e2e:
	pytest tests/e2e/ -v

# Run linting
lint:
	ruff check .
	ruff format --check .

# Format code
format:
	ruff format .

# Clean generated files
clean:
	rm -rf generated_tests/
	rm -rf data/
	rm -rf test-results/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Build Docker images
docker-build:
	docker-compose build

# Run with Docker
docker-up:
	docker-compose up

# Stop Docker containers
docker-down:
	docker-compose down
