import os
import sys

# Ensure the root directory is in python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Needhi AI Full-Stack Legal Suite (FastAPI Backend)...")
    print("Serving React Frontend built files from backend/server.py")
    print("Please open http://localhost:8000 in your browser.")
    print("=" * 60)
    
    import uvicorn
    # Start the server on port 8000
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)
