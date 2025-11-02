from world_state import WorldState

ws = WorldState(species="wolfkin")
ws.set_alignment_summary("streetwise, avoids police, protective of family")
ws.set_location("city_square")
ws.add_item("flashlight")
ws.add_item("watch")

ctx = ["time","crowd","weather","visibility","alignment"]

# For LLM use (clean)
print("[RUNTIME]", ws.get_status(ctx, mode="RUNTIME"))

# For debugging (full info)
print("[DEBUG]", ws.get_status(ctx, mode="DEBUG"))
