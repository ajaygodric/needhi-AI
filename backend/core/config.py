import os
from dotenv import load_dotenv

# Initialize dotenv
load_dotenv()

# Root paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATIC_DATA_DIR = os.path.join(ROOT_DIR, "backend", "data")


# Detect persistent storage mount directory (e.g. Render persistent disk)
PERSISTENT_DIR = "/opt/needhi-data"
if os.path.exists(PERSISTENT_DIR) and os.access(PERSISTENT_DIR, os.W_OK):
    DATA_DIR = PERSISTENT_DIR
else:
    DATA_DIR = STATIC_DATA_DIR

DATABASE_FILE = os.path.join(DATA_DIR, "needhi.db")

# Load API keys from environment variables
def load_api_keys():
    keys = []
    # Primary Key
    p_key = os.environ.get("GEMINI_API_KEY")
    if p_key:
        keys.append(p_key)
        
    # Check fallback rotated keys
    for i in range(2, 7):
        f_key = os.environ.get(f"GEMINI_API_KEY_{i}")
        if f_key and f_key not in keys:
            keys.append(f_key)
            
    # Fallback to local secrets.toml only if it exists (for backward compatibility during migration)
    if not keys:
        try:
            secrets_path = os.path.join(ROOT_DIR, ".streamlit", "secrets.toml")
            if os.path.exists(secrets_path):
                with open(secrets_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "GEMINI_API_KEY" in line and "=" in line:
                            val = line.split("=")[1].strip().strip('"').strip("'")
                            if val and val not in keys:
                                keys.append(val)
        except Exception:
            pass
            
    return keys if keys else [""]

API_KEYS = load_api_keys()
GOOGLE_API_KEY = API_KEYS[0]

MODEL_FALLBACK_ORDER = [
    "models/gemini-2.5-flash-lite",
    "models/gemini-2.5-flash",
    "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-lite",
]

ACTIVE_MODEL_NAME = "models/gemini-2.5-flash-lite"
