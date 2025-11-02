# ============================================================
# ChroniKeeper – Test: Moon Phase & Night Visibility
# ============================================================

from environment_engine import EnvironmentEngine
from world_state import WorldState

def main():
    print("=== ChroniKeeper Moon Cycle & Visibility Test ===")

    # --- Setup ---
    env = EnvironmentEngine()
    ws = WorldState(environment_engine=env)
    ws.climatic_zone = "temperate"
    ws.hemisphere = "north"

    # Start at midnight for clearer moonlight reading
    env.set_hour(0.0)
    print(f"{'Day':>3} | {'Hour':>4} | {'Phase':<18} | {'MoonLight':>9} | {'VisFloor':>9} | {'Season':>8}")

    # --- Simulate 30 consecutive nights ---
    for day in range(1, 31):
        env.time_state["is_night"] = True
        sig = env.update(ws)

        print(f"{day:3d} | {env.time_state['hour']:4.1f} | "
              f"{sig['moon_phase']:<18} | {sig['moon_light']:9.2f} | "
              f"{sig['visibility']:9.2f} | {sig['season']:>8}")

        # advance one day (24h)
        env.advance_time(24)

    print("\n=== Cycle complete ===")
    print("You should see phases from New Moon → Full Moon → back to Crescent.")

if __name__ == "__main__":
    main()
