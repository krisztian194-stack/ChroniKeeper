from memory_engine import MemoryEngine
from day_night_tracker import DayNightTracker
from relationship_manager import RelationshipManager
from summary_generator import SummaryGenerator
from cli_debug import run_cli

"""
ChroniKeeper – Quick Pickup CLI
Tests MemoryEngine, MemoryEvent, and readiness logic without LLM.
"""

from datetime import datetime, timedelta
from memory_engine import MemoryEngine, MemoryEvent

# Initialize the engine (you can tweak personality_multiplier later)
engine = MemoryEngine(personality_multiplier=1.0)

print("=== ChroniKeeper Quick Pickup Test ===")

# 1️⃣ Create sample memories
sample_memories = [
    MemoryEvent(event_id="mem_001", summary="Practiced guitar", tags=["skill:guitar", "music"]),
    MemoryEvent(event_id="mem_002", summary="Read Python documentation", tags=["skill:python", "learning"]),
    MemoryEvent(event_id="mem_003", summary="Met Alex for project discussion", tags=["social", "project"]),
]

# 2️⃣ Add them to engine
for mem in sample_memories:
    engine.add_memory(mem)
    print(f"Added memory: {mem.event_id} — {mem.summary}")

# 3️⃣ Reinforce a skill
print("\nReinforcing 'guitar' skill...")
engine.reinforce_by_tags(["skill:guitar"], current_time=datetime.now())

# 4️⃣ Fast-forward time to simulate decay
future_time = datetime.now() + timedelta(days=14)
print("\nSimulating 14 days later...")
for mem in engine.memories.values():
    readiness = mem.readiness_score(personality_multiplier=engine.personality_multiplier)
    print(f"[{mem.event_id}] {mem.summary} → readiness: {readiness:.3f}")

# 5️⃣ Search by tag
print("\nSearching memories tagged with 'python':")
matches = engine.search_by_tags(["skill:python"])
for mem in matches:
    print(f"→ {mem.event_id}: {mem.summary} (tags: {mem.tags})")

# 6️⃣ Save state
engine.save("debug_memory_state.json")
print("\nMemory state saved to debug_memory_state.json")

print("\n=== Done ===")

