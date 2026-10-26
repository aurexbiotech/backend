import uuid
from sqlalchemy import Boolean, Column, DateTime, String, func
from database import Base


class User(Base):
    """SQLAlchemy model representing the users table."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(150), nullable=False, default="")
    email = Column(String(191), unique=True, index=True, nullable=False)
    phone_number = Column(String(30), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="patient")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role} active={self.is_active}>"
