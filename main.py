from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import uuid
import time
from collections import defaultdict, deque

EMAIL = "23f1002312@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://app-4lsofn.example.com",
    "https://dash-hyi8bl.example.com",
]

RATE_LIMIT = 12
WINDOW = 10  # seconds

app = FastAPI()

# -----------------------------
# Middleware 1: CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Rate limiter storage
# -----------------------------
client_requests = defaultdict(deque)

# -----------------------------
# Middleware 2: Request Context
# -----------------------------
@app.middleware("http")
async def request_context(request: Request, call_next):

    rid = request.headers.get("X-Request-ID")

    if not rid:
        rid = str(uuid.uuid4())

    request.state.request_id = rid

    response = await call_next(request)

    response.headers["X-Request-ID"] = rid

    return response


# -----------------------------
# Middleware 3: Rate Limiter
# -----------------------------
@app.middleware("http")
async def rate_limit(request: Request, call_next):

    client = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    bucket = client_requests[client]

    while bucket and now - bucket[0] > WINDOW:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

    bucket.append(now)

    return await call_next(request)


@app.get("/ping")
async def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }


@app.get("/")
async def root():
    return {"status": "running"}
