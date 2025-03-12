from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, JSON, ARRAY, Enum, Table, Float
from sqlalchemy.orm import relationship
from .session import Base
from sqlalchemy.sql import func
 
class BaseTable(Base):
    __abstract__ = True

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, nullable=True)

class User(BaseTable):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    is_admin = Column(Integer, nullable=True)
    is_staff = Column(Integer, nullable=True)

    # Relationships
    tokens = relationship('Token', back_populates='user')  # Added relationship

class Token(Base):
    __tablename__ = 'tokens'

    token_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    token_type = Column(String, nullable=False)  # e.g., 'access' or 'refresh'
    token = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship('User', back_populates='tokens')  # Added back_populates