from memory_engine import MemoryEngine
from world_state import WorldState
from prompt_manager import PromptManager

# --- setup ---
engine = MemoryEngine()
world = WorldState(species="wolfkin")
pm = PromptManager(engine, world)

# --- sample memory for context ---
from memory_engine import MemoryEngine, MemoryEvent
# later in code
engine.add_memory(MemoryEvent(
    event_id="001",
    summary="Practiced guitar",
    tags=["skill:guitar"],
    participants=["self"],
    location="studio"
))
# --- setup world ---
world.set_alignment_summary("streetwise, avoids police, protective of family")
world.set_location("city_square")
world.add_item("flashlight")
world.add_item("watch")

ctx_keywords = ["time", "crowd", "weather", "alignment"]

# --- Runtime prompt (for AI) ---
runtime_prompt = pm.build_prompt(
    player_action="Look around the square for a place to rest.",
    goal="Stay unnoticed while resting.",
    context_keywords=ctx_keywords,
    mode="RUNTIME"
)
print(runtime_prompt)

# --- Debug prompt (for testing) ---
debug_prompt = pm.build_prompt(
    player_action="Look around the square for a place to rest.",
    goal="Stay unnoticed while resting.",
    context_keywords=ctx_keywords,
    mode="DEBUG"
)
print(debug_prompt)
