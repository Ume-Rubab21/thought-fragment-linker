import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.production import allowed_origins, production_guard_middleware
from routers import auth, brain_dumps, collections, dashboard, file_imports, knowledge_graph, model_calls, notes, suggestions, tags


app = FastAPI(
    title="Thought Fragment Linker API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Embedding-Status"],
)

app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(tags.router)
app.include_router(collections.router)
app.include_router(dashboard.router)
app.include_router(brain_dumps.router)
app.include_router(file_imports.router)
app.include_router(model_calls.router)
app.include_router(suggestions.router)
app.include_router(knowledge_graph.router)


app.middleware("http")(production_guard_middleware)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, error: Exception):
    if os.getenv("APP_ENV", "development").lower() != "production":
        raise error
    request_id = request.headers.get("X-Request-ID", "unknown")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected server error occurred.",
            "request_id": request_id,
        },
    )


@app.get("/health")
def health():
    return {"status": "ok", "environment": os.getenv("APP_ENV", "development")}


@app.get("/health/ready")
def readiness():
    return {"status": "ready"}