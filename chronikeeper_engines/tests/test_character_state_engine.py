# ============================================================
# ChroniKeeper – Character State Integration Test
# ============================================================

import os, sys
from datetime import datetime

# --- Force working directory to project root ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

# --- Imports from core packages ---
from chronikeeper_engines.world_core import WorldState, EnvironmentEngine
from chronikeeper_engines.simulation_core import CharacterStateEngine


print("=== ChroniKeeper Character State Integration Test ===")

# ------------------------------------------------------------
# 1️⃣ Initialize world + environment
# ------------------------------------------------------------
env_engine = EnvironmentEngine()
world = WorldState(environment_engine=env_engine)

for _ in range(8):
    sig = env_engine.update()
    print(f"{sig['hour']:05.2f}h | Temp:{sig['temperature']:.2f}  Comfort:{sig['comfort']:.2f}  "
          f"Visibility:{sig['visibility']:.2f}  Season:{sig['season']}")
    env_engine.advance_time(3.0)  # move 3 hours forward per tick

# ------------------------------------------------------------
# 2️⃣ Initialize Character State Engine
# ------------------------------------------------------------
char_engine = CharacterStateEngine(theme="default")

# Create a few NPCs
char_engine.npc_manager.register("Aiden", "technician", "day")
char_engine.npc_manager.register("Bella", "teacher", "morning")
char_engine.npc_manager.register("Carlos", "student", "afternoon")

# ------------------------------------------------------------
# 3️⃣ Run daily update ticks
# ------------------------------------------------------------
print("\n[INFO] Running daily state updates...")
for hour in range(0, 24, 6):
    # Sync world with environment
    world.environment_signature = getattr(env_engine, "get_signature", None)() if hasattr(env_engine, "get_signature") else env_engine.signature

    # Update character state based on environment
    char_engine.update_state(world.environment_signature)

    ctx = char_engine.get_context_fragment()
    print(
        f"{hour:02d}h | Mood:{ctx['mood']:.2f}  "
        f"Memory:{ctx['memory_count']:02d}  Familiarity:{ctx['familiarity_avg']:.2f}  "
        f"NPCs:{ctx['npc_count']}  NPC_Mood:{ctx['npc_mood_avg']:.2f}"
    )

# ------------------------------------------------------------
# 4️⃣ Save + summarize
# ------------------------------------------------------------
char_engine.save()
print("\n[INFO] Character state saved successfully.")
summary = char_engine.get_context_fragment()
print("[SUMMARY]", summary)
print("[INFO] Test completed successfully at", datetime.now().strftime("%H:%M:%S"))
