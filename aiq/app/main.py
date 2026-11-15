from fastapi import FastAPI
from app.api.health import router as health_router
from app.review.router import router as review_router

app = FastAPI(title="AIQ Control Center API", version="0.1.0")
app.include_router(health_router)
app.include_router(review_router)
