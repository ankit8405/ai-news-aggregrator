from .models import Base
from .connection import engine


def create_tables() -> None:
    """Create any missing database tables (idempotent)."""
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    create_tables()
    print("Tables created successfully")
