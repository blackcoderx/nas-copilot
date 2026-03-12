from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nascopilot.config import settings
from nascopilot.database import init_pool, close_pool, get_conn
from nascopilot.routers.auth import router as auth_router
from nascopilot.routers.cases import router as cases_router
from nascopilot.routers.outcomes import router as outcomes_router
from nascopilot.routers.facilities import router as facilities_router
from nascopilot.routers.analytics import router as analytics_router
from nascopilot.services.auth import hash_password


async def _seed_superadmin() -> None:
    """Create superadmin account on first boot if env vars are set and no superadmin exists."""
    if not settings.superadmin_username or not settings.superadmin_password:
        return
    async with get_conn() as conn:
        exists = await conn.fetchval("SELECT 1 FROM users WHERE role = 'superadmin' LIMIT 1")
        if exists:
            return
        hashed = hash_password(settings.superadmin_password)
        await conn.execute(
            "INSERT INTO users (username, hashed_pw, role) VALUES ($1, $2, 'superadmin')",
            settings.superadmin_username, hashed,
        )
        print(f"[startup] Superadmin '{settings.superadmin_username}' created.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    await _seed_superadmin()
    yield
    await close_pool()


app = FastAPI(title="NAS Copilot GH", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(cases_router)
app.include_router(outcomes_router)
app.include_router(facilities_router)
app.include_router(analytics_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
