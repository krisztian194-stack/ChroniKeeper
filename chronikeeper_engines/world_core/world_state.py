# ============================================================
# ChroniKeeper – WorldState
# Central world data container synced with EnvironmentEngine
# ============================================================

from dataclasses import dataclass, field

@dataclass
class WorldState:
    """
    Holds all persistent or shared data for the simulation world.
    The EnvironmentEngine manages time, season, and atmosphere;
    this class only caches and exposes those results.
    """

    environment_engine: object = None
    world_name: str = "Default World"
    player_name: str = "Player"
    climatic_zone: str = "temperate"
    hemisphere: str = "north"
    location_id: str = "city_center"

    # Core data stores
    environment_signature: dict = field(default_factory=dict)
    relationships: dict = field(default_factory=dict)
    inventory: list = field(default_factory=lambda: ["watch"])
    flags: dict = field(default_factory=dict)

    # ========================================================
    # === Environment integration ===
    # ========================================================

    def sync_with_environment(self):
        """Pull the latest environment signature from the EnvironmentEngine."""
        if not self.environment_engine:
            raise RuntimeError("WorldState: No EnvironmentEngine attached.")
        sig = self.environment_engine.update(self)
        self.environment_signature = sig
        return sig

    def advance_time(self, hours: float = 1.0):
        """Advance world time by N hours and refresh environment signature."""
        if not self.environment_engine:
            raise RuntimeError("WorldState: No EnvironmentEngine attached.")
        self.environment_engine.advance_time(hours)
        return self.sync_with_environment()

    def get_time_status(self) -> dict:
        """Expose current time information for other systems."""
        if not self.environment_engine:
            return {}
        return self.environment_engine.get_time_status()

    def get_season(self) -> str:
        """Expose current season."""
        if not self.environment_engine:
            return "unknown"
        return self.environment_engine.get_season()

    # ========================================================
    # === Convenience / utilities ===
    # ========================================================

    def describe_time(self) -> str:
        """Readable summary of current world time and season."""
        t = self.get_time_status()
        if not t:
            return "Time data unavailable"
        return f"Day {t['day']} ({t['hour']:.1f}h), Month {t['month']}, Season: {self.get_season().capitalize()}"

    def describe_environment(self) -> str:
        """Readable short text for prompts or debugging."""
        sig = self.environment_signature or {}
        if not sig:
            return "Environment not initialized"
        return (
            f"T:{sig.get('temperature', 0.5):.2f}, "
            f"H:{sig.get('humidity', 0.5):.2f}, "
            f"C:{sig.get('comfort', 0.5):.2f}, "
            f"AQ:{sig.get('air_quality', 0.5):.2f}, "
            f"Vis:{sig.get('visibility', 0.5):.2f}"
        )

    def set_location(self, location_id: str):
        """Move player/agent to another known map area."""
        self.location_id = location_id
        self.flags["last_moved"] = self.get_time_status().get("hour", 0)

    # ========================================================
    # === Serialization / persistence placeholders ===
    # ========================================================

    def to_dict(self) -> dict:
        """Serialize world data for saving."""
        return {
            "world_name": self.world_name,
            "player_name": self.player_name,
            "climatic_zone": self.climatic_zone,
            "hemisphere": self.hemisphere,
            "location_id": self.location_id,
            "environment_signature": self.environment_signature,
            "inventory": self.inventory,
            "flags": self.flags,
            "relationships": self.relationships,
        }

    @classmethod
    def from_dict(cls, data: dict, environment_engine=None):
        """Recreate a world state from saved JSON/dict."""
        ws = cls(environment_engine=environment_engine)
        for k, v in data.items():
            if hasattr(ws, k):
                setattr(ws, k, v)
        return ws
