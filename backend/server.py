import os
import sys

# Ensure the backend directory is in the python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

if __name__ == "__main__":
    import uvicorn
    # Local developmental server runner
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
