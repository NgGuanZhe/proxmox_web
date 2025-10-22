A web-based interface for managing Proxmox Virtual Environment (VE) resources, designed to run locally. This application provides a user-friendly way to interact with VMs, networks, SDN features, snapshots, and includes specialized features for creating and managing isolated lab environments. Built with a FastAPI backend and a Vue.js frontend.

## Features

**Authentication & User Management:**

* **User registration** and **login** system using JWT tokens.
* Password validation rules (length, character types) enforced during registration.
* **Admin role** with elevated privileges.
* (Admin) View a list of all registered users.
* (Admin) Delete users (admins cannot delete themselves).

---
**Virtual Machine (VM) Management:**

* **Dashboard:** View all VMs and Templates across all nodes, grouped logically.
* **Basic Operations:** Start/Stop all VMs with bulk actions. Rename individual VMs. Delete individual VMs (including stopping them first if running).
* **Details & Configuration:** View detailed VM information including hardware (CPU, Memory), network interfaces, status, and node. Reconfigure the network bridge for a VM's network interface.
* **Template Cloning:** Clone all detected Proxmox templates into new VMs with unique IDs and names. Delete all VMs previously created via the "Clone All Templates" feature.

---
**Snapshot Management:**

* List existing snapshots for a specific VM.
* Create new snapshots for a VM with a given name.
* Rollback a VM to a selected snapshot state.

---
**Network Management (Linux Bridges):**

* List existing Linux Bridges (`vmbrX`) on each Proxmox node.
* Create new Linux Bridges on a specified node.
* Delete Linux Bridges (excluding `vmbr0` and bridges currently in use).

---
**Proxmox SDN Management:**

* **Zones:** List, create (Simple, VLAN, VXLAN types), and delete SDN Zones. Deletion is prevented if the zone contains VNETs.
* **VNETs:** List, create, and delete SDN VNETs within zones. Requires specifying a VLAN tag when creating a VNET in a VLAN zone. Deletion is prevented if the VNET is in use by a VM.

---
**Lab Environment Management:**

* **Lab Builder:**
    * Define "Lab Groups" by tagging VM Templates and regular VMs via their description (`LabGroups:[group1,group2,...]`).
    * Instantiate a Lab Group: Creates a new, isolated SDN VNET (VLAN type) with a specified tag, clones all associated templates into this network, and optionally adds associated non-template VMs (if they are not part of another active lab instance). VM descriptions are updated to mark them as part of the lab instance (`Lab: <group_name> | Instance: <instance_number>`).
* **Lab Playground:**
    * View active lab instances, grouped by name and instance number (parsed from VM descriptions).
    * Start/Stop all VMs belonging to a specific lab instance.
    * Delete an entire lab instance, which stops and deletes all associated VMs and the corresponding SDN VNET.
    * Edit Lab Membership: Add available VMs (non-templates, not part of other labs) to an existing lab instance or remove VMs from it. Network configurations and descriptions are updated accordingly.

---
**Development & Configuration:**

* **Configuration Script:** Includes `prep.sh` to interactively generate the backend `.env` file, including Proxmox credentials and a securely generated `SECRET_KEY`.
* **Logging:** Backend includes structured JSON logging to file (`app.log`) and detailed error traceback logging to separate files (`log_error/`).

## Technologies Used

* **Backend:**
    * Python
    * FastAPI
    * Proxmoxer (Proxmox API Client)
    * SQLAlchemy & SQLite (for User Management)
    * Passlib & python-jose (JWT Authentication)
    * Uvicorn (ASGI Server)
    * python-dotenv
* **Frontend:**
    * Vue.js 3
    * Vite
    * Vue Router
    * JavaScript
    * CSS

## Prerequisites ⚙️

* Proxmox VE Environment accessible from the machine running the application.
* An API Token created in Proxmox (Permissions depend on desired features, likely requiring VM, Network, and SDN modification rights). Ensure "Privilege Separation" is **unchecked** when creating the token.
* Node.js (v20+) and npm installed.
* Python 3.9+ and pip installed.
* Git and Curl installed.
* `python3-venv` package (or equivalent for your OS).

## Setup and Installation (Local Development) 🚀

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd proxmox_web
    ```

2.  **System Dependencies (Debian/Ubuntu Example):**
    ```bash
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-venv git curl
    # Install Node.js v20+ (using NodeSource)
    curl -fsSL [https://deb.nodesource.com/setup_20.x](https://deb.nodesource.com/setup_20.x) | sudo -E bash -
    sudo apt-get install -y nodejs
    ```
    *(Adapt package manager commands for your specific Linux distribution if not using Debian/Ubuntu)*.

3.  **Configure Backend:**
    * **Set Token Secret:** Before running `prep.sh`, set your Proxmox API token **value** (the secret UUID) as an environment variable. **Use a space before the command** in Bash/Zsh to potentially prevent it from being saved in history:
        ```bash
         export PROXMOX_TOKEN_VALUE_ENV='YOUR_API_TOKEN_SECRET_VALUE'
        ```
       
    * **Run Prep Script:** Execute the preparation script. It will prompt for your Proxmox host IP, user (`user@realm`), API token **name**, and automatically detect the host IP for the frontend configuration. It reads the token value from the environment variable set above and generates a `SECRET_KEY`.
        ```bash
        chmod +x prep.sh
        ./prep.sh
        ```
        This creates the `.env` file in the root directory. The `PROXMOX_TOKEN_VALUE_ENV` variable is unset after the script runs.

4.  **Backend Setup & Run:**
    * Create and activate a Python virtual environment:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
       
    * Install Python dependencies:
        ```bash
        pip install -r requirements.txt
        ```
       
    * Run the FastAPI development server (leave this running in a terminal):
        ```bash
        uvicorn app.main:app --reload --host 0.0.0.0 
        ```
       

5.  **Frontend Setup & Run:**
    * Navigate to the frontend directory (in a **new** terminal):
        ```bash
        cd prox_frontend
        ```
    * Install Node.js dependencies:
        ```bash
        npm install
        ```
       
    * Run the Vite development server (leave this running):
        ```bash
        npm run dev
        ```

6.  **Access the Application:**
    Open your web browser and navigate to the local network IP address shown in the Vite output (e.g., `http://<your-local-ip>:5173`).

## API Documentation 📚

The backend is built using FastAPI, which automatically generates interactive API documentation. While the backend (`uvicorn`) is running, you can access it at:

* `http://<backend-ip>:8000/docs` (Swagger UI)
* `http://<backend-ip>:8000/redoc` (ReDoc)

Where `<backend-ip>` is the IP address of the machine running the backend (likely your local machine's IP).
