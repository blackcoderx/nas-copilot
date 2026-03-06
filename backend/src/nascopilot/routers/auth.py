from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from nascopilot.database import get_conn
from nascopilot.services.auth import hash_password, verify_password, create_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str
    password: str


class RegisterBody(BaseModel):
    username: str
    password: str


@router.post("/register", status_code=201)
async def register(body: RegisterBody):
    hashed = hash_password(body.password)
    async with get_conn() as conn:
        try:
            row = await conn.fetchrow(
                "INSERT INTO users (username, hashed_pw) VALUES ($1, $2) RETURNING id, username",
                body.username, hashed,
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Username already taken")
    return {"id": str(row["id"]), "username": row["username"]}


@router.post("/login")
async def login(body: LoginBody):
    async with get_conn() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", body.username)
    if not row or not verify_password(body.password, row["hashed_pw"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_token(str(row["id"]))
    return {"access_token": token, "username": row["username"]}
