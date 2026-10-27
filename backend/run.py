"""
Launcher for Indian Retail Billing Backend Server
"""
import uvicorn
import os
import sys

# Ensure project root is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# Load .env file automatically if present
env_file = os.path.join(root_dir, ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    print(f"Starting Indian Shopkeeper Conversational Billing Backend Server on port {port}...")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=False)
