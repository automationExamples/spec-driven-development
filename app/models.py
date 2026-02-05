from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AccountCreate(BaseModel):
    name: str
    initial_balance: float = 0.0

class Account(BaseModel):
    id: int
    name: str
    balance: float

class DepositWithdraw(BaseModel):
    amount: float

class Transfer(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float

class Transaction(BaseModel):
    id: int
    account_id: int
    type: str
    amount: float
    timestamp: str