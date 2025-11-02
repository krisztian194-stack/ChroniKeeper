# ============================================================
# ChroniKeeper – Test: NPC Family Behavior
# ============================================================

from npc_manager import NPCManager
from world_state import WorldState   # your existing one

def main():
    print("=== NPC Family Behavior Test ===")

    ws = WorldState()
    ws.set_hemisphere("north")
    ws.set_climatic_zone("temperate")

    npc_mgr = NPCManager(
        npc_path="data/npcs/world_default_npcs.json",
        persistent=False
    )

    # simulate 3 days, 24h each
    for day in range(1, 4):
        for hour in range(0, 24):
            ws.time.set_time(day=day, hour=hour)  # depends on your time API
            npc_mgr.update_all(ws, player_coord=[0,0], active_radius=3)

        print(f"\n--- DAY {day} SUMMARY ---")
        for npc_id, npc in npc_mgr.npcs.items():
            act = npc.get("current_activity", "unknown")
            shift = npc.get("current_shift", "n/a")
            mood = npc.get("mood", 0.0)
            name = npc.get("name", npc_id)
            print(f"{name:<18} | shift: {shift:<10} | act: {act:<14} | mood: {mood:+.2f}")

if __name__ == "__main__":
    main()
