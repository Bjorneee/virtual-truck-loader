from dataclasses import dataclass, field
from typing import Literal, Optional, List

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

    def __eq__(self, other):
        if not isinstance(other, Box_t):
            return NotImplemented
        return (
            self.width == other.width and
            self.height == other.height and
            self.depth == other.depth
        )

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


### Heuristic Helper Classes

"""
Top-left-origin free rectangle on the truck floor.

Coordinates:
    - x increases left -> right
    - z increases top -> bottom
    - (x, z) is the top-left corner of the free rectangle
"""
@dataclass
class FreeRectTL:

    x: float
    z: float
    w: float
    d: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.z + self.d
    

@dataclass
class SkylineSeg:
    x: float
    z: float
    w: float