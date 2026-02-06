# Feature Spec: Credit Risk Review Queue Ranking

Fulfilled via OpenAI Codex

## Goal
- Provide a full-stack app to manage and reprioritize credit application reviews by ranked order.

## Scope
- In:
  - Full ranking view of all applications with rank, applicant name, and summary.
  - Insert a new application at the start, end, or between two applications.
  - Remove an application from the queue.
  - Change an application's rank.
  - Persist data in SQLite.
- Out:
  - Authentication, authorization, or multi-user roles.
  - External credit bureau integrations.
  - Complex scoring models beyond manual ranking.

## Requirements
- Backend built with Python + FastAPI.
- Database using SQLite.
- REST endpoints to list, insert (start/end/between), move, and delete applications.
- Frontend that loads the full ranking and supports the above actions.
- Tests that cover key workflows and edge cases for ranking changes.

## Acceptance Criteria
- [ ] Viewing the main page shows the full ranking with each item's rank, applicant name, and summary.
- [ ] A user can insert a new application at the start of the list.
- [ ] A user can insert a new application at the end of the list.
- [ ] A user can insert a new application between two existing applications.
- [ ] A user can remove an application from the queue.
- [ ] A user can change the rank of an application and the list reflects the new order.
- [ ] Data persists in SQLite across server restarts.
- [ ] Tests validate list ordering, insertions, deletions, and rank changes.