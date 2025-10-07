from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from models import User, TokenData
from database import get_users_collection

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def authenticate_user(email: str, password: str):
    users_collection = await get_users_collection()
    user = await users_collection.find_one({"email": email})
    if not user:
        return False

    # Handle different password field names
    password_hash = user.get("password_hash") or user.get("password")
    if not password_hash:
        return False

    if not verify_password(password, password_hash):
        return False

    # Convert ObjectId to string for Pydantic
    user["id"] = str(user["_id"])
    # Remove the original _id field to avoid conflicts
    user.pop("_id", None)
    return User(**user)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, role=role)
    except JWTError:
        raise credentials_exception
    
    users_collection = await get_users_collection()
    user = await users_collection.find_one({"email": token_data.email})
    if user is None:
        raise credentials_exception
    # Convert ObjectId to string for Pydantic
    user["id"] = str(user["_id"])
    # Remove the original _id field to avoid conflicts
    user.pop("_id", None)
    return User(**user)

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.role == "pending":
        raise HTTPException(status_code=400, detail="User account is pending approval")
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user