# Item, Container, Placement, Solution (Internal Dataclasses)

from dataclasses import dataclass
from utils import swap

@dataclass
class Item:

    # Identifiers
    id: str
    name: str
    sku: int
    tags: list[str]
    stackable: bool = False

    # Dimensions
    width: float
    depth: float
    height: float
    weight: float

    # Returns the volume occupied by Item
    def volume(self) -> float:
        return self.width * self.depth * self.height
    
    # Returns the floor area occupied by Item
    def footprint(self) -> float:
        return self.width * self.depth
    
    # Rotates Item 90 degrees along any one axis
    def rotate(self, axis: {'x', 'y', 'z'}):
        match axis:
            case 'x':
                swap(self.depth, self.height)
                return
            case 'y':
                swap(self.depth, self.width)
                return
            case 'z':
                swap(self.height, self.width)
                return

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