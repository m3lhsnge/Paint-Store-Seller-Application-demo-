from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.db.session import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başladığında tüm tabloları oluşturur (eğer yoksa)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Boya Reçete Sistemi",
    description="Özel boya karışımı reçeteleri, maliyet hesaplama ve şube yönetimi API'si",
    version="1.0.0",
    lifespan=lifespan,
)

# Origin listesi env'den gelir (CORS_ORIGINS, virgülle ayrılmış; "*" sadece lokal geliştirme için).
# Kimlik doğrulama Authorization header'ı ile yapıldığından cookie credentials gerekmez.
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
