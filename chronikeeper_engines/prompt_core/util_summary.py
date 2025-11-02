# ============================================================
# ChroniKeeper – Summary Utility (Memory / Event Compression)
# ============================================================

from chronikeeper_engines.prompt_core.util_language import LanguageLookup

class SummaryGenerator:
    """Generates short summaries from recent character or world events."""

    def __init__(self, max_words=200, language="en"):
        self.max_words = max_words
        self.language = language
        self.translator = LanguageLookup()

    def generate_summary(self, events):
        """Create a compact text summary for prompt injection."""
        if not events:
            return "No significant recent events."
        key_points = [
            self.translator.translate_tag(e.get("summary", ""), "en", self.language)
            for e in events[-10:]
        ]
        combined = " ".join(key_points)
        words = combined.split()
        if len(words) > self.max_words:
            combined = " ".join(words[-self.max_words:])
        return combined.strip()
