# Backend Learning

Concept-focused modules — each in its own folder with runnable code and explanatory notes.

## Modules

Roughly ordered from foundational to specialized. The **Needs** column shows what
has to be running before the code works — see each module's README for specifics.

| Folder | Topics | Needs |
|---|---|---|
| [fast-api-tutorial/](fast-api-tutorial/) | FastAPI basics through advanced patterns | 🟢 |
| [testing-concepts/](testing-concepts/) | pytest, mocking, database testing, async testing | 🟢 |
| [database-concepts/](database-concepts/) | SQLAlchemy, Alembic migrations, indexes, transactions, full-text search, pgvector | 🐘 |
| [backend-concepts/](backend-concepts/) | Auth, caching, rate limiting, pagination, webhooks, WebSockets, Kafka, OAuth2, observability | varies — 🟢/🐘/🔴/🐳 per sub-module |
| [graphql-concepts/](graphql-concepts/) | Strawberry schemas, relationships, dataloaders, mutations, pagination | 🟢 |
| [grpc-concepts/](grpc-concepts/) | gRPC services with Protocol Buffers | 🟢 |
| [celery-concepts/](celery-concepts/) | Task queues and workers with Celery + Redis | 🔴🐳 |
| [email-concepts/](email-concepts/) | SMTP, IMAP, templating, and email testing | 🐳 (mail server) |
| [docker-concepts/](docker-concepts/) | Compose, multi-stage builds, debugging, reverse proxy, security, CI/CD | 🐳 |
| [aws-concepts/](aws-concepts/) | S3, Lambda, SQS, SNS, DynamoDB | ☁️🐳 (LocalStack) |
| [github-actions/](github-actions/) | CI/CD workflows | 🟢 (notes + workflows) |
| [makefile-concepts/](makefile-concepts/) | Makefile patterns for backend projects | 🟢 |

**Legend:** 🟢 no infra · 🐘 PostgreSQL · 🔴 Redis · 🐳 Docker · ☁️ external/cloud service
