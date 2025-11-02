from character_state_engine import CharacterStateEngine, MemoryEvent

engine = CharacterStateEngine()

# Create a fake memory
mem = MemoryEvent(event_id="skill_cook_001", summary="Practiced cooking", tags=["skill:cooking"])
engine.add_memory(mem)

# Simulate environment update
engine.update_state(days_passed=2)
engine.reinforce_memory("skill:cooking")
engine.adjust_relationship("player", "npc_chef", +0.4)

engine.debug_print()
print(engine.export_summary())
