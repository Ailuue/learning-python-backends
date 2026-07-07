# Learning Backend Engineering with Python

A public, open learning resource for backend engineering with Python — from CS
fundamentals through FastAPI, databases, auth, messaging, and AI/LLM integration,
up to full capstone projects. Every module is concept-focused, self-contained, and
runnable. Anyone is welcome to clone it, work through it at their own pace, and learn.

## Structure

| Folder | What's in it |
|---|---|
| [backends/](backends/) | FastAPI projects and concept-focused learning modules |
| [d-structs-algos/](d-structs-algos/) | Data structures, sorting, searching, P vs NP, and 11 interview-pattern families (heap, sliding window, two pointers, DP, backtracking, grid BFS/DFS, intervals, binary search on the answer, monotonic stack, union-find, trie) |
| [frontends/](frontends/) | React + Vite frontends that pair with backend projects |
| [utility_examples/](utility_examples/) | Standalone scripts: argparse, asyncio, ETL pipeline |
| [experiments/](experiments/) | One-off scripts and throwaway experiments |

## Suggested learning path

New here? This is the order the material is designed to be worked through. Each
step stands alone, so skip ahead if a topic is already familiar.

1. **[d-structs-algos/](d-structs-algos/)** — warm up CS fundamentals in Python (no setup). 🟢
2. **[utility_examples/](utility_examples/)** — core Python idioms: argparse, asyncio, an ETL pipeline. 🟢
3. **[backends/learning/fast-api-tutorial/](backends/learning/fast-api-tutorial/)** — your first FastAPI app. 🟢
4. **[backends/learning/testing-concepts/](backends/learning/testing-concepts/)** — pytest, mocking, async tests. 🟢
5. **[backends/learning/database-concepts/](backends/learning/database-concepts/)** — persistence with SQLAlchemy + Postgres. 🐘
6. **[backends/learning/backend-concepts/](backends/learning/backend-concepts/)** — auth, caching, rate limiting, pagination, real-time. 🟢/🔴
7. **Specialized topics, as needed** — ai (LLM APIs, RAG, agents), graphql, grpc, celery, email, aws, docker, github-actions, makefile.
8. **Capstone projects** — read and run [url-shortener](backends/url-shortener/) first, then the fuller [bookmark_manager](backends/bookmark_manager/). 🐘🔴

### What each module needs to run

| Icon | Meaning |
|---|---|
| 🟢 | No infrastructure — pure Python, SQLite, or in-memory |
| 🐘 | PostgreSQL (the `database-concepts` folder ships a one-command shared Docker setup) |
| 🔴 | Redis |
| 🐳 | Docker / Docker Compose |
| ☁️ | An external or cloud service (a paid LLM API, AWS via LocalStack, GitHub OAuth, an SMTP server) |

Each module's README states exactly what it needs and how to start it.

## Backends

### Projects
- [bookmark_manager](backends/bookmark_manager/) — full FastAPI app with auth, Redis, Celery, Alembic, and rate limiting
- [url-shortener](backends/url-shortener/) — URL shortener with auth, caching, and click tracking

### Learning modules (`backends/learning/`)
- [fast-api-tutorial](backends/learning/fast-api-tutorial/) — FastAPI basics through advanced patterns
- [database-concepts](backends/learning/database-concepts/) — SQLAlchemy, migrations, indexes, transactions, full-text search, pgvector
- [backend-concepts](backends/learning/backend-concepts/) — auth, caching, rate limiting, pagination, webhooks, WebSockets, Kafka, OAuth2
- [ai-concepts](backends/learning/ai-concepts/) — LLM APIs, prompt engineering, structured outputs, tool use, embeddings, RAG, evaluation, guardrails; Claude & OpenAI side by side (paid APIs)
- [testing-concepts](backends/learning/testing-concepts/) — pytest, mocking, database testing, async testing
- [docker-concepts](backends/learning/docker-concepts/) — multi-stage builds, Compose, debugging, reverse proxy, security, CI/CD
- [aws-concepts](backends/learning/aws-concepts/) — S3, Lambda, SQS, SNS, DynamoDB
- [graphql-concepts](backends/learning/graphql-concepts/) — Strawberry schemas, dataloaders, mutations, pagination
- [grpc-concepts](backends/learning/grpc-concepts/) — gRPC with Protocol Buffers
- [celery-concepts](backends/learning/celery-concepts/) — task queues with Celery + Redis
- [email-concepts](backends/learning/email-concepts/) — SMTP, IMAP, templating, testing email
- [github-actions](backends/learning/github-actions/) — CI/CD workflows
- [makefile-concepts](backends/learning/makefile-concepts/) — Makefile patterns for backend projects

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # root-level deps: FastAPI, pytest, the tutorials
```

### Dependencies are per-folder, by design

There is **no single requirements file for the whole repo**. The root
`requirements.txt` covers the FastAPI tutorial and the lightweight concept demos.
Each capstone project and many learning modules pin their own heavier dependency
sets (Celery, Redis, SQLAlchemy drivers, Strawberry, boto3, …) in a local
`requirements.txt`.

So when you enter a project or module that has its own `requirements.txt`,
install it — otherwise you'll hit `ModuleNotFoundError`:

```bash
cd backends/bookmark_manager
pip install -r requirements.txt        # into the same venv is fine
python -m pytest                        # 46 tests, in-memory SQLite, no infra
```

Each folder's README states what it needs. Modules that require a service
(PostgreSQL, Redis, Kafka, …) ship a `docker-compose.yml` or point at a shared one.