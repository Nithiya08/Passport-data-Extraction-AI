"""FastAPI application entrypoint for Passport AI Extractor."""

import time
import logging
from typing import List, Dict
from collections import defaultdict
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.schemas import ExtractionResult, HealthResponse, ErrorResponse
from app.services.file_service import validate_and_process_uploads
from app.services.gemini_service import extract_passport_data, get_gemini_client
from app.services.cache_service import document_cache

# Configure safe logging without sensitive data or keys
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("passport_extractor")

app = FastAPI(
    title="Passport AI Extractor API",
    version="1.0.0",
    description="High-precision passport biodata, TD3 MRZ verification, and chronological travel timeline extraction using Google Gemini."
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# In-memory sliding window rate limiter implemented as pure ASGI middleware
# (avoids BaseHTTPMiddleware ASGI deadlock bugs in test transports)
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 30
request_history: Dict[str, List[float]] = defaultdict(list)


class RateLimitMiddleware:
    """Pure ASGI rate limiting middleware."""
    def __init__(self, app_instance):
        self.app = app_instance

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in ("/api/health", "/docs", "/openapi.json", "/redoc"):
            await self.app(scope, receive, send)
            return

        client_info = scope.get("client")
        client_ip = client_info[0] if client_info else "unknown"
        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW_SECONDS

        # Clean old timestamps
        timestamps = [t for t in request_history[client_ip] if t > window_start]
        timestamps.append(now)
        request_history[client_ip] = timestamps

        if len(timestamps) > RATE_LIMIT_MAX_REQUESTS:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "Rate limit exceeded. Please wait a minute before making another request."}
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


app.add_middleware(RateLimitMiddleware)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Clean JSON response for HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Clean JSON response for unexpected internal server errors."""
    logger.error(f"Unexpected error processing request: {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An unexpected error occurred during document processing.", "detail": str(exc)}
    )


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """Return service status, Gemini API configuration state, and in-memory cache stats."""
    client = get_gemini_client()
    return HealthResponse(
        status="ok",
        gemini_model=settings.GEMINI_MODEL,
        gemini_configured=client is not None,
        version="1.0.0",
        cache_stats=document_cache.stats()
    )


@app.post(
    "/api/extract",
    response_model=ExtractionResult,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file upload or unreadable format"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Extraction or processing failure"}
    }
)
def extract_passport(
    files: List[UploadFile] = File(...),
    force_refresh: bool = False
):
    """Extract passport personal details, validate MRZ, and reconstruct travel timeline.

    - Accepts passport files (JPG, PNG, WEBP, PDF) without arbitrary page limits
    - Validates file content in memory (never written to disk)
    - Checks in-memory cache using SHA-256 document content hash for instant duplicate responses
    - Returns structured PersonalDetails, chronological TravelEvents, MRZ verification, and warnings
    """
    logger.info(f"Received extraction request with {len(files)} uploaded file(s) (force_refresh={force_refresh}).")

    # 1. Validate files and convert to image buffers in memory
    image_buffers = validate_and_process_uploads(files)
    logger.info(f"Processed {len(image_buffers)} document page(s) in memory.")

    # 2. Check in-memory document cache (keyed by cryptographic hash of document pages)
    doc_hash = document_cache.compute_hash(image_buffers)
    if not force_refresh:
        cached_result = document_cache.get(doc_hash)
        if cached_result:
            logger.info(f"Cache HIT for document hash {doc_hash[:12]}... Returning instant cached response.")
            return cached_result
        logger.info(f"Cache MISS for document hash {doc_hash[:12]}... Calling Gemini extraction pipeline.")
    else:
        logger.info(f"force_refresh=True specified. Bypassing cache for document hash {doc_hash[:12]}...")

    # 3. Run extraction pipeline
    result = extract_passport_data(image_buffers)
    logger.info(f"Extraction complete: {len(result.travel_events)} travel events identified.")

    # 4. Save to in-memory cache
    document_cache.set(doc_hash, result)

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
