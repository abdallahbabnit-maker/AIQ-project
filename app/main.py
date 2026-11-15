from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import os
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.studio import router as studio_router
from app.review.router import router as review_router
from app.core.security import require_user

app = FastAPI(title="AIQ Control Center API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/{file_path:path}")
async def serve_static(file_path: str):
    full_path = os.path.join(FRONTEND_DIR, file_path)
    if os.path.isfile(full_path):
        return FileResponse(full_path)
    return JSONResponse({"error": "not found"}, status_code=404)

@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return JSONResponse(content={}, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    })

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router, dependencies=[Depends(require_user)])
app.include_router(studio_router)
app.include_router(review_router, dependencies=[Depends(require_user)])
