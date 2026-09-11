from typing import List

from sqlalchemy import inspect, text
from sqlalchemy.schema import CreateColumn

from .connection import engine
from .models import Base


def _add_missing_columns(bind) -> List[str]:
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())
    added: List[str] = []

    with bind.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            existing_columns = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns:
                    continue
                if not column.nullable and column.server_default is None and column.default is None:
                    print(
                        f"  ! skipping required column {table.name}.{column.name}; "
                        "add it with a migration"
                    )
                    continue
                ddl = CreateColumn(column).compile(dialect=bind.dialect)
                conn.execute(text(f"ALTER TABLE {table.name} ADD COLUMN {ddl}"))
                added.append(f"{table.name}.{column.name}")

    return added


def create_tables(bind=engine) -> None:
    Base.metadata.create_all(bind)
    added = _add_missing_columns(bind)
    if added:
        print(f"Added missing columns: {', '.join(added)}")


if __name__ == "__main__":
    create_tables()
    print("Tables created/updated successfully")
