# ============================================================
# ChroniKeeper – Data Loader
# Generic JSON table merger for modular data-driven systems.
# ============================================================

import os, json, glob
from chronikeeper_engines.core_paths import DATA_ROOT

def load_tables(base_dir: str, theme: str = "default", prefix: str = "", fallback_data=None):
    """
    Auto-loads and merges all JSON files matching {prefix}{theme or default}_*.json.
    Default files load first, theme files override.
    Returns merged dict.
    """
    tables = {}
    if not os.path.exists(base_dir):
        print(f"[WARN] Missing data directory: {base_dir}")
        return fallback_data or {}

    files = glob.glob(os.path.join(base_dir, f"{prefix}*.json"))
    # Load defaults first
    files.sort(key=lambda f: "default" not in f)

    theme_files = [f for f in files if "default" in f or theme in f]
    for path in theme_files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Deep merge
            for k, v in data.items():
                if isinstance(v, dict):
                    tables.setdefault(k, {}).update(v)
                else:
                    tables[k] = v
        except Exception as e:
            print(f"[WARN] Failed to load {path}: {e}")
    if not tables and fallback_data:
        tables = fallback_data
    print(f"[INFO] Loaded {len(theme_files)} data files from '{base_dir}' (theme='{theme}')")
    return tables

def load_relationship_tables(theme: str = "default"):
    base_path = os.path.join(DATA_ROOT, "relationship_tables", f"{theme}.json")
    alt_path = os.path.join(DATA_ROOT, "relationship_tables", f"{theme}_relationship_weights.json")
    for path in (base_path, alt_path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    print(f"[WARN] relationship table not found: {base_path}")
    return {}
