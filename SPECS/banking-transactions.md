# Feature Spec: Banking Transactions

## Goal
Build a simple banking system that allows users to create accounts, manage balances, and perform transactions.

## Scope
- In: Account creation, deposits, withdrawals, transfers, transaction history, basic UI
- Out: Authentication, multi-currency, external integrations

## Requirements
- Users can create bank accounts with initial balance
- Users can deposit money into accounts
- Users can withdraw money (with insufficient funds validation)
- Users can transfer between accounts
- Users can view transaction history
- API returns appropriate status codes and error messages

## Acceptance Criteria
- [ ] POST /accounts creates a new account and returns account details
- [ ] GET /accounts/{id} returns account with current balance
- [ ] POST /accounts/{id}/deposit increases balance
- [ ] POST /accounts/{id}/withdraw decreases balance (fails if insufficient funds)
- [ ] POST /transfers moves money between accounts
- [ ] GET /accounts/{id}/transactions returns transaction history
- [ ] UI allows all operations above
- [ ] All API endpoints have passing tests
- [ ] UI has Playwright E2E tests