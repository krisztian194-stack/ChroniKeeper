# ============================================================
# ChroniKeeper – Map Manager v2
# data-driven, multi-layer (global → regional → local)
# ============================================================

import os, sys
import json
import math
import random
import hashlib
from typing import Dict, Any, Optional, Tuple

# --- ensure we are using the project root as base path ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
DATA_ROOT = os.path.join(PROJECT_ROOT, "data")

# fallback if not found
if not os.path.exists(DATA_ROOT):
    alt_data = os.path.join(CURRENT_DIR, "data")
    if os.path.exists(alt_data):
        DATA_ROOT = alt_data

def _load_json(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"[WARN] missing json: {path}")
    return {}


def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


class MapManager:
    """
    Layered source of world context.

    Priority (low → high):
      1. global_world.json      (optional, climate bands, countries, big water)
      2. default_map.json       (regional / city / district)
      3. grid.json              (local tile: biome, humidity, heat, water)
      4. default_buildings.json (building-level defaults)
      5. default_rooms.json     (room-level lighting / comfort)
      6. locations/*.json       (hand-authored, detective scenes, player home)

    Everything is deterministic on world_seed + coord / location_id.
    """

    def __init__(
        self,
        grid_path: str = None,
        world_path: str = None,
        map_path: str = None,
        buildings_path: str = None,
        rooms_path: str = None,
        locations_dir: str = None,
        world_seed: str = "ChroniKeeper_Default_World",
        ):
        # --- default fallbacks built from detected DATA_ROOT ---
        base = DATA_ROOT
        self.grid_path = grid_path or os.path.join(base, "maps", "world", "grid.json")
        self.world_path = world_path or os.path.join(base, "maps", "world", "world_index.json")
        self.map_path = map_path or os.path.join(base, "maps", "templates", "default_map.json")
        self.buildings_path = buildings_path or os.path.join(base, "maps", "templates", "default_buildings.json")
        self.rooms_path = rooms_path or os.path.join(base, "maps", "templates", "default_rooms.json")
        self.locations_dir = locations_dir or os.path.join(base, "locations")

        # --- world seed/id and data holders (unchanged) ---
        self.world_seed = world_seed
        self.world_id = self._make_world_id(world_seed)
        self.world_index = {}
        self.map_data = {}
        self.grid_data = {}
        self.building_templates = {}
        self.room_templates = {}
        self.landmark_cache = {}

        self._load_all()

    # --------------------------------------------------------
    # init helpers
    # --------------------------------------------------------
    def _make_world_id(self, seed_text: str) -> str:
        h = hashlib.sha256(seed_text.encode()).hexdigest()
        # 16 chars is enough to be "world-unique" for us
        return h[:16]

    def _load_all(self):
        # global layer (optional, for Earth-scale later)
        self.world_index = _load_json(self.world_path)
        # regional / named areas
        self.map_data = _load_json(self.map_path)
        # local tile env
        self.grid_data = _load_json(self.grid_path)
        # building + room
        self.building_templates = _load_json(self.buildings_path)
        self.room_templates = _load_json(self.rooms_path)

    # --------------------------------------------------------
    # RNG helpers
    # --------------------------------------------------------
    def _seed_for(self, *parts) -> int:
        """Stable seed for world + tile."""
        base = self.world_id
        key = base + "_" + "_".join(str(p) for p in parts)
        return int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**32)

    def _weighted_pick(self, rnd: random.Random, table: dict, default: str = "none") -> str:
        if not table:
            return default
        total = sum(table.values())
        r = rnd.random() * total
        acc = 0.0
        for k, w in table.items():
            acc += w
            if r <= acc:
                return k
        # fallback
        return list(table.keys())[0]

    # --------------------------------------------------------
    # landmark helpers
    # --------------------------------------------------------
    def _register_landmark(self, xy, name: str, radius: int):
        if xy is None:
            return
        self.landmark_cache[tuple(xy)] = {"name": name, "radius": radius}

    def _lookup_landmark(self, xy):
        if xy is None:
            return None
        x, y = xy
        for (lx, ly), info in self.landmark_cache.items():
            r = info["radius"]
            if abs(lx - x) <= r and abs(ly - y) <= r:
                return info["name"]
        return None

    # --------------------------------------------------------
    # global / regional lookup
    # --------------------------------------------------------
    def _get_global_region(self, coord) -> dict:
        """
        Later: from big world_index.json figure out which country, climate,
        water body, etc. For now: return empty.
        """
        # structure idea (future):
        # { "bands": [...], "countries": [...], "oceans": [...] }
        return self.world_index.get("global", {})

    def _get_regional_entry(self, location_id: Optional[str], coord) -> dict:
        """
        default_map.json currently holds stuff like:
        {
          "A1": { "region": "urban_core", "coord": [0,0] },
          "regions": { "urban_core": {...}, "suburb": {...} }
        }
        We support BOTH ways:
          - direct tile: "A1"
          - or coord: look for "x,y"
        """
        if location_id and location_id in self.map_data:
            return self.map_data[location_id]

        # coord lookup: "x,y"
        if coord is not None:
            key = f"{coord[0]},{coord[1]}"
            if key in self.map_data:
                return self.map_data[key]

        # if nothing found: empty
        return {}

    def _get_region_template(self, region_key: str) -> dict:
        # default_map.json can have a "regions" section
        regions = self.map_data.get("regions", {})
        return regions.get(region_key, {})

    def _get_grid_tile(self, coord) -> dict:
        """
        grid.json should be keyed either by "x,y" or by int index.
        We'll support "x,y" now.
        """
        if coord is None:
            return {}
        key = f"{coord[0]},{coord[1]}"
        return self.grid_data.get(key, {})

    # --------------------------------------------------------
    # public: main context builder
    # --------------------------------------------------------
    def get_context_fragment(
        self,
        location_id: Optional[str] = None,
        coord: Optional[Tuple[int, int]] = None,
    ) -> dict:
        """
        Returns a FULLY MERGED context:
          - world_id
          - region + region modifiers
          - grid env (humidity, heat_retention, biome, water)
          - building + room comfort
          - light_pollution and landmark
        """

        # 1) figure out coord
        if coord is None:
            # maybe in map file
            if location_id and location_id in self.map_data:
                coord = self.map_data[location_id].get("coord", [0, 0])
            else:
                coord = [0, 0]

        x, y = coord[0], coord[1]

        # 2) RNG for this tile
        seed = self._seed_for(location_id or f"{x}_{y}")
        rnd = random.Random(seed)

        # 3) global (very high level, future: continents, climate, oceans)
        global_ctx = self._get_global_region(coord)

        # 4) regional (from default_map.json, per-tile or named)
        regional_entry = self._get_regional_entry(location_id, coord)
        region_key = regional_entry.get("region", regional_entry.get("zone", "suburb"))
        region_template = self._get_region_template(region_key)

        # 5) local grid info (from grid.json: humidity, heat, noise, water)
        grid_tile = self._get_grid_tile(coord)

        # 6) base ctx
        ctx: Dict[str, Any] = {
            "world_id": self.world_id,
            "location_id": location_id,
            "coord": [x, y],
            "region": region_key,
            "zone_type": region_template.get("type", "wilderness"),
            "name": regional_entry.get("name", ""),
        }

        # ----------------------------------------------------
        # 7) building pick (from region OR from map entry)
        # ----------------------------------------------------
        # priority:
        #   map entry -> region template -> fallback
        region_buildings = region_template.get("buildings", [])
        if "building" in regional_entry:
            building_key = regional_entry["building"]
        elif region_buildings:
            # make weights: all 1 for now
            btable = {b: 1 for b in region_buildings}
            building_key = self._weighted_pick(rnd, btable, default="generic_building")
        else:
            building_key = "generic_building"

        building_data = self.building_templates.get(building_key, {})

        # ----------------------------------------------------
        # 8) room pick (from building template or default_rooms)
        # ----------------------------------------------------
        # in your files: default_buildings.json typically has "rooms": [...]
        room_key = None
        if "rooms" in building_data and building_data["rooms"]:
            room_key = rnd.choice(building_data["rooms"])
        else:
            # fallback to a default room
            room_key = "generic_room"

        room_data = self.room_templates.get(room_key, {})

        # ----------------------------------------------------
        # 9) light pollution & environment base
        # ----------------------------------------------------
        # from region
        region_lp = float(region_template.get("light_pollution", 0.0))
        # from grid (e.g. near water, near city)
        grid_lp = float(grid_tile.get("light_pollution", 0.0))
        # from map explicit
        map_lp = float(regional_entry.get("light_pollution", 0.0))
        # final
        light_pollution = max(region_lp, grid_lp, map_lp)

        # ----------------------------------------------------
        # 10) landmark (deterministic, with radius support)
        # ----------------------------------------------------
        landmark = self._lookup_landmark(coord)
        if not landmark:
            # region can define a landmark pool
            lm_pool = region_template.get("landmarks", {})
            if lm_pool:
                # roll candidates
                candidates = []
                for lname, linf in lm_pool.items():
                    chance = float(linf.get("chance", 0.0))
                    if rnd.random() <= chance:
                        candidates.append((lname, linf))
                if candidates:
                    lname, linf = rnd.choice(candidates)
                    landmark = lname
                    radius = int(linf.get("radius", 0))
                    if radius > 0:
                        self._register_landmark(coord, lname, radius)

        # ----------------------------------------------------
        # 11) comfort / noise / air / safety merge
        # ----------------------------------------------------
        # base from room
        base_comfort = float(room_data.get("comfort_base", 0.5))
        base_noise = float(room_data.get("noise_base", 0.3))
        base_air = float(room_data.get("air_base", 0.6))

        # building-level tweaks
        b_comf_mod = float(building_data.get("comfort_mod", 0.0))
        b_noise_mod = float(building_data.get("noise_mod", 0.0))
        b_air_mod = float(building_data.get("air_mod", 0.0))

        # region-level tweaks (poor/rich/abandoned/etc.)
        r_comf_mod = float(region_template.get("comfort_mod", 0.0))
        r_noise_mod = float(region_template.get("noise_mod", 0.0))
        r_safety_mod = float(region_template.get("safety_mod", 0.0))

        # grid-level influence (noise_pollution, heat_retention, water)
        g_noise = float(grid_tile.get("noise_pollution", 0.0))   # 0..1
        g_heat = float(grid_tile.get("heat_retention", 0.5))     # 0..1
        g_hum = float(grid_tile.get("humidity", 0.5))            # 0..1
        g_water = float(grid_tile.get("water_body", 0.0))        # 0..1 (lake/river/coast)

        # comfort: room + building + region - bad humidity + nice water
        comfort = base_comfort
        comfort += b_comf_mod + r_comf_mod
        comfort -= (g_hum - 0.5) * 0.15          # very humid = slightly less comfy
        comfort += g_water * 0.05                # near large lake/river = tiny bonus
        comfort = _clamp(comfort)

        # noise: room + building + region + grid noise
        noise = base_noise
        noise += b_noise_mod + r_noise_mod
        noise += g_noise * 0.4                   # near road/rail/port
        noise = _clamp(noise)

        # air: room + building + grid (heat + water can trap air)
        air_quality = base_air
        air_quality += b_air_mod
        air_quality -= g_heat * 0.1              # urban heat island
        air_quality -= g_noise * 0.05            # pollution proxy
        air_quality = _clamp(air_quality)

        # safety: region-based first, then noise/weather could tweak later
        safety = 1.0 + r_safety_mod
        safety = _clamp(safety, 0.0, 1.0)

        # ----------------------------------------------------
        # 12) room lighting
        # ----------------------------------------------------
        # room_data can define fixed light, else use pollution as fallback
        if "light" in room_data:
            room_light = float(room_data["light"])
        else:
            # outdoor or non-lit areas: base on environment
            room_light = light_pollution * 0.5
        room_light = _clamp(room_light)

        # ----------------------------------------------------
        # 13) hand-authored location override
        # ----------------------------------------------------
        if location_id:
            custom_path = os.path.join(self.locations_dir, f"{location_id}.json")
            if os.path.exists(custom_path):
                with open(custom_path, "r", encoding="utf-8") as f:
                    loc_override = json.load(f)
                # overrides win
                ctx.update(loc_override)
                # but we keep computed values too unless explicitly replaced
                comfort = float(loc_override.get("comfort", comfort))
                noise = float(loc_override.get("noise", noise))
                air_quality = float(loc_override.get("air_quality", air_quality))
                room_light = float(loc_override.get("room_light", room_light))
                light_pollution = float(loc_override.get("light_pollution", light_pollution))
                landmark = loc_override.get("landmark", landmark)

        # ----------------------------------------------------
        # 14) final ctx
        # ----------------------------------------------------
        ctx.update(
            {
                "building_type": building_key,
                "room_type": room_key,
                "comfort": round(comfort, 3),
                "noise": round(noise, 3),
                "air_quality": round(air_quality, 3),
                "safety": round(safety, 3),
                "light_pollution": round(light_pollution, 3),
                "room_light": round(room_light, 3),
                "landmark": landmark,
                "grid": {
                    "biome": grid_tile.get("biome"),
                    "humidity": g_hum,
                    "heat_retention": g_heat,
                    "noise_pollution": g_noise,
                    "water_body": g_water,
                    "elevation": grid_tile.get("elevation"),
                },
                "global": {
                    "country": global_ctx.get("country"),
                    "climate_band": global_ctx.get("climate_band"),
                    "sea_proximity": global_ctx.get("sea_proximity"),
                },
            }
        )

        return ctx
