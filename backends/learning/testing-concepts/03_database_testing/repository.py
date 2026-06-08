"""
Data access layer — the code under test.

Keeping queries in repository functions (rather than inline in routes)
makes them easy to unit-test: just pass in a Session and assert on the result.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Post, User


# ---------------------------------------------------------------------------
# UserRepository
# ---------------------------------------------------------------------------

def create_user(db: Session, username: str, email: str) -> User:
    user = User(username=username, email=email)
    db.add(user)
    db.flush()   # assigns .id without committing — visible within the transaction
    return user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == email)).first()


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)).all())


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.flush()


# ---------------------------------------------------------------------------
# PostRepository
# ---------------------------------------------------------------------------

def create_post(
    db: Session,
    user: User,
    title: str,
    body: str,
    published: bool = False,
) -> Post:
    post = Post(user_id=user.id, title=title, body=body, published=published)
    db.add(post)
    db.flush()
    return post


def get_published_posts(db: Session) -> list[Post]:
    return list(
        db.scalars(
            select(Post).where(Post.published.is_(True)).order_by(Post.id)
        ).all()
    )


def get_posts_by_user(db: Session, user: User) -> list[Post]:
    return list(
        db.scalars(select(Post).where(Post.user_id == user.id).order_by(Post.id)).all()
    )
