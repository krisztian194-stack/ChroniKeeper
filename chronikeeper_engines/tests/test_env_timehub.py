# test_env_timehub.py
from environment_engine import EnvironmentEngine

env = EnvironmentEngine()
env.hemisphere = "north"
env.latitude = 30.0

print("=== One-day simulation ===")
for hour in range(0, 25, 3):
    env.set_hour(hour)
    sig = env.update()
    print(f"{hour:02d}h | Season:{sig['season']:<7} T:{sig['temperature']:.2f} Comfort:{sig['comfort']:.2f} Night:{sig['is_night']}")
