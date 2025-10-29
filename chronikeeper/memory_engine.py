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
        **kwargs,
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
        self.created_at = date_created or datetime.utcnow().isoformat()
        self.accuracy = 1.0

        # >>> SKILL TRACKING 001 <<<
        self.frequency_count = kwargs.get("frequency_count", 1)
        self.familiarity = kwargs.get("familiarity", 0.0)
        self.last_occurrence = kwargs.get("last_occurrence", None)
        # <<< END SKILL TRACKING 001 >>>
        
        # >>> SKILL TRACKING 008 <<< — Fuzzy decay control flags
        self.skill_level_flag = kwargs.get("skill_level_flag", "neutral")
        # >>> SKILL TRACKING 011 <<< — Emotional & confidence bias
        self.confidence = kwargs.get("confidence", 0.5)   # short-term modifier (0–1)
        # <<< END SKILL TRACKING 011 >>>
        self.last_decay_update = kwargs.get("last_decay_update", datetime.utcnow().isoformat())
        # <<< END SKILL TRACKING 008 >>>

        self.last_recalled = kwargs.get("last_recalled", None)

    # >>> SKILL TRACKING 007 <<< — Fuzzy decay thresholds
    SKILL_THRESHOLDS = {
        "disastrous": 0.0,
        "bad": 0.2,
        "neutral": 0.4,
        "good": 0.6,
        "perfect": 0.8,
        "veteran": 0.95,
    }
    # <<< END SKILL TRACKING 007 >>>

    # --------------------------------------------
    # Memory decay function (called per "story day")
    # --------------------------------------------
    def decay(self, days_passed: int, personality_multiplier: float = 1.0):
        """Soft skill decay with fuzzy plateaus and rebound sensitivity."""
        if self.core_memory:
            return

        # baseline accuracy decay
        decay_rate = 0.0015 * (2.0 - self.importance)
        if self.memorable:
            decay_rate *= 0.5
        # >>> SKILL TRACKING 012 <<< — Negative bias decay modifier
        # Humans remember mistakes longer than successes.
        # Positive emotion: fade slightly faster (don't dwell)
        # Negative emotion: fade slower (stick longer)
        if self.emotion_score > 0:
            emotion_bias = 1.0 + (self.emotion_score * 0.2)   # faster fade for good outcomes
        elif self.emotion_score < 0:
            emotion_bias = max(0.6, 1.0 - abs(self.emotion_score) * 0.4)  # slower fade for failures
        else:
            emotion_bias = 1.0
        # <<< END SKILL TRACKING 012 >>>

        # decay accuracy value
        decay_factor = math.exp(-decay_rate * days_passed * personality_multiplier)
        old_acc = self.accuracy
        self.accuracy = max(0.2, self.accuracy * decay_factor)

        # soft familiarity decay
        loss_factor = 1.0 - (decay_rate * days_passed * personality_multiplier)
        self.familiarity = max(0.0, self.familiarity * loss_factor)

        # slow transitions near plateau edges
        plateau = self.skill_tier()
        lower_bound = self.SKILL_THRESHOLDS[plateau]
        upper_bound = 1.0
        for k, v in self.SKILL_THRESHOLDS.items():
            if v > lower_bound:
                upper_bound = v
                break
        if lower_bound < self.familiarity < upper_bound:
            self.familiarity += 0.02 * (self.familiarity - lower_bound)

        # check for skill-level shift
        new_flag = self.skill_tier()
        if new_flag != self.skill_level_flag:
            print(f"[FUZZY] {self.event_id}: skill level shifted {self.skill_level_flag} → {new_flag}")
            self.skill_level_flag = new_flag

        self.last_decay_update = datetime.utcnow().isoformat()

    # >>> SKILL TRACKING 002 <<<
    def reinforce(self, current_time=None):
        """Increase frequency and update familiarity/skill metric."""
        old_freq = self.frequency_count
        self.frequency_count += 1
        self.familiarity = min(1.0, 0.2 + 0.3 * math.log1p(self.frequency_count))
        if current_time:
            self.last_occurrence = current_time
        print(f"[DEBUG] Reinforced memory {self.event_id}: freq {old_freq}->{self.frequency_count}, familiarity {self.familiarity:.2f}")
        # >>> SKILL TRACKING 010 <<< — Quick rebound if recently decayed
        if self.skill_level_flag != self.skill_tier():
            self.familiarity = min(1.0, self.familiarity + 0.05)
    # <<< END SKILL TRACKING 002 >>>

    # >>> SKILL TRACKING 003 <<<
    def readiness_score(self, personality_multiplier=1.0):
        """Combines familiarity, recency, and personality to estimate preparedness."""
        time_factor = 1.0
        if self.last_occurrence:
            days_since = (datetime.now() - self.last_occurrence).days
            time_factor = max(0.3, min(1.0, 1.0 - 0.01 * days_since))
        score = min(1.0, self.familiarity * personality_multiplier * time_factor)
        return max(0.01, score)
    # <<< END SKILL TRACKING 003 >>>

    def revive(self):
        boost = 0.15
        old_acc = self.accuracy
        self.accuracy = min(1.0, self.accuracy + boost)
        self.last_recalled = datetime.utcnow().isoformat()
        print(f"[DEBUG] Revived memory {self.event_id} ({old_acc:.2f} → {self.accuracy:.2f})")

    # >>> SKILL TRACKING 006 <<< — Optional tier mapping
    def skill_tier(self):
        """Return human-readable skill level name based on familiarity."""
        f = self.familiarity
        if f < 0.2:
            return "disastrous"
        elif f < 0.4:
            return "bad"
        elif f < 0.6:
            return "neutral"
        elif f < 0.8:
            return "good"
        elif f < 0.95:
            return "perfect"
        else:
            return "veteran"

    # >>> SKILL TRACKING 018 <<< — Confidence label helper
    def confidence_label(self):
        """Return a simple qualitative label for confidence."""
        c = self.confidence
        if c < 0.3:
            return "insecure"
        elif c < 0.6:
            return "uncertain"
        elif c < 0.85:
            return "steady"
        else:
            return "assured"
    # <<< END SKILL TRACKING 018 >>>


    def recall(self):
        if self.accuracy >= 0.5:
            return {"summary": self.summary, "tags": self.tags, "clarity": round(self.accuracy, 2)}
        else:
            return {"summary": "The memory feels vague... only fragments remain.",
                    "tags": self.tags[:2], "clarity": round(self.accuracy, 2)}

    def to_dict(self):
        data = self.__dict__.copy()
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


# ============================================================
# ChroniKeeper Memory Engine
# ============================================================
class MemoryEngine:
    def __init__(self, storage_path="memory_data.json", personality_multiplier=1.0):
        self.storage_path = storage_path
        self.memories: Dict[str, MemoryEvent] = {}
        self.personality_multiplier = personality_multiplier
        self.load()

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

    def add_memory(self, event: MemoryEvent):
        self.memories[event.event_id] = event
        print(f"[INFO] Added memory '{event.event_id}' ({event.summary[:40]}...)")
        self.reinforce_by_tags(event.tags, current_time=datetime.now())
        self.save()

    def reinforce_by_tags(self, new_tags, current_time=None):
        matched = []
        for mem in self.memories.values():
            if any(tag in mem.tags for tag in new_tags):
                mem.reinforce(current_time=current_time)
                matched.append(mem.event_id)
        if matched:
            print(f"[INFO] Reinforced memories (skill) by tags: {matched}")
            self.save()
    
        # >>> SKILL TRACKING 017 <<< — Build compact LLM context
    def build_compact_skill_context(self, include_confidence=True):
        """
        Build a single compressed string summarizing all skill memories.
        Keeps prompt size small while preserving tone consistency.
        Example: 'skills: python(good|clear|0.66), guitar(neutral|clear|0.58)'
        """
        parts = []
        for mem in self.memories.values():
            # Skip non-skill memories
            if not any("skill:" in t for t in mem.tags):
                continue

            skill_name = next((t.split(":")[1] for t in mem.tags if "skill:" in t), None)
            if not skill_name:
                continue

            clarity = "clear" if mem.accuracy >= 0.9 else "fuzzy"
            tier = mem.skill_tier()
            if include_confidence:
                parts.append(f"{skill_name}({tier}|{clarity}|{mem.confidence:.2f})")
            else:
                parts.append(f"{skill_name}({tier}|{clarity})")

        if not parts:
            return "skills: none"
        return "skills: " + ", ".join(parts)
    # <<< END SKILL TRACKING 017 >>>


    # --------------------------------------------
    # Recall by tag or fuzzy recall
    # --------------------------------------------
    def recall_by_tag(self, tag: str):
        tag = tag.lower()
        found = [m for m in self.memories.values() if any(tag in t for t in m.tags)]
        if not found:
            print(f"[INFO] No memories with tag '{tag}'.")
            return []

        for m in found:
            m.revive()
        self.save()
        return [m.recall() for m in found]

