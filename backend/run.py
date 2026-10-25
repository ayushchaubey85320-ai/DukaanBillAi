"""
Launcher for Indian Retail Billing Backend Server
"""
import uvicorn
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    print("Starting Indian Shopkeeper Conversational Billing Backend Server on port 8001...")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8001, reload=False)
