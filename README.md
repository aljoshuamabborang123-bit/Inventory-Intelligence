# Inventory Intelligence Platform

A full-stack inventory and maintenance intelligence platform for apartment maintenance teams. It connects parts usage to work orders and unit turns to improve inventory visibility, cost tracking, and operational decision-making.

## Project status

**Early development — foundation setup**

This repository is being built incrementally. Features will be documented as they are implemented and tested.

## Planned capabilities

- Inventory catalog with stock levels and reorder thresholds
- Work order and unit-turn tracking
- Parts usage linked to maintenance activities
- Inventory transaction history and audit trail
- Cost and usage analytics dashboard
- Role-based access for maintenance teams and managers

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM and migrations | SQLAlchemy, Alembic |
| Testing | Pytest, Vitest |
| Local development | Docker Compose |

## Repository structure

```text
frontend/       Next.js web application
backend/        FastAPI application and tests
database/       Database-related assets and migrations
docs/           Architecture notes and project documentation
docker-compose.yml
```

## Getting started

Prerequisites: Git, Python 3.12+, Node.js 20+, and Docker Desktop.

The development setup instructions will be expanded as each service is implemented.

## Development principles

- Keep business rules in the backend service layer.
- Validate inputs at API boundaries.
- Track inventory changes instead of silently overwriting stock.
- Use database constraints and migrations for data integrity.
- Add automated tests for critical workflows.
- Never commit secrets, credentials, or local environment files.

## Roadmap

1. Establish the repository and application structure.
2. Design the relational data model and database migrations.
3. Implement authentication, inventory, work orders, and parts-usage APIs.
4. Build the responsive frontend dashboard and management screens.
5. Add integration tests, documentation, and deployment configuration.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
