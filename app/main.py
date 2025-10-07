from fastapi import FastAPI
from app.routers import vms, networks, sdn, lab_builder, labs, auth
from app import models # <-- Import models
from app.database import engine # <-- Import engine

models.Base.metadata.create_all(bind=engine) # <-- Add this line

app = FastAPI(
    title="Proxmox Cyber Range API",
    description="An API to manage Proxmox virtual machines for a cyber range.",
    version="1.0.0",
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

