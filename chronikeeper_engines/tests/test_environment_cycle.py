# test_env_quick.py

from environment_engine import EnvironmentEngine
from world_state import WorldState
from map_manager import MapManager  # use your current one

# fake map manager if you want to run without real map
class FakeMap:
    def __init__(self, ctx): self.ctx = ctx
    def get_context_fragment(self, loc): return self.ctx

ws = WorldState()
ws.climatic_zone = "arid"   # desert
ws.set_hemisphere("north")

# desert open sand
desert_map = FakeMap({"heat_retention": 0.1, "airflow": 0.4, "noise": 0.05})
desert_env = EnvironmentEngine(map_manager=desert_map)

# city center (hot, bad airflow)
city_map = FakeMap({"heat_retention": 0.4, "airflow": 0.2, "noise": 0.4, "air_quality": -0.2, "comfort": -0.1})
city_env = EnvironmentEngine(map_manager=city_map)

print("=== Desert vs City (every 3h) ===")
for h in range(0, 24, 3):
    ws.time.set_hour(h)
    d_sig = desert_env.update(ws)
    c_sig = city_env.update(ws)
    print(f"{h:02d}h | DESERT T:{d_sig['temperature']:.2f} C:{d_sig['comfort']:.2f}  ||  CITY T:{c_sig['temperature']:.2f} C:{c_sig['comfort']:.2f}")
