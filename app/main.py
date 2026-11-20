from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.studio import router as studio_router
from app.core.config import settings
from app.core.security import require_user
from app.review.router import router as review_router

app = FastAPI(title="AIQ Control Center API", version="0.2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_ROOT = FRONTEND_DIR.resolve()

# Register API routes before the catch-all static-file route.
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router, dependencies=[Depends(require_user)])
app.include_router(studio_router)
app.include_router(review_router, dependencies=[Depends(require_user)])


@app.get("/")
async def serve_frontend():
    return FileResponse(FRONTEND_ROOT / "index.html")


@app.get("/{file_path:path}")
async def serve_static(file_path: str):
    requested_path = (FRONTEND_ROOT / file_path).resolve()
    try:
        requested_path.relative_to(FRONTEND_ROOT)
    except ValueError:
        return JSONResponse({"error": "not found"}, status_code=404)

    if requested_path.is_file():
        return FileResponse(requested_path)
    return JSONResponse({"error": "not found"}, status_code=404)
