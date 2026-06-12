# Learning Python

A personal repo for practicing and learning Python — backend engineering, data structures, and more.

## Structure

| Folder | What's in it |
|---|---|
| [backends/](backends/) | FastAPI projects and concept-focused learning modules |
| [d-structs-algos/](d-structs-algos/) | Data structures, sorting algorithms, searching, and P vs NP problems |
| [frontends/](frontends/) | React + Vite frontends that pair with backend projects |
| [utility_examples/](utility_examples/) | Standalone scripts: argparse, asyncio, ETL pipeline |
| [experiments/](experiments/) | One-off scripts and throwaway experiments |

## Backends

### Projects
- [bookmark_manager](backends/bookmark_manager/) — full FastAPI app with auth, Redis, Celery, Alembic, and rate limiting
- [url-shortener](backends/url-shortener/) — URL shortener with auth, caching, and click tracking

### Learning modules (`backends/learning/`)
- [fast-api-tutorial](backends/learning/fast-api-tutorial/) — FastAPI basics through advanced patterns
- [database-concepts](backends/learning/database-concepts/) — SQLAlchemy, migrations, indexes, transactions, full-text search, pgvector
- [backend-concepts](backends/learning/backend-concepts/) — auth, caching, rate limiting, pagination, webhooks, WebSockets, Kafka, OAuth2
- [testing-concepts](backends/learning/testing-concepts/) — pytest, mocking, database testing, async testing
- [docker-concepts](backends/learning/docker-concepts/) — multi-stage builds, Compose, debugging, reverse proxy, security, CI/CD
- [aws-concepts](backends/learning/aws-concepts/) — S3, Lambda, SQS, SNS, DynamoDB
- [graphql-concepts](backends/learning/graphql-concepts/) — Strawberry schemas, dataloaders, mutations, pagination
- [grpc-concepts](backends/learning/grpc-concepts/) — gRPC with Protocol Buffers
- [celery-concepts](backends/learning/celery-concepts/) — task queues with Celery + Redis
- [email-concepts](backends/learning/email-concepts/) — SMTP, IMAP, templating, testing email

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # root-level dependencies
```

Most learning modules have their own `requirements.txt` and `docker-compose.yml`. See each folder's README for setup instructions.