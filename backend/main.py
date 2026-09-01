from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routers import drugs, interactions, pharmacist, identity, dispense, voice

app = FastAPI(title="PharmCheck SK", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(drugs.router)
app.include_router(interactions.router)
app.include_router(pharmacist.router)
app.include_router(identity.router)
app.include_router(dispense.router)
app.include_router(voice.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}
