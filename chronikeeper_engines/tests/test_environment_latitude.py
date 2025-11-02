"""
ChroniKeeper Test – Environment Latitude & Microclimate
Simulates day length and comfort shifts for various latitudes.
"""

from environment_engine import EnvironmentEngine
from map_manager import MapManager


class DummyWorld:
    """Simple world-state stub for testing the environment engine."""
    def __init__(self, ctx):
        self.location_id = None
        self.climatic_zone = "temperate"
        self.context = ctx


def run_latitude_test(lat, label):
    print(f"\n=== {label} (Latitude {lat}°) ===")

    env = EnvironmentEngine()
    mm = MapManager(template="default")
    env.map_manager = mm  # optional link

    # fake context representing environment tile
    ctx = {
        "latitude": lat,
        "settlement_size": 3 if label == "Mid-Lat City" else 0,
        "structure_density": 0.7 if label == "Mid-Lat City" else 0.0,
        "wind_block": 0.4 if label == "Mid-Lat City" else 0.1,
        "wind_redirect": 0.3 if label == "Mid-Lat City" else 0.2,
        "noise_pollution": 0.6 if label == "Mid-Lat City" else 0.1,
    }

    ws = DummyWorld(ctx)

    # simulate 4 seasonal days
    for day in [30, 100, 180, 300]:
        env.time_state["day_of_year"] = day
        env.time_state["is_night"] = False
        env.time_state["hour"] = 12.0
        result = env.update(ws)
        print(
            f"Day {day:3d} | "
            f"Daylight: {result['ctx']['daylight_hours']:4.1f}h | "
            f"Daylight factor: {result['ctx']['daylight_factor']:.3f} | "
            f"Temp-like Heat: {result['temperature']:.2f} | "
            f"Comfort: {result['comfort']:.2f}"
        )


def main():
    run_latitude_test(0.0, "Equator")
    run_latitude_test(45.0, "Mid-Lat City")
    run_latitude_test(70.0, "Polar Zone")


if __name__ == "__main__":
    print("=== ChroniKeeper: Latitude & Microclimate Test ===")
    main()
    print("\n=== TEST COMPLETE ===")
