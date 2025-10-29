import json
import math
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# ============================================================
# ChroniKeeper v0.2 – Core Memory Engine
# Handles event storage, decay, recall, and emotional weighting
# ============================================================

class MemoryEvent:
    def __init__(
        self,
        event_id: str,
        summary: str,
        tags: List[str],
        participants: List[str],
        location: str,
        emotion_score: float = 0.0,
        importance: float = 1.0,
        memorable: bool = False,
        core_memory: bool = False,
        date_created: Optional[str] = None,
    ):
        self.event_id = event_id
        self.summary = summary.strip()
        self.tags = [t.lower() for t in tags]
        self.participants = participants
        self.location = location
        self.emotion_score = emotion_score
        self.importance = importance
        self.memorable = memorable
        self.core_memory = core_memory
        self.frequency_count = 1
        self.last_recalled = None
        self.created_at = date_created or datetime.utcnow().isoformat()
        self.accuracy = 1.0  # start fully accurate

    # --------------------------------------------
    # Memory decay function (called per "story day")
    # --------------------------------------------
    def decay(self, days_passed: int, personality_multiplier: float = 1.0):
        if self.core_memory:
            return  # Core memories never decay

        decay_rate = 0.0015 * (2.0 - self.importance)
        if self.memorable:
            decay_rate *= 0.5  # memorable events fade slower

        decay_factor = math.exp(-decay_rate * days_passed * personality_multiplier)
        old_acc = self.accuracy
        self.accuracy = max(0.2, self.accuracy * decay_factor)  # never drop below 0.2

        # print for debugging if accuracy changes significantly
        if abs(old_acc - self.accuracy) > 0.05:
            print(f"[DEBUG] Memory {self.event_id} decayed from {old_acc:.2f} → {self.accuracy:.2f}")

    # --------------------------------------------
    # Revival logic (called when memory is mentioned)
    # --------------------------------------------
    def revive(self):
        boost = 0.15
        old_acc = self.accuracy
        self.accuracy = min(1.0, self.accuracy + boost)
        self.last_recalled = datetime.utcnow().isoformat()
        print(f"[DEBUG] Revived memory {self.event_id} ({old_acc:.2f} → {self.accuracy:.2f})")

    # --------------------------------------------
    # Fuzzy recall – partial data when accuracy < 0.5
    # --------------------------------------------
    def recall(self):
        if self.accuracy >= 0.5:
            return {
                "summary": self.summary,
                "tags": self.tags,
                "clarity": round(self.accuracy, 2),
            }
        else:
            return {
                "summary": "The memory feels vague... only fragments remain.",
                "tags": self.tags[:2],
                "clarity": round(self.accuracy, 2),
            }

    def to_dict(self):
        return self.__dict__


# ============================================================
# ChroniKeeper Memory Engine
# ============================================================
class MemoryEngine:
    def __init__(self, storage_path="memory_data.json", personality_multiplier=1.0):
        self.storage_path = storage_path
        self.memories: Dict[str, MemoryEvent] = {}
        self.personality_multiplier = personality_multiplier
        self.load()

    # ------------------------------
    # Basic save/load functionality
    # ------------------------------
    def save(self):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump({k: v.to_dict() for k, v in self.memories.items()}, f, indent=2)

    def load(self):
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in data.items():
                self.memories[k] = MemoryEvent(**v)
            print(f"[INFO] Loaded {len(self.memories)} memories from {self.storage_path}")
        except FileNotFoundError:
            print(f"[INFO] No existing memory file found, starting fresh.")

    # ------------------------------
    # Add new memory
    # ------------------------------
    def add_memory(self, event: MemoryEvent):
        self.memories[event.event_id] = event
        print(f"[INFO] Added memory '{event.event_id}' ({event.summary[:40]}...)")
        self.save()

    # ------------------------------
    # Advance time and decay memories
    # ------------------------------
    def tick_time(self, days=1):
        print(f"[INFO] Advancing {days} day(s)...")
        for mem in self.memories.values():
            mem.decay(days, self.personality_multiplier)
        self.save()

    # ------------------------------
    # Recall by tag or fuzzy recall
    # ------------------------------
    def recall_by_tag(self, tag: str):
        tag = tag.lower()
        found = [m for m in self.memories.values() if tag in m.tags]
        if not found:
            print(f"[INFO] No memories with tag '{tag}'.")
            return []

        for m in found:
            m.revive()

        self.save()
        return [m.recall() for m in found]

    # ------------------------------
    # List memory stats
    # ------------------------------
    def stats(self):
        return {
            "total": len(self.memories),
            "avg_accuracy": round(sum(m.accuracy for m in self.memories.values()) / len(self.memories), 2)
            if self.memories else 0,
        }
