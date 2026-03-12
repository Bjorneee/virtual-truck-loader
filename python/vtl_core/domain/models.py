# Item, Container, Placement, Solution (Internal Dataclasses)

from dataclasses import dataclass
from typing import Literal, List, Optional

@dataclass
class Box_t:

    # Identifiers
    id: str
    
    # Dimensions
    width: float
    height: float
    depth: float
    weight: float

    # Config
    priority: Optional[float] = None

    # Methods

    # Returns the volume occupied by Item
    @property
    def volume(self) -> float:
        return self.width * self.depth * self.height
    
    # Returns the floor area occupied by Item
    @property
    def footprint(self) -> float:
        return self.width * self.depth
    
    # Rotates Item 90 degrees along any one axis
    @property
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

@dataclass
class PlacedBox_t:

    # Identifiers
    id: str

    # Position
    x: float
    y: float
    z: float
    rotation: int = 0

@dataclass(frozen=True)
class Truck_t:

    # Identifiers
    id: str

    # Dimensions
    width: float
    height: float
    depth: float
    max_weight: Optional[float] = None

    # Methods

    # Returns inner volume of Container
    @property
    def volume(self) -> float:
        return self.width * self.depth * self.height
    
    @property
    def floor_area(self) -> float:
        return self.width * self.depth
