import os, hashlib, base64, hmac, json, time
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from database import find_one, insert_one, update_one

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-production")

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _create_jwt(payload: dict) -> str:
    header = _b64url(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
    body = _b64url(json.dumps(payload, default=str).encode())
    sig = _b64url(hmac.new(SECRET_KEY.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"

def _decode_jwt(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT")
    header_body = f"{parts[0]}.{parts[1]}".encode()
    expected = _b64url(hmac.new(SECRET_KEY.encode(), header_body, hashlib.sha256).digest())
    if not hmac.compare_digest(expected, parts[2]):
        raise ValueError("Invalid signature")
    body = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
    if body.get("exp", 0) < time.time():
        raise ValueError("Token expired")
    return body

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
        "exp": time.time() + 86400 * 7,
        "iat": time.time(),
    }
    return _create_jwt(payload)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        payload = _decode_jwt(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(401, "Invalid token")
    except ValueError:
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
