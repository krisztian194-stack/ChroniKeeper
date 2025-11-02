import os, sys
from map_manager import MapManager

# --- ensure we are using the project root as base path ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
DATA_ROOT = os.path.join(PROJECT_ROOT, "data")
print("=== ChroniKeeper MapManager Test ===")

# ensure paths resolve from project root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT_DIR)
sys.path.insert(0, ROOT_DIR)

mm = MapManager()

tiles = ["A1", "A2", "B1", "B2", "C1", "C2", "HOME_PLAYER"]
for t in tiles:
    ctx = mm.get_context_fragment(t)
    print(
        f"{t:10} | Region:{ctx.get('region','-'):<16} "
        f"Type:{ctx.get('zone_type','-'):<10} "
        f"Light:{ctx.get('light_pollution',0):.2f} "
        f"RoomL:{ctx.get('room_light',0):.2f} "
        f"Comfort:{ctx.get('comfort',0):.2f} "
        f"Noise:{ctx.get('noise',0):.2f} "
        f"Air:{ctx.get('air_quality',0):.2f} "
        f"Landmark:{ctx.get('landmark','-')}"
    )
