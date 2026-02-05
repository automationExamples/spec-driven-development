from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.models import AccountCreate, Account, DepositWithdraw, Transfer, Transaction
from app.database import init_db, get_db

app = FastAPI(title="Banking API")

@app.on_event("startup")
def startup():
    init_db()

@app.post("/accounts", response_model=Account, status_code=201)
def create_account(data: AccountCreate):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO accounts (name, balance) VALUES (?, ?)",
            (data.name, data.initial_balance)
        )
        account_id = cursor.lastrowid
        return {"id": account_id, "name": data.name, "balance": data.initial_balance}

@app.get("/accounts/{account_id}", response_model=Account)
def get_account(account_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        return dict(row)

@app.post("/accounts/{account_id}/deposit", response_model=Account)
def deposit(account_id: int, data: DepositWithdraw):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    with get_db() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        new_balance = row["balance"] + data.amount
        conn.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, account_id))
        conn.execute(
            "INSERT INTO transactions (account_id, type, amount) VALUES (?, ?, ?)",
            (account_id, "deposit", data.amount)
        )
        return {"id": account_id, "name": row["name"], "balance": new_balance}

@app.post("/accounts/{account_id}/withdraw", response_model=Account)
def withdraw(account_id: int, data: DepositWithdraw):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    with get_db() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        if row["balance"] < data.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")
        new_balance = row["balance"] - data.amount
        conn.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, account_id))
        conn.execute(
            "INSERT INTO transactions (account_id, type, amount) VALUES (?, ?, ?)",
            (account_id, "withdraw", data.amount)
        )
        return {"id": account_id, "name": row["name"], "balance": new_balance}

@app.post("/transfers", response_model=dict)
def transfer(data: Transfer):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    with get_db() as conn:
        from_acc = conn.execute("SELECT * FROM accounts WHERE id = ?", (data.from_account_id,)).fetchone()
        to_acc = conn.execute("SELECT * FROM accounts WHERE id = ?", (data.to_account_id,)).fetchone()
        if not from_acc:
            raise HTTPException(status_code=404, detail="Source account not found")
        if not to_acc:
            raise HTTPException(status_code=404, detail="Destination account not found")
        if from_acc["balance"] < data.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")
        
        conn.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (data.amount, data.from_account_id))
        conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (data.amount, data.to_account_id))
        conn.execute(
            "INSERT INTO transactions (account_id, type, amount) VALUES (?, ?, ?)",
            (data.from_account_id, "transfer_out", data.amount)
        )
        conn.execute(
            "INSERT INTO transactions (account_id, type, amount) VALUES (?, ?, ?)",
            (data.to_account_id, "transfer_in", data.amount)
        )
        return {"message": "Transfer successful"}

@app.get("/accounts/{account_id}/transactions", response_model=list[Transaction])
def get_transactions(account_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        rows = conn.execute(
            "SELECT * FROM transactions WHERE account_id = ? ORDER BY timestamp DESC",
            (account_id,)
        ).fetchall()
        return [dict(r) for r in rows]

# Serve frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")