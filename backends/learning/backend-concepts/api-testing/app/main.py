from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Post, User
from .schemas import PostCreate, PostResponse, PostUpdate

app = FastAPI(title="Posts API — testing demo")

# ---------------------------------------------------------------------------
# Auth
# NOTE: X-User-Id is intentionally simplified for this teaching module.
# A real app would use JWT. The auth dependency pattern being tested here
# (injected via Depends, overridable in tests) is identical regardless of
# the auth mechanism.
# ---------------------------------------------------------------------------

def get_current_user(
    x_user_id: int = Header(..., alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, x_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user.")
    return user


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/posts", response_model=list[PostResponse])
def list_posts(
    author_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Return all published posts. Optionally filter by author."""
    q = select(Post).where(Post.published.is_(True))
    if author_id is not None:
        q = q.where(Post.user_id == author_id)
    return db.scalars(q.order_by(Post.created_at.desc(), Post.id.desc())).all()


@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    return post


@app.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    body: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = Post(user_id=current_user.id, title=body.title, body=body.body)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@app.patch("/posts/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    body: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your post.")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(post, field, value)
    db.commit()
    db.refresh(post)
    return post


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your post.")
    db.delete(post)
    db.commit()
