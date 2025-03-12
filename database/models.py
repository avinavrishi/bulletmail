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
    tokens = relationship('Token', back_populates='user')
    integrations = relationship('Integration', back_populates='user')
    subscription = relationship('Subscription', uselist=False, back_populates='user')  # One-to-one relationship
    documents = relationship('Document', back_populates='user')

class Token(Base):
    __tablename__ = 'tokens'

    token_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    token_type = Column(String, nullable=False)  # e.g., 'access' or 'refresh'
    token = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship('User', back_populates='tokens')

class Integration(Base):
    __tablename__ = 'integrations'

    integration_id = Column(Integer, primary_key=True, autoincrement=True)
    integration_key = Column(String, nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    account_id = Column(Integer, nullable=False)
    private_key_file = Column(Text, nullable=False)
    email = Column(String, nullable=False)
    status = Column(Enum('active', 'inactive', 'pending', 'failed', name='integration_status'), default='pending')

    # Relationships
    user = relationship('User', back_populates='integrations')

class Plan(Base):
    __tablename__ = 'plans'

    plan_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Enum('free', '1_month', '6_month', '12_month', name='plan_names'), unique=True, nullable=False)
    duration_days = Column(Integer, nullable=False)  # e.g., 0 for free, 30 for 1 month, etc.
    price = Column(Integer, nullable=False)  # Price in the smallest currency unit (e.g., cents)

    # Relationships
    subscriptions = relationship('Subscription', back_populates='plan')

class Subscription(Base):
    __tablename__ = 'subscriptions'

    subscription_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, unique=True)
    plan_id = Column(Integer, ForeignKey('plans.plan_id'), nullable=False)
    start_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(Enum('active', 'expired', 'cancelled', name='subscription_status'), default='active')

    # Relationships
    user = relationship('User', back_populates='subscription')
    plan = relationship('Plan', back_populates='subscriptions')

class Document(BaseTable):
    __tablename__ = 'documents'

    document_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Store file path in storage
    file_type = Column(String, nullable=False)  # e.g., 'pdf', 'docx', 'png'

    # Relationships
    user = relationship('User', back_populates='documents')