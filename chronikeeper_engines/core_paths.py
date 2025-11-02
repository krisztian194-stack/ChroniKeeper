# chronikeeper_engines/core_paths.py
import os

# Base directory of this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Corrected data root inside the engine folder
DATA_ROOT = os.path.join(BASE_DIR, "data")

# Ensure the path exists
if not os.path.exists(DATA_ROOT):
    print(f"[WARN] DATA_ROOT not found at {DATA_ROOT}")

def ensure_dir(subpath):
    path = os.path.join(DATA_ROOT, subpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path
