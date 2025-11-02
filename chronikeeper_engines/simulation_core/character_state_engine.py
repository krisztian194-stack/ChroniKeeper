# ============================================================
# ChroniKeeper – Character State Engine (Unified Simulation Core)
# ============================================================

import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from chronikeeper_engines.core_paths import DATA_ROOT
from chronikeeper_engines.simulation_core import data_loader as DataLoader

# ============================================================
# === Utility & Base Classes =================================
# ============================================================

def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# ============================================================
# === Relationship Manager ===================================
# ============================================================

class RelationshipManager:
    """
    Manages interpersonal relationship tables, modifiers, and
    thematic presets loaded from data/relationship_tables.
    """

    def __init__(self, theme: str = "default"):
        self.theme = theme
        self.tables = DataLoader.load_relationship_tables(theme)
        self.relations: Dict[str, Dict[str, float]] = {}

    def adjust(self, name: str, delta: float):
        self.relations.setdefault(name, {"affinity": 0.5})
        self.relations[name]["affinity"] = clamp(
            self.relations[name]["affinity"] + delta, 0.0, 1.0
        )

    def get_affinity(self, name: str) -> float:
        return self.relations.get(name, {}).get("affinity", 0.5)

    def get_context_fragment(self) -> Dict[str, Any]:
        avg_affinity = (
            sum(v["affinity"] for v in self.relations.values()) / len(self.relations)
            if self.relations else 0.5
        )
        return {"relationship_count": len(self.relations), "affinity_avg": avg_affinity}


# ============================================================
# === Mood Engine ============================================
# ============================================================

class MoodEngine:
    """
    Generates overall mood multiplier based on environment,
    relationships, comfort, and random variance.
    """

    def __init__(self, theme: str = "default"):
        self.theme = theme
        self.base_mood = 0.5

    def update(self, comfort: float, social_affinity: float, stress: float = 0.0) -> float:
        mood = self.base_mood
        mood += (comfort - 0.5) * 0.5
        mood += (social_affinity - 0.5) * 0.4
        mood -= stress * 0.2
        mood += random.uniform(-0.05, 0.05)
        self.base_mood = clamp(mood)
        return self.base_mood

    def get_context_fragment(self) -> Dict[str, Any]:
        return {"mood": round(self.base_mood, 3)}


# ============================================================
# === Memory Engine ==========================================
# ============================================================

class MemoryEvent:
    def __init__(self, event_id: str, summary: str, tags: List[str]):
        self.event_id = event_id
        self.summary = summary
        self.tags = tags
        self.timestamp = datetime.now().isoformat()
        self.familiarity = 0.5

    def reinforce(self, delta: float = 0.05):
        self.familiarity = clamp(self.familiarity + delta)

    def decay(self, days: float = 1.0):
        self.familiarity = clamp(self.familiarity * (0.995 ** days))

    def to_dict(self):
        return self.__dict__


class MemoryEngine:
    def __init__(self, theme: str = "default"):
        self.theme = theme
        self.events: Dict[str, MemoryEvent] = {}

    def add(self, event: MemoryEvent):
        self.events[event.event_id] = event

    def reinforce_by_tag(self, tag: str, delta: float = 0.02):
        for e in self.events.values():
            if tag in e.tags:
                e.reinforce(delta)

    def decay_all(self, days: float = 1.0):
        for e in self.events.values():
            e.decay(days)

    def get_context_fragment(self) -> Dict[str, Any]:
        familiarity_avg = (
            sum(e.familiarity for e in self.events.values()) / len(self.events)
            if self.events else 0.5
        )
        return {"memory_count": len(self.events), "familiarity_avg": familiarity_avg}


# ============================================================
# === NPC Manager ============================================
# ============================================================

class NPCManager:
    """
    Tracks active NPCs, basic schedules, and simplified traits.
    """

    def __init__(self):
        self.npcs: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, occupation: str = "civilian", shift: str = "day"):
        self.npcs[name] = {
            "occupation": occupation,
            "shift": shift,
            "mood": random.uniform(0.4, 0.6),
            "last_seen": datetime.now().isoformat(),
        }

    def update_all(self, world_context: Dict[str, Any]):
        for npc in self.npcs.values():
            comfort = world_context.get("comfort", 0.5)
            noise = world_context.get("noise", 0.5)
            delta = (comfort - noise) * 0.02
            npc["mood"] = clamp(npc["mood"] + delta + random.uniform(-0.01, 0.01))

    def get_context_fragment(self) -> Dict[str, Any]:
        avg_mood = (
            sum(n["mood"] for n in self.npcs.values()) / len(self.npcs)
            if self.npcs else 0.5
        )
        return {"npc_count": len(self.npcs), "npc_mood_avg": avg_mood}


# ============================================================
# === Session Memory =========================================
# ============================================================

class SessionMemory:
    """
    Ephemeral memory limited to one runtime/chat session.
    """

    def __init__(self, session_id: str = "session_default"):
        self.session_id = session_id
        self.entries: List[str] = []

    def add(self, text: str):
        self.entries.append(text)
        if len(self.entries) > 200:
            self.entries.pop(0)

    def summarize(self, limit: int = 5) -> str:
        return " | ".join(self.entries[-limit:])

    def get_context_fragment(self) -> Dict[str, Any]:
        return {"session_entry_count": len(self.entries)}


# ============================================================
# === Character State Engine (Main) ==========================
# ============================================================

class CharacterStateEngine:
    """
    Central simulation engine combining mood, relationships,
    memory, NPCs, and session memory.
    """

    def __init__(self, theme: str = "default", storage_path: Optional[str] = None):
        self.theme = theme
        self.storage_path = storage_path or os.path.join(DATA_ROOT, "character_state.json")

        self.relationships = RelationshipManager(theme)
        self.mood_engine = MoodEngine(theme)
        self.memory = MemoryEngine(theme)
        self.npc_manager = NPCManager()
        self.session_memory = SessionMemory()
        self.last_update = datetime.now()

        self.load()

    # --------------------------------------------------------
    # === Core update & integration ==========================
    # --------------------------------------------------------

    def update_state(self, world_context: Dict[str, Any]):
        # --- Update environment effects ---
        comfort = world_context.get("comfort", 0.5)
        social_affinity = self.relationships.get_context_fragment()["affinity_avg"]
        stress = world_context.get("noise", 0.5)
        self.mood_engine.update(comfort, social_affinity, stress)

        # --- Update NPCs and memory ---
        self.npc_manager.update_all(world_context)
        self.memory.decay_all(days=1.0)

        # --- Save ephemeral memory if any ---
        if len(self.session_memory.entries) > 100:
            self.save()

    # --------------------------------------------------------
    # === Persistence ========================================
    # --------------------------------------------------------

    def save(self):
        data = {
            "theme": self.theme,
            "relationships": self.relationships.relations,
            "memory": {k: e.to_dict() for k, e in self.memory.events.items()},
            "npcs": self.npc_manager.npcs,
            "session": self.session_memory.entries,
            "last_update": self.last_update.isoformat(),
        }
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self):
        if not os.path.exists(self.storage_path):
            print(f"[INFO] No previous character state at {self.storage_path}")
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.theme = data.get("theme", self.theme)
            self.relationships.relations = data.get("relationships", {})
            self.npc_manager.npcs = data.get("npcs", {})
            self.session_memory.entries = data.get("session", [])
            for k, v in data.get("memory", {}).items():
                self.memory.events[k] = MemoryEvent(v["event_id"], v["summary"], v["tags"])
                self.memory.events[k].familiarity = v.get("familiarity", 0.5)
        except Exception as e:
            print("[WARN] Failed to load character state:", e)

    # --------------------------------------------------------
    # === Export Context =====================================
    # --------------------------------------------------------

    def get_context_fragment(self) -> Dict[str, Any]:
        ctx = {}
        ctx.update(self.relationships.get_context_fragment())
        ctx.update(self.mood_engine.get_context_fragment())
        ctx.update(self.memory.get_context_fragment())
        ctx.update(self.npc_manager.get_context_fragment())
        ctx.update(self.session_memory.get_context_fragment())
        return ctx
