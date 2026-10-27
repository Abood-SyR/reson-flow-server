from fastapi import FastAPI
from app.core.database import Base, engine
from app.routers import auth, orders, inventory, departments, financial_ledgers
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Reson Flow API",
    description="B2B SaaS management system for sweets bakeries in Syria",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(orders.router)
app.include_router(inventory.router)
app.include_router(financial_ledgers.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Reson Flow API - Backend is running successfully!"}