from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from nascopilot.database import get_conn
from nascopilot.dependencies import get_current_user, require_admin, require_superadmin
from nascopilot.services.auth import hash_password, verify_password, create_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str
    password: str


class RegisterEMTBody(BaseModel):
    username: str
    password: str
    full_name: str | None = None


class RegisterAdminBody(BaseModel):
    hospital_name: str
    username: str
    password: str
    full_name: str | None = None


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login")
async def login(body: LoginBody):
    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, hashed_pw, role, hospital_id, full_name FROM users WHERE username = $1",
            body.username,
        )
    if not row or not verify_password(body.password, row["hashed_pw"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_token(
        str(row["id"]),
        row["role"],
        str(row["hospital_id"]) if row["hospital_id"] else None,
    )
    return {
        "access_token": token,
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
    }


# ── Register EMT (admin creates for their hospital) ───────────────────────────

@router.post("/register/emt", status_code=201)
async def register_emt(body: RegisterEMTBody, admin: dict = Depends(require_admin)):
    hashed = hash_password(body.password)
    async with get_conn() as conn:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO users (username, hashed_pw, role, hospital_id, full_name)
                VALUES ($1, $2, 'emt', $3, $4)
                RETURNING id, username, role, hospital_id, full_name
                """,
                body.username, hashed, admin["hospital_id"], body.full_name,
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Username already taken")
    return {
        "id": str(row["id"]),
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
        "hospital_id": str(row["hospital_id"]) if row["hospital_id"] else None,
    }


# ── Register Admin + Hospital (superadmin only) ───────────────────────────────

@router.post("/register/admin", status_code=201)
async def register_admin(body: RegisterAdminBody, _: dict = Depends(require_superadmin)):
    hashed = hash_password(body.password)
    async with get_conn() as conn:
        try:
            hospital = await conn.fetchrow(
                "INSERT INTO hospitals (name) VALUES ($1) RETURNING id, name",
                body.hospital_name,
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Hospital name already exists")
        try:
            user = await conn.fetchrow(
                """
                INSERT INTO users (username, hashed_pw, role, hospital_id, full_name)
                VALUES ($1, $2, 'admin', $3, $4)
                RETURNING id, username, role, hospital_id, full_name
                """,
                body.username, hashed, hospital["id"], body.full_name,
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Username already taken")
    return {
        "hospital": {"id": str(hospital["id"]), "name": hospital["name"]},
        "admin": {
            "id": str(user["id"]),
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
        },
    }


# ── List users for admin's hospital ──────────────────────────────────────────

@router.get("/users")
async def list_hospital_users(admin: dict = Depends(require_admin)):
    async with get_conn() as conn:
        if admin["role"] == "superadmin":
            rows = await conn.fetch(
                "SELECT id, username, full_name, role, hospital_id, created_at FROM users ORDER BY created_at DESC"
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, username, full_name, role, hospital_id, created_at
                FROM users WHERE hospital_id = $1 ORDER BY created_at DESC
                """,
                admin["hospital_id"],
            )
    return [
        {
            "id": str(r["id"]),
            "username": r["username"],
            "full_name": r["full_name"],
            "role": r["role"],
            "hospital_id": str(r["hospital_id"]) if r["hospital_id"] else None,
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


# ── List hospitals (superadmin only) ─────────────────────────────────────────

@router.get("/hospitals")
async def list_hospitals(_: dict = Depends(require_superadmin)):
    async with get_conn() as conn:
        hospitals = await conn.fetch("SELECT id, name, created_at FROM hospitals ORDER BY created_at DESC")
        result = []
        for h in hospitals:
            admins = await conn.fetch(
                "SELECT id, username, full_name FROM users WHERE hospital_id = $1 AND role = 'admin'",
                h["id"],
            )
            result.append({
                "id": str(h["id"]),
                "name": h["name"],
                "created_at": h["created_at"].isoformat(),
                "admins": [
                    {"id": str(a["id"]), "username": a["username"], "full_name": a["full_name"]}
                    for a in admins
                ],
            })
    return result


# ── Current user info ─────────────────────────────────────────────────────────

@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    async with get_conn() as conn:
        row = await conn.fetchrow(
            """
            SELECT u.id, u.username, u.full_name, u.role, u.hospital_id, h.name AS hospital_name
            FROM users u
            LEFT JOIN hospitals h ON h.id = u.hospital_id
            WHERE u.id = $1
            """,
            user["user_id"],
        )
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(row["id"]),
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
        "hospital_id": str(row["hospital_id"]) if row["hospital_id"] else None,
        "hospital_name": row["hospital_name"],
    }
