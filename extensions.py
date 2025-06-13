"""
Shared Flask extensions to avoid circular imports and multiple SQLAlchemy instances.
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Single shared database instance
db = SQLAlchemy(model_class=Base)