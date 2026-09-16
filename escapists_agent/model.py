from dataclasses import dataclass, field
from typing import Protocol
import numpy as np


@dataclass
class Observation:
    timestamp: float
    player: tuple[int, int] | None
    confidence: float
    state: str
    reason: str
    entities: list[dict] = field(default_factory=list)
    inventory: list[str] = field(default_factory=list)
    schedule: str | None = None


@dataclass
class Action:
    key: str | None
    duration: float
    reason: str


class Perception(Protocol):
    def observe(self, frame: np.ndarray, timestamp: float) -> Observation: ...


class Policy(Protocol):
    def decide(self, observation: Observation) -> Action: ...


class Controller(Protocol):
    def perform(self, action: Action, timestamp: float) -> None: ...
