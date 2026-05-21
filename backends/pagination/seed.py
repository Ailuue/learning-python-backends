import random
from datetime import datetime, timedelta

from database import engine
from models import Article, Base, Comment

Base.metadata.create_all(engine)

from sqlalchemy.orm import sessionmaker
session = sessionmaker(bind=engine)()

TITLES = [
    "Understanding Async Programming in Python",
    "A Beginner's Guide to SQL Indexes",
    "How Vector Databases Work",
    "REST vs GraphQL: When to Use Each",
    "Pagination Patterns for APIs",
    "Intro to Database Normalization",
    "How to Use PostgreSQL Window Functions",
    "Building a Rate Limiter from Scratch",
    "Caching Strategies for Web APIs",
    "JWT vs Session Tokens Explained",
    "Getting Started with Docker",
    "A Practical Guide to Git Rebasing",
    "Understanding the Event Loop",
    "Type Safety in Python with mypy",
    "When to Denormalize Your Database",
    "Writing Testable Code in FastAPI",
    "How Indexes Actually Speed Up Queries",
    "Intro to Message Queues with Redis",
    "Designing a Good REST API",
    "Why Connection Pools Matter",
    "How to Debug Slow SQL Queries",
    "Background Tasks in FastAPI",
    "Choosing the Right Database for Your App",
    "Python Dataclasses vs Pydantic",
    "An Introduction to HNSW Indexes",
    "Understanding HTTP Caching Headers",
    "Soft Delete Patterns in SQL",
    "How to Store Passwords Safely",
    "The N+1 Query Problem Explained",
    "ACID Transactions in Plain English",
    "Intro to Full-Text Search",
    "Cursor vs Offset Pagination",
    "Database Migrations Without Downtime",
    "Building a CLI Tool with Typer",
    "Understanding OAuth 2.0 Flows",
    "How to Write a Good README",
    "Python Logging Best Practices",
    "Load Testing Your API with Locust",
    "Dependency Injection in FastAPI",
    "Why You Should Use Database Constraints",
    "An Intro to Time-Series Databases",
    "How Bloom Filters Work",
    "Optimistic vs Pessimistic Locking",
    "Building a Webhook System",
    "Structured Logging in Python",
    "Foreign Keys and Referential Integrity",
    "Writing SQL Migrations You Can Roll Back",
    "What Is a Materialized View?",
    "How to Profile a Python Application",
    "Rate Limiting with Token Buckets",
]

AUTHORS = ["alice", "bob", "carol", "dave", "eve"]

COMMENT_BODIES = [
    "Great write-up, learned a lot!",
    "Could you go deeper on the tradeoffs?",
    "This helped me fix a bug I've had for weeks.",
    "I'd love a follow-up post on this.",
    "Small correction: in the third example the query should use LEFT JOIN.",
    "Bookmarked. Coming back to this one.",
    "The diagram really clarified things.",
    "Any recommendations for further reading?",
    "Ran into this exact issue yesterday.",
    "The cursor pagination section was eye-opening.",
]

now = datetime.utcnow()

articles = []
for i, title in enumerate(TITLES):
    published_at = now - timedelta(days=len(TITLES) - i, hours=random.randint(0, 23))
    articles.append(Article(
        title=title,
        body=f"This is the full body of the article titled '{title}'. " * 3,
        author=random.choice(AUTHORS),
        published_at=published_at,
        view_count=random.randint(10, 5000),
    ))

session.add_all(articles)
session.flush()

comments = []
for article in articles:
    for body in random.sample(COMMENT_BODIES, k=random.randint(1, 4)):
        comments.append(Comment(
            article_id=article.id,
            author=random.choice(AUTHORS),
            body=body,
        ))

session.add_all(comments)
session.commit()
session.close()

print(f"Seeded {len(articles)} articles and {len(comments)} comments.")
