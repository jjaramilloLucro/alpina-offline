from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import configs 
from sqlalchemy.orm import Session
from api import connection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = configs.get_db_settings()


def authenticate(db: Session, username:str, password:str):
    user = connection.get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user['password']):
        return False
    
    return user

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def encode(to_encode, key, algorithm):
    return jwt.encode(to_encode, key, algorithm)

def create_access_token(data: dict):
    expires_delta = timedelta(minutes=30)
    to_encode = data.copy()
    expire = time_now() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = encode(to_encode, key=settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def time_now():
    return datetime.now()