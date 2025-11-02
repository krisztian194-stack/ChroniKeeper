import os
for p in [
    "data/maps/world/world_index.json",
    "data/maps/world/grid.json",
    "data/maps/templates/default_map.json",
    "data/maps/templates/default_buildings.json",
    "data/maps/templates/default_rooms.json",
]:
    print(p, "→", os.path.exists(p))
    print("Current working dir:", os.getcwd())
