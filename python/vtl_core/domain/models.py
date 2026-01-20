# Item, Container, Placement, Solution (Internal Dataclasses)

from dataclasses import dataclass
from typing import Literal

@dataclass
class Item:

    # Identifiers
    id: str
    name: str
    sku: int
    tags: list[str]

    # Dimensions
    width: float
    depth: float
    height: float
    weight: float

    # Config
    stackable: bool = False

    # Returns the volume occupied by Item
    def volume(self) -> float:
        return self.width * self.depth * self.height
    
    # Returns the floor area occupied by Item
    def footprint(self) -> float:
        return self.width * self.depth
    
    # Rotates Item 90 degrees along any one axis
    def rotate(self, axis: Literal['x', 'y', 'z']):
        match axis:
            case 'x':
                self.depth, self.height = self.height, self.depth
                return
            case 'y':
                self.depth, self.width = self.width, self.depth
                return
            case 'z':
                self.height, self.width = self.width, self.height
                return
            case _:
                raise ValueError(f"Invalid axis: {axis!r}")

@dataclass(frozen=True)
class Container:

    # Identifiers
    id: str
    name: str

    # Dimensions
    width: float
    depth: float
    height: float
    capacity: float

    # Returns inner volume of Container
    def volume(self) -> float:
        return self.width * self.depth * self.height