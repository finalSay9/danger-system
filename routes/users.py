from fastapi import Depends, APIRouter,HTTPException, Request, status, FastAPI
from sqlalchemy.orm import Session
import model
from database import get_db
import schema
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.exc import IntegrityError
import logging
from . import auth


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter




router = APIRouter(
    prefix='/users',
    tags=['users']
)

@router.post('/register', status_code=status.HTTP_201_CREATED,response_model=schema.UserResponse)
@limiter.limit('5/minute')
def create_user(
    user:schema.UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    
   ):
    #check if email exist and email
    logger.info(f"Attempting to register user with email: {user.email}")
    existing_user = db.query(model.User).filter(
    (model.User.email == user.email) | (model.User.username == user.username)).first()
    if existing_user:
      if existing_user.email == user.email.lower():
        logger.warning(f"Registration failed: Email {user.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    if existing_user is not None and existing_user.username == user.username:
        logger.warning(f"Registration failed: Username {user.username} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    hashed_pwd =auth.hash_password(user.password)
    db_user = model.User(
        username=user.username,
        email=user.email.lower(),
        first_name=user.first_name,
        last_name=user.last_name,
        gender=user.gender,
        password_hash=hashed_pwd
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User registered successfully: {user.email}")
        return db_user
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database error during user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user due to database constraint"
        )
        