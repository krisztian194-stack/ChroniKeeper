from __future__ import annotations

# ============================================================
# ChroniKeeper – Prompt Manager
# Orchestrates all components into final LLM prompt contexts.
# ============================================================

from chronikeeper_engines.simulation_core.character_state_engine import CharacterStateEngine
from chronikeeper_engines.world_core.world_state import WorldState
from chronikeeper_engines.prompt_core.util_summary import SummaryGenerator
from chronikeeper_engines.prompt_core.util_language import LanguageLookup


class PromptManager:
    """Central manager that composes world + memory + character data into compact LLM prompts."""

    def __init__(self, char_engine: CharacterStateEngine, world: WorldState, lang="en"):
        self.engine = char_engine
        self.world = world
        self.lang = lang
        self.summarizer = SummaryGenerator(language=lang)
        self.translator = LanguageLookup(default_lang=lang)

    def build_context(self):
        """Generate a short prompt context summarizing the current world and character state."""
        events = getattr(self.engine, "memory_buffer", [])
        summary = self.summarizer.generate_summary(events)
        world_state = getattr(self.world, "environment_signature", {})

        # Safe hour handling
        hour_val = world_state.get("hour", 0)
        try:
            hour_val = float(hour_val)
        except (ValueError, TypeError):
            hour_val = 0.0

        context = (
            f"World time: {hour_val:05.2f}h, "
            f"Season: {world_state.get('season', 'unknown')}. "
            f"Character mood: {getattr(self.engine, 'current_mood', 0.5):.2f}. "
            f"Recent events: {summary}"
        )
        return self.translator.apply_contextual_slang(
            context, getattr(self.world, "world_type", "general")
        )

    def build_instruction_prompt(self, player_input: str):
        """Generate final formatted LLM prompt from world + player + summary."""
        base_context = self.build_context()
        formatted = (
            f"[CONTEXT]\n{base_context}\n\n"
            f"[PLAYER INPUT]\n{player_input.strip()}\n\n"
            f"[EXPECTED OUTPUT]\nContinue story realistically, "
            f"keeping consistency with past events."
        )
        return formatted
