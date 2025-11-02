# ============================================================
# ChroniKeeper – Test: EnvironmentEngine Time Buffer
# ============================================================

from environment_engine import EnvironmentEngine
from world_state import WorldState

def main():
    print("=== ChroniKeeper Time Buffer Test ===")

    env = EnvironmentEngine()
    ws = WorldState(environment_engine=env)

    # --- Starting state ---
    print(ws.describe_time())

    # --- Scenario 1: LLM misunderstanding (rollback) ---
    env.request_time(0.1)  # user action queued (~6 min)
    print(f"After request: pending={env._pending_hours:.2f}h")
    env.rollback_time()    # user rewrites
    print(f"After rollback: pending={env._pending_hours:.2f}h")

    # --- Scenario 2: Confirmed short talk ---
    env.request_time(0.05)
    env.commit_time()
    print(ws.describe_time())

    # --- Scenario 3: Walk to another district (longer) ---
    env.request_time(0.25)
    env.commit_time()
    print(ws.describe_time())

    # --- Scenario 4: Sleep skip (force advance) ---
    env.force_time_jump(8.0)
    print(ws.describe_time())

    # --- Scenario 5: Idle LLM grace tick ---
    for i in range(4):
        env.graceful_tick(0.02)
        print(f"Grace tick {i} | pending={env._pending_hours:.2f}h")
    env.commit_time()
    print(ws.describe_time())

if __name__ == "__main__":
    main()
