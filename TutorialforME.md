ONLY WORKS ON LOCAL NETWORK??? 

- Step 1: sudo apt-get update
- Step 2: sudo apt-get install -y python3-pip python3-venv git curl
- Step 3: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
- Step 4: sudo apt-get install -y nodejs
- Step 5: Go root dir (proxmox_web) run python3 -m venv venv and then source venv/bin/activate
- Step 6: pip install -r requirements.txt
- Step 7: run ./prep.sh and key in details (need create Proxmox API first, i untick the privilege seperation)
- Step 8: npm i in prox_frontend then npm run dev (for frontend)
- Step 9: uvicorn app.main:app --reload --host 0.0.0.0 (for backend) (ye ik its 0.0.0.0 which is bad but its for my own development purposes rn)
- Step 10: Open browser and put in the network ip addr after npm run dev

Its not a read me ah im jus writing so i wont forget.
