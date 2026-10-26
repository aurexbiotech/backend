import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from auth import (
    create_session_token,
    decode_session_token,
    generate_csrf_token,
    hash_password,
    normalize_role,
    roles_match,
    verify_password,
)
from config import settings
from database import Base, engine, get_db
from models import User
from schemas import (
    LoginRequest,
    LoginSuccessResponse,
    MessageResponse,
    RegisterRequest,
    UserResponse,
)

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aurex_hms")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to ensure database tables are created on startup."""
    try:
        # Create tables defined in models if they don't already exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as exc:
        logger.error(f"Failed to initialize database tables: {exc}")
    yield


app = FastAPI(
    title="AUREX Hospital Management System API",
    description="Backend API for AUREX HMS authentication and hospital management operations.",
    version="1.0.0",
    lifespan=lifespan,
)

# -----------------------------------------------------------------------------
# CORS Middleware Configuration
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Global Safe Error Handlers
# -----------------------------------------------------------------------------
@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Catch database errors to prevent leaking raw SQL queries or sensitive details."""
    logger.error(f"Database error during request {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database service is temporarily unavailable. Please try again later."},
    )


# -----------------------------------------------------------------------------
# Current User Dependency
# -----------------------------------------------------------------------------
def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    hms_session: Optional[str] = Cookie(default=None),
    authorization: Optional[str] = Header(default=None),
) -> User:
    """Extracts and verifies the authenticated user from the session cookie or Bearer header."""
    # 1. Try session cookie first
    token = hms_session

    # 2. Fall back to Authorization Bearer header (supports Swagger UI and Postman)
    if not token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
        )

    # 3. Decode & verify token
    payload = decode_session_token(token)
    if not payload or "user_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid. Please log in again.",
        )

    # 4. Fetch user from DB
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this session no longer exists.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact your hospital administrator.",
        )

    return user


# -----------------------------------------------------------------------------
# Health Check Endpoints
# -----------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to verify backend server and database availability."""
    db_status = "disconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        logger.warning(f"Health check database ping failed: {exc}")

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "Aurex HMS Backend",
        "database": db_status,
    }


@app.get("/health/database", tags=["Health"])
def health_database_check(db: Session = Depends(get_db)):
    """Dedicated database health check endpoint."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable",
        )


# -----------------------------------------------------------------------------
# Authentication Endpoints
# -----------------------------------------------------------------------------
@app.post(
    "/api/v1/auth/login",
    response_model=LoginSuccessResponse,
    tags=["Authentication"],
    summary="Authenticate user and start session",
)
def login(request_data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Authenticates a user by email/login ID, password, and selected role.

    - Validates email and password existence.
    - Matches user in MySQL database.
    - Verifies Argon2 password hash.
    - Validates selected role against the user's role in the database.
    - Verifies that account is active.
    - Sets secure HttpOnly session cookie and CSRF cookie.
    """
    identifier = request_data.identifier
    password = request_data.password
    selected_role = request_data.selected_role

    # 1. Basic validation
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email address or login ID is required.",
        )

    if not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password is required.",
        )

    # 2. Lookup user by email / login ID
    user = db.query(User).filter(User.email == identifier).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # 3. Verify password hash
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # 4. Verify account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact the hospital administrator.",
        )

    # 5. Verify role if specified
    if selected_role and not roles_match(selected_role, user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Selected role '{selected_role}' does not match your assigned account role.",
        )

    # 6. Issue Session and CSRF Tokens
    token = create_session_token(user_id=user.id, role=user.role)
    csrf_token = generate_csrf_token()

    # 7. Set Cookies for the browser (HttpOnly session + client-readable CSRF)
    max_age_seconds = settings.SESSION_TTL_HOURS * 3600

    response.set_cookie(
        key="hms_session",
        value=token,
        max_age=max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )

    response.set_cookie(
        key="hms_csrf",
        value=csrf_token,
        max_age=max_age_seconds,
        httponly=False,  # Accessible to frontend JS for CSRF header inclusion
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )

    return LoginSuccessResponse(
        id=user.id,
        full_name=user.full_name or "Aurex User",
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        token=token,
        csrf_token=csrf_token,
        message="Login successful",
    )


@app.get(
    "/api/v1/auth/me",
    response_model=UserResponse,
    tags=["Authentication"],
    summary="Get currently logged in user info",
)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile information."""
    return current_user


@app.post(
    "/api/v1/auth/logout",
    response_model=MessageResponse,
    tags=["Authentication"],
    summary="Log out and clear session cookies",
)
def logout(response: Response):
    """Logs the user out by deleting session and CSRF cookies."""
    response.delete_cookie(key="hms_session", path="/")
    response.delete_cookie(key="hms_csrf", path="/")
    return MessageResponse(message="Logged out successfully")


@app.post(
    "/api/v1/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
    summary="Register a new patient account",
)
def register(request_data: RegisterRequest, db: Session = Depends(get_db)):
    """Registers a new account.

    Public self-registration is limited to the 'patient' category.
    Staff roles (doctor, nurse, laboratory, etc.) must be provisioned by administrators.
    """
    category = normalize_role(request_data.category or request_data.role or "patient")

    if category != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public self-registration is only allowed for patients. Staff accounts must be provisioned by an administrator.",
        )

    # Check if email is already in use
    existing_user = db.query(User).filter(User.email == request_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Hash the password with Argon2
    hashed = hash_password(request_data.password)

    new_user = User(
        full_name=request_data.full_name.strip(),
        email=request_data.email.strip().lower(),
        phone_number=request_data.phone_number.strip() if request_data.phone_number else None,
        password_hash=hashed,
        role="patient",
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
