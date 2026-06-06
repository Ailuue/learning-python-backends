from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os

_HERE = os.path.dirname(os.path.abspath(__file__))
SQLITE_URL = f"sqlite:///{_HERE}/library.db"

engine = create_engine(SQLITE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def get_session():
    return SessionLocal()
