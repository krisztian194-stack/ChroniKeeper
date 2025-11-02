# tests/test_environment_events.py
# Demonstrates forcing storm/fog/heatwave and seasonal/area fade

from environment_engine import EnvironmentEngine
from world_state import WorldState

def main():
    print("=== Environment Events Test ===")

    # fake map manager for 3 different contexts
    class FakeMap:
        def __init__(self, ctx): self.ctx = ctx
        def get_context_fragment(self, loc): return self.ctx

    # 1) coastal town – high water, medium airflow
    coastal_map = FakeMap({
        "heat_retention": 0.1,
        "airflow": 0.5,
        "water_coverage": 0.8,
        "elevation": 0.1,
        "comfort": 0.05,
        "noise": 0.2,
    })
    env = EnvironmentEngine(map_manager=coastal_map)
    ws = WorldState(environment_engine=env)
    ws.climatic_zone = "temperate"
    ws.hemisphere = "north"
    ws.location_id = "coastal_town"

    # force a storm for testing
    env.set_test_flag("storm", duration=6)

    for i in range(10):
        ws.advance_time(1)
        sig = ws.environment_signature
        print(f"Tick {i:02d} | {ws.describe_time()} | "
              f"Ev:{sig['active_events']}({sig['event_intensity']}) | "
              f"Prec:{sig['precipitation']:.2f} Vis:{sig['visibility']:.2f} "
              f"Comfort:{sig['comfort']:.2f} Wind:{sig['wind_kmh']:.1f} km/h")

    print("\n--- Switching to mountain village (should clear faster) ---\n")

    # 2) mountain village – high elevation, high airflow → faster fade
    mountain_map = FakeMap({
        "heat_retention": 0.0,
        "airflow": 0.8,
        "water_coverage": 0.2,
        "elevation": 0.8,
        "comfort": 0.0,
        "noise": 0.1,
    })
    env2 = EnvironmentEngine(map_manager=mountain_map)
    ws2 = WorldState(environment_engine=env2)
    ws2.climatic_zone = "temperate"
    ws2.hemisphere = "north"
    ws2.location_id = "mountain_village"

    env2.set_test_flag("fog", duration=5)

    for i in range(8):
        ws2.advance_time(1)
        sig = ws2.environment_signature
        print(f"[MTN] {ws2.describe_time()} | Ev:{sig['active_events']}({sig['event_intensity']}) "
              f"| Vis:{sig['visibility']:.2f} | Wind:{sig['wind_kmh']:.1f} km/h")

if __name__ == "__main__":
    main()
