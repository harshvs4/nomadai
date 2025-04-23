# create_tables.py
from database import Base, engine
from models.user import UserInDB
from utils.auth import get_password_hash

# Create all tables
def setup_database():
    """Create all database tables and optionally add initial data."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

if __name__ == "__main__":
    setup_database()