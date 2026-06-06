"""
Database layer — SQLAlchemy engine, Product model, helpers.

Product is the entity we cache throughout all five scripts.
It represents something expensive to load from DB but cheap to serve from cache:
a product catalogue that's read thousands of times per minute but updated rarely.
"""

import os
from contextlib import contextmanager
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy import Numeric, String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"])


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id:    Mapped[int]     = mapped_column(primary_key=True)
    name:  Mapped[str]     = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock: Mapped[int]     = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"Product(id={self.id}, name={self.name!r}, price={self.price}, stock={self.stock})"


# ---------------------------------------------------------------------------
# Session context manager
# ---------------------------------------------------------------------------

@contextmanager
def get_session():
    with Session(engine) as session:
        yield session


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

def reset_schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def seed(session: Session) -> list[Product]:
    """Insert a small catalogue and return the Product objects."""
    products = [
        Product(name="Wireless Keyboard", price=Decimal("79.99"), stock=42),
        Product(name="USB-C Hub",         price=Decimal("49.99"), stock=130),
        Product(name="Monitor Stand",     price=Decimal("34.99"), stock=17),
    ]
    session.add_all(products)
    session.commit()
    for p in products:
        session.refresh(p)
    return products


# ---------------------------------------------------------------------------
# Print helper
# ---------------------------------------------------------------------------

def print_products(session: Session, label: str = "DB state"):
    rows = session.query(Product).order_by(Product.id).all()
    print(f"\n  [{label}]")
    for p in rows:
        print(f"    {p}")
