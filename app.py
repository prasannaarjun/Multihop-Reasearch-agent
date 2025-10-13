"""
Multi-hop Research Agent API - Modular Version
Now registering modular routers only.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from auth import auth_router

from api.dependencies import lifespan
from api.routes.core import router as core_router
from api.routes.research import router as research_router
from api.routes.models import router as models_router
from api.routes.chat import router as chat_router
from api.routes.conversations import router as conversations_router


app = FastAPI(
    title="Multi-hop Research Agent",
    description="A research agent that uses Postgres + pgvector for document retrieval and multi-hop reasoning",
    version="1.0.0",
    lifespan=lifespan,
)

# Note: For development, restrict origins and allow credentials for cookie-based auth
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(core_router)
app.include_router(research_router)
app.include_router(models_router)
app.include_router(chat_router)
app.include_router(conversations_router)

if os.path.exists("frontend/build"):
    app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
