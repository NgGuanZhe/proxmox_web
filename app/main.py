from fastapi import FastAPI
from app.routers import vms, networks, sdn

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
