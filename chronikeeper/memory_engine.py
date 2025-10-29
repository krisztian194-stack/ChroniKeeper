import json
import os
from datetime import datetime

MEMORY_FILE = "chronikeeper_memory.json"

class MemoryEngine:
    def __init__(self):
        self.memory = {"characters": {}, "world": {}, "events": []}
        self.load_memory()

    def load_memory(self):
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                self.memory = json.load(f)

    def save_memory(self):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)

    # Character memory
    def update_character(self, char_id, key, value):
        if char_id not in self.memory["characters"]:
            self.memory["characters"][char_id] = {}
        self.memory["characters"][char_id][key] = value
        self.save_memory()

    def get_character(self, char_id):
        return self.memory["characters"].get(char_id, {})

    # World memory
    def update_world(self, key, value):
        self.memory["world"][key] = value
        self.save_memory()

    def get_world(self, key):
        return self.memory["world"].get(key, None)

    # Event logging
    def log_event(self, description, char_id=None, points=0):
        event = {
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "char_id": char_id,
            "points": points
        }
        self.memory["events"].append(event)
        self.save_memory()
