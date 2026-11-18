"""
World schema (pydantic edge): the shape and cross-references of world data. No file I/O here.
"""

from typing import Annotated, Literal, Self

from pydantic import Field, StrictInt, model_validator

from ml_based_strategies.domain.spec_model import SpecModel


class Location(SpecModel):
    id: str
    name: str
    kind: str
    x: float
    y: float
    owner: str | None = None
    protected: bool = False


class Faction(SpecModel):
    id: str
    name: str
    color: str
    allowed: frozenset[str] = frozenset()


class Edge(SpecModel):
    a: str
    b: str
    cost: Annotated[StrictInt, Field(gt=0)]  # travel cost in time points

    @model_validator(mode="after")
    def _no_self_loop(self) -> Self:
        if self.a == self.b:
            # !r - repr quoting
            raise ValueError(f"path {self.a!r}-{self.b!r} is a self-loop")
        return self


class Threat(SpecModel):
    """
    Something dangerous at a location, independent of who owns it. Kinds are fixed: sim logic branches on them.
    """

    id: str
    location: str
    kind: Literal["anomaly", "monsters", "trap"]
    level: Annotated[StrictInt, Field(ge=1, le=5)]


def build_adjacency(loc_ids_lst: list[str], paths_lst: list[Edge]) -> dict[str, dict[str, int]]:
    """
    Recreate adjacency from configured paths.
    """
    adjacency_dict: dict[str, dict[str, int]] = {loc_id: {} for loc_id in loc_ids_lst}
    for p in paths_lst:
        adjacency_dict[p.a][p.b] = adjacency_dict[p.b][p.a] = p.cost
    return adjacency_dict


class World(SpecModel):
    """
    Schema of a whole world (its files merged); cross-file references and connectivity are checked here.
    """

    factions: list[Faction]
    locations: list[Location]
    paths: list[Edge]
    threats: list[Threat] = []  # initial contents; optional so plain maps still load

    @model_validator(mode="after")
    def _check_graph(self) -> Self:
        for el_type, items_lst in (("faction", self.factions), ("location", self.locations), ("threat", self.threats)):
            seen_set: set[str] = set()
            for item in items_lst:
                if item.id in seen_set:
                    raise ValueError(f"duplicate {el_type} id: {item.id!r}")
                seen_set.add(item.id)

        faction_ids_set = {f.id for f in self.factions}
        for loc in self.locations:
            if loc.owner is not None and loc.owner not in faction_ids_set:
                raise ValueError(f"location {loc.id!r} has unknown owner {loc.owner!r}")

        loc_ids_lst = [loc.id for loc in self.locations]
        for p in self.paths:
            if p.a not in loc_ids_lst or p.b not in loc_ids_lst:
                raise ValueError(f"path {p.a!r}-{p.b!r} references an unknown location")
        for t in self.threats:
            if t.location not in loc_ids_lst:
                raise ValueError(f"threat {t.id!r} references unknown location {t.location!r}")

        if loc_ids_lst:
            adjacency_dict = build_adjacency(loc_ids_lst, self.paths)
            reached_set, stack_lst = {loc_ids_lst[0]}, [loc_ids_lst[0]]
            while stack_lst:
                for n in adjacency_dict[stack_lst.pop()]:
                    if n not in reached_set:
                        reached_set.add(n)
                        stack_lst.append(n)
            if missing_set := set(loc_ids_lst) - reached_set:
                raise ValueError(f"world graph is disconnected; unreachable: {sorted(missing_set)}")
        return self
