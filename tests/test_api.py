import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app


@pytest.fixture(autouse=True)
def clean_db():
    """Reset database before each test"""
    from app.database import init_db, DATABASE
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    init_db()  # Initialize the database
    yield
    if os.path.exists(DATABASE):
        os.remove(DATABASE)

@pytest.fixture
def client():
    return TestClient(app)

class TestAccountCreation:
    def test_create_account_success(self, client):
        response = client.post("/accounts", json={"name": "John Doe", "initial_balance": 100.0})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["balance"] == 100.0
        assert "id" in data

    def test_create_account_zero_balance(self, client):
        response = client.post("/accounts", json={"name": "Jane Doe"})
        assert response.status_code == 201
        assert response.json()["balance"] == 0.0

class TestGetAccount:
    def test_get_account_success(self, client):
        create_res = client.post("/accounts", json={"name": "Test User", "initial_balance": 50.0})
        account_id = create_res.json()["id"]
        
        response = client.get(f"/accounts/{account_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test User"
        assert response.json()["balance"] == 50.0

    def test_get_account_not_found(self, client):
        response = client.get("/accounts/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Account not found"

class TestDeposit:
    def test_deposit_success(self, client):
        create_res = client.post("/accounts", json={"name": "Depositor", "initial_balance": 100.0})
        account_id = create_res.json()["id"]
        
        response = client.post(f"/accounts/{account_id}/deposit", json={"amount": 50.0})
        assert response.status_code == 200
        assert response.json()["balance"] == 150.0

    def test_deposit_invalid_amount(self, client):
        create_res = client.post("/accounts", json={"name": "Test", "initial_balance": 100.0})
        account_id = create_res.json()["id"]
        
        response = client.post(f"/accounts/{account_id}/deposit", json={"amount": -10.0})
        assert response.status_code == 400
        assert response.json()["detail"] == "Amount must be positive"

    def test_deposit_account_not_found(self, client):
        response = client.post("/accounts/9999/deposit", json={"amount": 50.0})
        assert response.status_code == 404

class TestWithdraw:
    def test_withdraw_success(self, client):
        create_res = client.post("/accounts", json={"name": "Withdrawer", "initial_balance": 100.0})
        account_id = create_res.json()["id"]
        
        response = client.post(f"/accounts/{account_id}/withdraw", json={"amount": 30.0})
        assert response.status_code == 200
        assert response.json()["balance"] == 70.0

    def test_withdraw_insufficient_funds(self, client):
        create_res = client.post("/accounts", json={"name": "Broke", "initial_balance": 20.0})
        account_id = create_res.json()["id"]
        
        response = client.post(f"/accounts/{account_id}/withdraw", json={"amount": 50.0})
        assert response.status_code == 400
        assert response.json()["detail"] == "Insufficient funds"

    def test_withdraw_invalid_amount(self, client):
        create_res = client.post("/accounts", json={"name": "Test", "initial_balance": 100.0})
        account_id = create_res.json()["id"]
        
        response = client.post(f"/accounts/{account_id}/withdraw", json={"amount": 0})
        assert response.status_code == 400

class TestTransfer:
    def test_transfer_success(self, client):
        acc1 = client.post("/accounts", json={"name": "Sender", "initial_balance": 100.0}).json()
        acc2 = client.post("/accounts", json={"name": "Receiver", "initial_balance": 50.0}).json()
        
        response = client.post("/transfers", json={
            "from_account_id": acc1["id"],
            "to_account_id": acc2["id"],
            "amount": 30.0
        })
        assert response.status_code == 200
        assert response.json()["message"] == "Transfer successful"
        
        assert client.get(f"/accounts/{acc1['id']}").json()["balance"] == 70.0
        assert client.get(f"/accounts/{acc2['id']}").json()["balance"] == 80.0

    def test_transfer_insufficient_funds(self, client):
        acc1 = client.post("/accounts", json={"name": "Sender", "initial_balance": 10.0}).json()
        acc2 = client.post("/accounts", json={"name": "Receiver", "initial_balance": 50.0}).json()
        
        response = client.post("/transfers", json={
            "from_account_id": acc1["id"],
            "to_account_id": acc2["id"],
            "amount": 100.0
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "Insufficient funds"

    def test_transfer_account_not_found(self, client):
        acc1 = client.post("/accounts", json={"name": "Sender", "initial_balance": 100.0}).json()
        
        response = client.post("/transfers", json={
            "from_account_id": acc1["id"],
            "to_account_id": 9999,
            "amount": 30.0
        })
        assert response.status_code == 404

class TestTransactions:
    def test_get_transactions(self, client):
      acc = client.post("/accounts", json={"name": "Active User", "initial_balance": 100.0}).json()
      client.post(f"/accounts/{acc['id']}/deposit", json={"amount": 50.0})
      client.post(f"/accounts/{acc['id']}/withdraw", json={"amount": 20.0})

      response = client.get(f"/accounts/{acc['id']}/transactions")
      assert response.status_code == 200
      transactions = response.json()
      assert len(transactions) == 2
      types = [t["type"] for t in transactions]
      assert "deposit" in types
      assert "withdraw" in types