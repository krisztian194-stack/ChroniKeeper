# ============================================================
# ChroniKeeper – Language Utility Module (Localization + Slang)
# ============================================================

import os, json
from chronikeeper_engines.core_paths import DATA_ROOT

class LanguageLookup:
    """Handles translation, slang filtering, and context-specific phrasing."""

    def __init__(self, lookup_path=None, default_lang="en"):
        self.lookup_path = lookup_path or os.path.join(DATA_ROOT, "language", "tag_map.json")
        self.default_lang = default_lang
        self.cache = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.lookup_path):
            print(f"[WARN] Missing translation file: {self.lookup_path}")
            self.translations = {}
            return
        try:
            with open(self.lookup_path, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        except Exception as e:
            print("[ERROR] Failed to load translation map:", e)
            self.translations = {}

    # --- Translation ---
    def translate_tag(self, tag: str, from_lang="en", to_lang=None):
        """Translate tags or keywords using a simple dictionary map."""
        to_lang = to_lang or self.default_lang
        if from_lang == to_lang:
            return tag
        return self.translations.get(to_lang, {}).get(tag, tag)

    # --- Slang Adaptation ---
    def apply_contextual_slang(self, text: str, context: str) -> str:
        """
        Replace words based on thematic context, to avoid immersion breaks.
        Example: 'detective' → 'gumshoe' in mystery worlds.
        """
        slang_map = {}
        if "mystery" in context.lower():
            slang_map.update({"police": "coppers", "detective": "gumshoe", "criminal": "perp"})
        elif "sci-fi" in context.lower():
            slang_map.update({"computer": "terminal", "robot": "drone"})
        elif "fantasy" in context.lower():
            slang_map.update({"money": "gold", "police": "guards"})
        for k, v in slang_map.items():
            text = text.replace(k, v)
        return text
