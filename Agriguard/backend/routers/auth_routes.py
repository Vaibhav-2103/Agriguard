from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from backend.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Registers a new user (farmer or expert) and returns an access token."""
    existing_user = db.query(User).filter(User.email == user_data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    hashed_pw = hash_password(user_data.password)
    user = User(
        name=user_data.name.strip(),
        email=user_data.email.lower().strip(),
        password_hash=hashed_pw,
        role=user_data.role,
        preferred_language=user_data.preferred_language
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "role": user.role, "name": user.name})
    return TokenResponse(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticates a user and returns a JWT access token."""
    user = db.query(User).filter(User.email == login_data.email.lower().strip()).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": str(user.id), "role": user.role, "name": user.name})
    return TokenResponse(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)
