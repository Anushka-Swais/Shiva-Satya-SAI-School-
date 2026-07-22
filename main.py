import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 1. LOAD ENVIRONMENT VARIABLES FIRST
# This ensures your API keys and DB passwords are ready before anything else loads!
load_dotenv() 

# 2. Import your database config (optional at this stage, but good to initialize)
from config.database import engine, Base

# 3. Import all your dashboard routes
from routes import admin_route, faculty_route, hm_route, parent_route, student_route

# 4. Create database tables (if they don't exist yet)
Base.metadata.create_all(bind=engine)

# 5. Initialize the FastAPI application
app = FastAPI(
    title="SSS@school API",
    description="Backend API for all SSS School Dashboards",
    version="1.0.0"
)

# 6. Setup CORS (Allows your frontend to talk to this backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, change this to your frontend domain!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 7. Register all your Dashboard Routes
app.include_router(admin_route.router, prefix="/api/admin", tags=["Admin Dashboard"])
app.include_router(faculty_route.router, prefix="/api/faculty", tags=["Faculty Dashboard"])
app.include_router(hm_route.router, prefix="/api/hm", tags=["Headmaster Dashboard"])
app.include_router(parent_route.router, prefix="/api/parent", tags=["Parent Dashboard"])
app.include_router(student_route.router, prefix="/api/student", tags=["Student Dashboard"])

# 8. Root Health Check Endpoint
@app.get("/")
async def root():
    return {"status": "running", "message": "SSS Backend is live!"}