from .models import Base
from .connection import engine

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Tables created successfully")