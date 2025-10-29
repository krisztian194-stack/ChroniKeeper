# ============================================================
# ChroniKeeper – Extended Test
# Focus: fuzzy decay, emotional bias, and compact skill context
# ============================================================

from datetime import datetime
from memory_engine import MemoryEngine, MemoryEvent

print("=== ChroniKeeper Extended Test ===")

# Initialize engine
engine = MemoryEngine(storage_path="test_memory_data.json", personality_multiplier=1.0)

# 1️⃣ Create memories with mild emotional tone
m1 = MemoryEvent(
    event_id="skill_python_001",
    summary="Studied Python basics and fixed a stubborn bug.",
    tags=["skill:python", "learning"],
    participants=["self"],
    location="home",
    emotion_score=-0.3,  # negative (remembered mistake)
)

m2 = MemoryEvent(
    event_id="skill_guitar_001",
    summary="Played an easy song successfully.",
    tags=["skill:guitar", "music"],
    participants=["self"],
    location="studio",
    emotion_score=0.4,  # positive (success fades faster)
)

engine.add_memory(m1)
engine.add_memory(m2)

# 2️⃣ Reinforce skill
print("\n[TEST] Reinforcing Python-related memories...")
engine.reinforce_by_tags(["skill:python"], current_time=datetime.now())

# 3️⃣ Simulate fuzzy decay for 30 days
print("\n[TEST] Fuzzy decay simulation (30 days)...")
for day in range(1, 31):
    for mem in engine.memories.values():
        mem.decay(1)
    if day % 5 == 0:
        print(f"\n--- Day {day:02d} ---")
        for mem in engine.memories.values():
            print(f"{mem.event_id:<20} | Tier: {mem.skill_tier():<8} | Fam: {mem.familiarity:.3f} | Conf: {mem.confidence:.2f}")

# 4️⃣ LLM context compression output
print("\n[TEST] Compact LLM context:")
print(engine.build_compact_skill_context())

print("\n=== TEST COMPLETE ===")
