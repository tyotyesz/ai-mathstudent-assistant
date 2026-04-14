from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, qa
from app.core.db import init_db

init_db()

app = FastAPI(title="AI Student Assistant Demo", version="0.1.0")

origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(qa.router)


@app.get("/health")
def health():
    return {"status": "ok"}
