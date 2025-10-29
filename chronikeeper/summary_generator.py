# Placeholder for LLM integration
class SummaryGenerator:
    def __init__(self, max_words=200):
        self.max_words = max_words

    def generate_summary(self, events):
        """
        events: list of dicts from MemoryEngine
        returns: short summary string
        """
        key_points = [e["description"] for e in events[-10:]]  # last 10 events
        summary = " ".join(key_points)
        words = summary.split()
        if len(words) > self.max_words:
            summary = " ".join(words[-self.max_words:])
        return summary
