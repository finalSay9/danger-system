from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, APIRouter, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
from .utils.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    SECRET_KEY, ALGORITHM
)

import model
from database import get_db
import schema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure rate limiting
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)


# Configuration
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Retrieve the current authenticated user from a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        scopes: list = payload.get("scopes", [])
        if email is None:
            raise credentials_exception
        token_data = schema.TokenData(email=email, scopes=scopes)
    except JWTError:
        raise credentials_exception
    user = db.query(model.User).filter(model.User.email == token_data.email).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user



@router.post(
    '/token',
    response_model=schema.Token,
    summary="User login",
    description="Authenticate a user and return an access token and refresh token."
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    
):
    """Authenticate a user and issue a JWT access token."""
    logger.info(f"Login attempt for email: {form_data.username}")
    user = db.query(model.User).filter(model.User.email == form_data.username.lower()).first()
    if not user or not user.is_active or not verify_password(form_data.password, user.password_hash):
        logger.warning(f"Failed login attempt for email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email, password, or account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)  # optional: reload the updated user

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=7)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email},
        expires_delta=refresh_token_expires
    )
    logger.info(f"Successful login for email: {user.email}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds()),
        "refresh_token": refresh_token
    }

@router.post(
    '/refresh',
    response_model=schema.Token,
    summary="Refresh access token",
    description="Generate a new access token using a valid refresh token."
)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    refresh_token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    
):
    """Refresh an access token using a refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        user = db.query(model.User).filter(model.User.email == email).first()
        if user is None or not user.is_active:
            raise credentials_exception
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "scopes": [user.role.value]},
            expires_delta=access_token_expires
        )
        logger.info(f"Access token refreshed for email: {user.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds()),
            "refresh_token": refresh_token
        }
    except JWTError:
        logger.warning(f"Failed refresh token attempt")
        raise credentials_exception