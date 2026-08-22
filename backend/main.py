import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Core imports
from core.config import ROOT_DIR, ACTIVE_MODEL_NAME
from core.db import init_db, purge_old_records_db
from core.security import check_rate_limit_ai

# Router imports
from routers import chat, cases, bookings, fir, bns, docs, tools

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("needhi")

# Initialize FastAPI App
app = FastAPI(title="Needhi AI Backend", version="1.0.0")

# CORS Middleware
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Startup Lifespan events
@app.on_event("startup")
def startup_event():
    # Guarantee DB exists and is migrated
    init_db()
    # Purge expired PII/bookings/subscriptions older than 90 days
    purge_old_records_db(days=90)
    logger.info("Needhi AI Backend startup sequence complete.")

# Register sub-routers
app.include_router(chat.router)
app.include_router(cases.router)
app.include_router(bookings.router)
app.include_router(fir.router)
app.include_router(bns.router)
app.include_router(docs.router)
app.include_router(tools.router)

# Serve React static files in production if dist exists
dist_path = os.path.join(ROOT_DIR, "frontend", "dist")
if os.path.exists(dist_path):
    # Mount assets (js, css, images) directly so they serve correctly
    assets_path = os.path.join(dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# SPA HTML5 History API Catch-All Fallback Route
@app.get("/{catchall:path}")
def spa_catch_all(catchall: str):
    # API requests that failed to match a route should return API 404
    if catchall.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
        
    index_file = os.path.join(dist_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
        
    raise HTTPException(status_code=404, detail="Frontend build assets not found.")
