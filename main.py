from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.database import Base, engine
from app.models import entities  # noqa: F401
from app.api.sfe_api import router as sfe_router
from app.api.auth_api import router as auth_router
from seed import run as seed_run

app = FastAPI(title="SFE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
with engine.begin() as conn:
    cols_user = [r[1] for r in conn.execute(text("PRAGMA table_info(users)")).fetchall()]
    if 'is_active' not in cols_user:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
    cols_customer = [r[1] for r in conn.execute(text("PRAGMA table_info(customers)")).fetchall()]
    if 'is_active' not in cols_customer:
        conn.execute(text("ALTER TABLE customers ADD COLUMN is_active BOOLEAN DEFAULT 1"))

seed_run()
app.include_router(auth_router)
app.include_router(sfe_router)


@app.get("/")
def root():
    return {"status": "ok", "system": "SFE backend running"}
