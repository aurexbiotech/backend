from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for user login.

    Accepts either 'email' or 'login_id', and either 'category' or 'role'
    to remain fully compatible with both the existing frontend and standard REST clients.
    """

    category: str | None = Field(default=None, description="Role/category selected on frontend UI")
    role: str | None = Field(default=None, description="Role name (alias for category)")
    email: str | None = Field(default=None, description="User email address")
    login_id: str | None = Field(default=None, description="User login ID / email alias")
    password: str = Field(..., min_length=1, description="Account password")

    @property
    def identifier(self) -> str:
        """Returns the non-empty login identifier (email or login_id)."""
        val = (self.email or self.login_id or "").strip()
        return val

    @property
    def selected_role(self) -> str:
        """Returns the non-empty selected role (category or role)."""
        return (self.category or self.role or "").strip()


class RegisterRequest(BaseModel):
    """Schema for public user registration (defaults to patient role)."""

    category: str | None = "patient"
    role: str | None = "patient"
    full_name: str = Field(..., min_length=1, max_length=150, description="Full name")
    email: EmailStr = Field(..., description="Valid email address")
    phone_number: str | None = Field(default=None, max_length=30, description="Optional phone number")
    password: str = Field(..., min_length=8, description="Password (at least 8 characters)")


class UserResponse(BaseModel):
    """Schema for public user profile representations."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: str
    phone_number: str | None = None
    role: str
    is_active: bool
    created_at: datetime | None = None


class LoginSuccessResponse(BaseModel):
    """Schema returned upon successful authentication."""

    id: str
    full_name: str
    email: str
    role: str
    is_active: bool
    token: str
    csrf_token: str
    message: str = "Login successful"


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str
