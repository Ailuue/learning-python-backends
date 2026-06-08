"""
Async data access layer.

Uses async SQLAlchemy sessions — every database operation is awaited.
The interface mirrors the sync repository in 03_database_testing/ so the
two can be compared directly.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from async_models import Post, User


async def create_user(db: AsyncSession, username: str, email: str) -> User:
    user = User(username=username, email=email)
    db.add(user)
    await db.flush()
    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.id))
    return list(result.scalars().all())


async def create_post(
    db: AsyncSession,
    user: User,
    title: str,
    body: str,
    published: bool = False,
) -> Post:
    post = Post(user_id=user.id, title=title, body=body, published=published)
    db.add(post)
    await db.flush()
    return post


async def get_published_posts(db: AsyncSession) -> list[Post]:
    result = await db.execute(
        select(Post).where(Post.published.is_(True)).order_by(Post.id)
    )
    return list(result.scalars().all())


async def get_posts_by_user(db: AsyncSession, user: User) -> list[Post]:
    result = await db.execute(
        select(Post).where(Post.user_id == user.id).order_by(Post.id)
    )
    return list(result.scalars().all())
