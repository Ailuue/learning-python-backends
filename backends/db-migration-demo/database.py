from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLite — stored in a local file
SQLITE_URL = "sqlite:///./library.db"

engine = create_engine(SQLITE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def get_session():
    return SessionLocal()
