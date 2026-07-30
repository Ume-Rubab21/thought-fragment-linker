from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, brain_dumps, collections, model_calls, notes, tags


app = FastAPI(
    title="Thought Fragment Linker API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Embedding-Status"],
)

app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(tags.router)
app.include_router(collections.router)
app.include_router(brain_dumps.router)
app.include_router(model_calls.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
    }