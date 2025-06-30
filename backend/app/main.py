from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import auth_routes, job_routes, data_routes

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Facebook Group Scraper API",
    description="API for scraping public Facebook groups",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],  # Streamlit and React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(job_routes.router)
app.include_router(data_routes.router)

@app.get("/")
def read_root():
    return {"message": "Facebook Group Scraper API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

