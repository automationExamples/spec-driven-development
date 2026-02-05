# Banking Transaction System

A full-stack banking application built for the spec-driven-development assessment.

## Features
- Create bank accounts with initial balance
- Deposit and withdraw funds
- Transfer between accounts
- View transaction history
- Input validation and error handling

## Tech Stack
- **Backend:** FastAPI (Python)
- **Database:** SQLite
- **Frontend:** HTML/CSS/JavaScript
- **Testing:** pytest, Playwright

## Setup

```bash
# Clone and navigate
git clone https://github.com/Farhod75/spec-driven-development.git
cd spec-driven-development

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run the Application
uvicorn app.main:app --reload --port 8000
Open http://localhost:8000

# Run Tests
# API tests
pytest tests/test_api.py -v

# UI tests (server must be running)
pytest tests/test_ui.py -v

# All tests
pytest -v

API Endpoints
Method	Endpoint	Description
POST	/accounts	Create account
GET	/accounts/{id}	Get account details
POST	/accounts/{id}/deposit	Deposit funds
POST	/accounts/{id}/withdraw	Withdraw funds
POST	/transfers	Transfer between accounts
GET	/accounts/{id}/transactions	Get transaction history

# AI Tools Used

Claude (Anthropic) - Code generation and debugging

# Author
Farhod Elbekov