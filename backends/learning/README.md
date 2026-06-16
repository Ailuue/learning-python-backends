# Backend Learning

Concept-focused modules — each in its own folder with runnable code and explanatory notes.

## Modules

Work the **core path** in order first — each step builds on the last. After that,
the **specialized topics** can be done in any order, as you need them. The **Needs**
column shows what has to be running before the code works (see each module's README).

### Core path — do these in order

| # | Folder | Topics | Needs |
|---|---|---|---|
| 1 | [fast-api-tutorial/](fast-api-tutorial/) | FastAPI basics through advanced patterns | 🟢 |
| 2 | [testing-concepts/](testing-concepts/) | pytest, mocking, database testing, async testing | 🟢 |
| 3 | [database-concepts/](database-concepts/) | SQLAlchemy, Alembic migrations, indexes, transactions, full-text search, pgvector | 🐘 |
| 4 | [backend-concepts/](backend-concepts/) | Auth, caching, rate limiting, pagination, webhooks, WebSockets, Kafka, OAuth2, observability | varies — 🟢/🐘/🔴/🐳 per sub-module |

### Specialized topics — any order, after the core path

| Folder | Topics | Needs |
|---|---|---|
| [graphql-concepts/](graphql-concepts/) | Strawberry schemas, relationships, dataloaders, mutations, pagination | 🟢 |
| [grpc-concepts/](grpc-concepts/) | gRPC services with Protocol Buffers | 🟢 |
| [celery-concepts/](celery-concepts/) | Task queues and workers with Celery + Redis | 🔴🐳 |
| [email-concepts/](email-concepts/) | SMTP, IMAP, templating, and email testing | 🐳 (mail server) |
| [docker-concepts/](docker-concepts/) | Compose, multi-stage builds, debugging, reverse proxy, security, CI/CD | 🐳 |
| [aws-concepts/](aws-concepts/) | S3, Lambda, SQS, SNS, DynamoDB | ☁️🐳 (LocalStack) |
| [github-actions/](github-actions/) | CI/CD workflows | 🟢 (notes + workflows) |
| [makefile-concepts/](makefile-concepts/) | Makefile patterns for backend projects | 🟢 |
| [ai-concepts/](ai-concepts/) | LLM APIs, prompt engineering, structured outputs, tool use, embeddings, RAG, evaluation, guardrails — Claude & GPT side by side | ☁️ (paid LLM APIs) |

**Legend:** 🟢 no infra · 🐘 PostgreSQL · 🔴 Redis · 🐳 Docker · ☁️ external/cloud service

## Conventions

- **Folder names use hyphens** (`full-text-search/`, `rate-limiting/`). The one
  exception is a folder that Python must `import` as a package — those use
  underscores, because hyphens aren't valid in import paths.
- **Step files use a zero-padded number prefix** (`01_basics.py`, `02_ranking.py`)
  so the intended reading order is obvious and they sort correctly.
- **Conceptual explanations ("the why") live in `README.md`**; code files carry
  short docstrings for "the what." There are no prose-only `.py` note files.
