from fastapi import FastAPI
from app.routers import vms, networks, sdn, lab_builder, labs, auth
from fastapi.middleware.cors import CORSMiddleware
from app import models # <-- Import models
from app.database import engine # <-- Import engine
from logging.config import dictConfig # <-- Import this
from .logging_config import LogConfig #

dictConfig(LogConfig().dict())
models.Base.metadata.create_all(bind=engine) # <-- Add this line

app = FastAPI(
    title="Proxmox Cyber Range API",
    description="An API to manage Proxmox virtual machines for a cyber range.",
    version="1.0.0",
)
origins = [
    # Add the address of your frontend here
    # If you are running 'npm run dev', it is likely one of these
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def read_root():
    return {"message": "Welcome to the Proxmox API"}

# --- THIS IS THE CORRECTED LINE ---
# The prefix="/api" has been removed.
app.include_router(vms.router)
app.include_router(networks.router)
app.include_router(sdn.router)
app.include_router(lab_builder.router)
app.include_router(labs.router)
app.include_router(auth.router)

