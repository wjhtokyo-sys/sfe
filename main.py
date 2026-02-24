from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.models import entities  # noqa: F401
from app.api.sfe_api import router as sfe_router

app = FastAPI(title="SFE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
app.include_router(sfe_router)


@app.get("/")
def root():
    return {"status": "ok", "system": "SFE backend running"}
