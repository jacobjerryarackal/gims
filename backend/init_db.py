from sqlalchemy import create_engine
from models import Base

# Use sync connection for table creation
engine = create_engine('postgresql://postgres:postgres@localhost:5432/gims')
Base.metadata.create_all(engine)
print("Database tables created successfully!")