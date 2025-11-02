# ============================================================
# ChroniKeeper – Integrated Time & Environment Simulation Test
# Simulates several in-world days with automatic hourly updates
# ============================================================

from environment_engine import EnvironmentEngine
from world_state import WorldState
import time as realtime

def run_timecycle_test(days=2, step_hours=3, sleep_between=0.0):
    """
    Runs a multi-day simulation where environment and world time evolve together.
    You can optionally slow it down with `sleep_between` for live viewing.
    """
    print("=== ChroniKeeper World Simulation Test ===")
    print(f"[INFO] Simulating {days} day(s) with {step_hours}-hour increments\n")

    # --- initialize systems ---
    env = EnvironmentEngine()
    ws = WorldState(environment_engine=env)

    # starting parameters
    ws.climatic_zone = "temperate"
    ws.hemisphere = "north"
    ws.set_location("city_center")

    total_steps = int((24 / step_hours) * days)
    for tick in range(total_steps):
        ws.advance_time(step_hours)
        sig = ws.environment_signature
        time_info = ws.get_time_status()

        # === FORMATTED OUTPUT ===
        day = time_info["day"]
        hour = time_info["hour"]
        season = ws.get_season()
        night_emoji = "🌙" if sig["is_night"] else "☀️"

        print(f"Day {day:02d} | {hour:04.1f}h {night_emoji} | "
              f"Season: {season:<7} | "
              f"T:{sig['temperature']:.2f} | "
              f"Comfort:{sig['comfort']:.2f} | "
              f"Air:{sig['air_quality']:.2f} | "
              f"Vis:{sig['visibility']:.2f}")

        if sleep_between:
            realtime.sleep(sleep_between)

    print("\n=== Simulation complete ===")
    print(f"Final: {ws.describe_time()} | {ws.describe_environment()}\n")

if __name__ == "__main__":
    # Run 3 simulated days, updating every 3 in-world hours
    # (set sleep_between=0.5 if you want slow animated output)
    run_timecycle_test(days=3, step_hours=3, sleep_between=0.0)
