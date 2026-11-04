# Architecture Overview

The initial architecture is a modular monolith with a Next.js/TypeScript frontend, a FastAPI backend, and PostgreSQL. Business rules and validation belong in the backend. Inventory changes should be recorded as transactions to preserve an auditable stock history.
