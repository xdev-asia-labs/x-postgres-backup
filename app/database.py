from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
engine = create_engine(
    settings.DATABASE_URL,
    **(
        {}
        if _is_sqlite
        else {"pool_size": 5, "max_overflow": 10, "pool_pre_ping": True}
    ),
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models import BackupRecord, JobHistory, JobSchedule  # noqa: F401

    Base.metadata.create_all(bind=engine)
