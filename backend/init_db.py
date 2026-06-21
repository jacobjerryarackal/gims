import os
from sqlalchemy import create_engine
from models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:15432/gims")

# psycopg2 for sync operations (init_db.py runs sync)
engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(engine)
print("Database tables created successfully!")