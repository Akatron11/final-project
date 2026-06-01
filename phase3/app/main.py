from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, gyms, members, plans, subscriptions, credentials, devices, verify, access_logs, occupancy

app = FastAPI(title="GymGate API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(gyms.router, prefix="/api/v1")
app.include_router(members.router, prefix="/api/v1")
app.include_router(plans.router, prefix="/api/v1")
app.include_router(subscriptions.router, prefix="/api/v1")
app.include_router(credentials.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1")
app.include_router(verify.router, prefix="/api/v1")
app.include_router(access_logs.router, prefix="/api/v1")
app.include_router(occupancy.router, prefix="/api/v1")
