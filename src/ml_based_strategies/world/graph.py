"""
Runtime world graph used by the sim: holds already-validated models, no validation runs here.
"""

from dataclasses import dataclass

from ml_based_strategies.world.schema import Faction, Location, Threat


@dataclass(frozen=True)
class World:
    locations_dict: dict[str, Location]
    factions_dict: dict[str, Faction]
    adjacency_dict: dict[str, dict[str, int]]  # loc id -> {neighbor id: travel cost in time points}
    threats_dict: dict[str, Threat]  # starting contents only; the future sim/ state owns the mutable copy

    def threats_at(self, loc_id: str) -> list[Threat]:
        return [t for t in self.threats_dict.values() if t.location == loc_id]

    def neighbors(self, loc_id: str) -> dict[str, int]:
        return self.adjacency_dict[loc_id]

    def can_enter(self, faction_id: str, loc_id: str) -> bool:
        """
        Action mask: a faction may enter a location if allowed, and protected ground only if it owns it.
        """
        loc = self.locations_dict[loc_id]
        faction = self.factions_dict[faction_id]
        if loc.protected and loc.owner != faction_id:
            return False
        return loc.kind in faction.allowed_kinds or loc.id in faction.allowed_ids
