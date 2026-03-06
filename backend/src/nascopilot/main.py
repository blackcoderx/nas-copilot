from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nascopilot.config import settings
from nascopilot.database import init_pool, close_pool
from nascopilot.routers.auth import router as auth_router
from nascopilot.routers.cases import router as cases_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
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


@app.get("/health")
async def health():
    return {"status": "ok"}
