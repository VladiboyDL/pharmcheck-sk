from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .security import allowed_origins
from .routers import drugs, interactions, identity, dispense, voice

app = FastAPI(title="PharmCheck SK", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    # Not "*": this API is unauthenticated and serves health data, so any page on the
    # internet could otherwise read it from a visitor's browser.
    allow_origins=allowed_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(drugs.router)
app.include_router(interactions.router)
app.include_router(identity.router)
app.include_router(dispense.router)
app.include_router(voice.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}
