from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth

app = FastAPI(title="Thought Fragment Linker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/health")
def health():
    return {"status": "ok"}