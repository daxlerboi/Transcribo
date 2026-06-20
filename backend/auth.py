import os, hashlib, base64
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from database import find_one, insert_one, update_one

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(days=7)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600000)
    return base64.b64encode(salt + dk).decode()

def _verify_password(password: str, stored: str) -> bool:
    raw = base64.b64decode(stored)
    salt, dk = raw[:16], raw[16:]
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600000) == dk

class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

def create_token(email: str) -> str:
    payload = {
        "sub": email,
        "exp": datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(401, "Invalid token")
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")
    user = await find_one("users", {"email": email})
    if not user:
        raise HTTPException(401, "User not found")
    if user.get("tokens_blacklisted") and token in user.get("tokens_blacklisted", []):
        raise HTTPException(401, "Token revoked")
    return user

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    try:
        if not req.email or not req.password:
            raise HTTPException(400, "Email and password required")
        if len(req.password) < 6:
            raise HTTPException(400, "Password must be at least 6 characters")
        existing = await find_one("users", {"email": req.email})
        if existing:
            raise HTTPException(409, "Email already registered")
        hashed = _hash_password(req.password)
        user = await insert_one("users", {
            "email": req.email,
            "password": hashed,
            "tokens_blacklisted": [],
        })
        token = create_token(req.email)
        return TokenResponse(access_token=token, user=UserResponse(id=user["_id"], email=user["email"]))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"{type(e).__name__}: {e}")

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    try:
        user = await find_one("users", {"email": req.email})
        if not user or not _verify_password(req.password, user["password"]):
            raise HTTPException(401, "Invalid email or password")
        token = create_token(req.email)
        return TokenResponse(access_token=token, user=UserResponse(id=user["_id"], email=user["email"]))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"{type(e).__name__}: {e}")

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = await get_current_user(credentials)
    blacklisted = user.get("tokens_blacklisted", [])
    blacklisted.append(credentials.credentials)
    await update_one("users", {"email": user["email"]}, {"tokens_blacklisted": blacklisted})
    return {"message": "Logged out"}

@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)):
    return UserResponse(id=user["_id"], email=user["email"])
