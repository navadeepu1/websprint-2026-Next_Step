from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select
from datetime import datetime, timezone

from app.models import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut
from app.services.auth import create_session, hash_password, revoke_token, user_from_token, verify_password

router = APIRouter(prefix="/auth")


def _token(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterRequest, request: Request) -> AuthResponse:
    session = request.app.state.session_factory()
    try:
        email = str(payload.email).lower()
        if session.scalar(select(User).where(User.email == email)):
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        user = User(email=email, display_name=payload.display_name.strip(), password_hash=hash_password(payload.password), created_at=datetime.now(timezone.utc).replace(tzinfo=None))
        session.add(user)
        session.flush()
        token = create_session(session, user)
        return AuthResponse(access_token=token, user=UserOut(id=user.id, email=user.email, display_name=user.display_name))
    finally:
        session.close()


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request) -> AuthResponse:
    session = request.app.state.session_factory()
    try:
        user = session.scalar(select(User).where(User.email == str(payload.email).lower()))
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        return AuthResponse(access_token=create_session(session, user), user=UserOut(id=user.id, email=user.email, display_name=user.display_name))
    finally:
        session.close()


@router.get("/me", response_model=UserOut)
def me(request: Request, authorization: str | None = Header(default=None)) -> UserOut:
    session = request.app.state.session_factory()
    try:
        user = user_from_token(session, _token(authorization))
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        return UserOut(id=user.id, email=user.email, display_name=user.display_name)
    finally:
        session.close()


@router.post("/logout")
def logout(request: Request, authorization: str | None = Header(default=None)) -> dict[str, str]:
    session = request.app.state.session_factory()
    try:
        revoke_token(session, _token(authorization))
        return {"status": "logged_out"}
    finally:
        session.close()
