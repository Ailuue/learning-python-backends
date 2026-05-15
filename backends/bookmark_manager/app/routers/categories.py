import logging

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.dependencies import CurrentUserDep, SessionDep
from app.models import Category
from app.schemas.category import CategoryCreate, CategoryPublic, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate, user: CurrentUserDep, session: SessionDep
) -> Category:
    existing = session.exec(
        select(Category).where(
            (Category.name == category_in.name) & (Category.user_id == user.id)
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with that name already exists",
        )
    category = Category(
        name=category_in.name,
        description=category_in.description,
        user_id=user.id,
    )
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.get("/", response_model=list[CategoryPublic])
def list_categories(user: CurrentUserDep, session: SessionDep) -> list[Category]:
    return list(
        session.exec(
            select(Category).where(Category.user_id == user.id).order_by(Category.name)
        ).all()
    )


@router.get("/{category_id}", response_model=CategoryPublic)
def read_category(
    category_id: int, user: CurrentUserDep, session: SessionDep
) -> Category:
    category = session.get(Category, category_id)
    if not category or category.user_id != user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.patch("/{category_id}", response_model=CategoryPublic)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    user: CurrentUserDep,
    session: SessionDep,
) -> Category:
    category = session.get(Category, category_id)
    if not category or category.user_id != user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    update_data = category_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int, user: CurrentUserDep, session: SessionDep
) -> None:
    category = session.get(Category, category_id)
    if not category or category.user_id != user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    session.delete(category)
    session.commit()
    logger.info("User %s deleted category %s", user.username, category_id)
