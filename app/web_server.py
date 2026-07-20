"""FastAPI application exposed by the web-server container."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.api.schemas import HealthResponse

app = FastAPI(
    title="Real-time Transaction Fraud Monitor API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Development web clients commonly run on these ports. Production origins can
# be tightened when the separate frontend service is introduced.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:4200",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse()
