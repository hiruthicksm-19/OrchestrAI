"""
SQLAlchemy Declarative Base

This module provides the shared declarative base that all ORM models inherit from.

Future models will be created in app/database/models/ and inherit from this base:

    from app.database.base import Base
    from sqlalchemy import Column, Integer, String
    
    class User(Base):
        __tablename__ = "users"
        
        id = Column(Integer, primary_key=True)
        name = Column(String)

Design:
- Single source of truth for all models
- Table metadata is collected here
- Used by Alembic for auto-detecting models
- Supports inheritance hierarchies
- Type hints fully supported

Do NOT create models in this file.
Models belong in app/database/models/ directory.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base for all ORM models.

    All database models should inherit from this class:

        class MyModel(Base):
            __tablename__ = "my_table"
            ...

    Metadata is automatically collected on this class.
    This is used by Alembic for auto-migrations.
    """

    pass
