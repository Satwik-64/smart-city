# app/services/auth_service.py
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.models import User, UserType
from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Settings (from .env via settings)
SECRET_KEY = settings.effective_jwt_secret
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_expire_minutes

class AuthService:
    """Authentication helpers for user and authority accounts."""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Return True when ``plain_password`` matches ``hashed_password``."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate a password hash using the configured context."""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a signed JWT for the provided payload."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Decode and validate a JWT, returning the payload on success."""
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            return None

    @staticmethod
    def authenticate_user(db: Session, identifier: str, password: str) -> Optional[User]:
        """Authenticate a citizen or authority stored in the ``users`` table."""
        user = (
            db.query(User)
            .filter((User.phone_number == identifier) | (User.email == identifier))
            .first()
        )
        if not user:
            return None

        password_hash = getattr(user, "password_hash", None)
        if not isinstance(password_hash, str):
            return None

        if not AuthService.verify_password(password, password_hash):
            return None

        if not bool(getattr(user, "is_active", False)):
            return None

        setattr(user, "last_login", datetime.utcnow())
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def register_user(
        db: Session,
        name: str,
        phone_number: str,
        password: str,
        email: Optional[str] = None,
        address: Optional[str] = None,
    ) -> User | dict:
        """Register a new citizen account."""
        if db.query(User).filter(User.phone_number == phone_number).first():
            return {"error": "Phone number already registered"}

        if email and db.query(User).filter(User.email == email).first():
            return {"error": "Email already registered"}

        hashed_password = AuthService.get_password_hash(password)
        new_user = User(
            name=name,
            phone_number=phone_number,
            email=email,
            password_hash=hashed_password,
            address=address,
            user_type=UserType.USER,
            is_active=True,
            is_approved=True,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def register_authority(
        db: Session,
        name: str,
        position: str,
        feedback_route: str,
        phone_number: str,
        email: str,
        password: str,
    ) -> User | dict:
        """Register a new authority account."""
        if db.query(User).filter(User.phone_number == phone_number).first():
            return {"error": "Phone number already registered"}

        if db.query(User).filter(User.email == email).first():
            return {"error": "Email already registered"}

        hashed_password = AuthService.get_password_hash(password)
        authority = User(
            name=name,
            position=position,
            feedback_route=feedback_route,
            phone_number=phone_number,
            email=email,
            password_hash=hashed_password,
            user_type=UserType.AUTHORITY,
            is_active=True,
            is_approved=True,
        )

        try:
            db.add(authority)
            db.commit()
        except OperationalError:
            db.rollback()
            raise

        db.refresh(authority)
        return authority


auth_service = AuthService()
