# models/user.py
from sqlalchemy import Boolean, Column, String
from pydantic import BaseModel
from database import Base

# SQLAlchemy Model for database
class UserInDB(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    disabled = Column(Boolean, default=False)

# Pydantic Models for API
class UserBase(BaseModel):
    username: str
    full_name: str = ""
    email: str = ""
    disabled: bool = False

class UserCreate(UserBase):
    password: str

class User(UserBase):
    class Config:
        from_attributes = True  # Updated from orm_mode=True for Pydantic v2

class UserUpdate(BaseModel):
    full_name: str = None
    email: str = None
    password: str = None
    
    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    username: str
    full_name: str = ""
    email: str = ""
    
    class Config:
        from_attributes = True