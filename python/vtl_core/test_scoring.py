from engine import ScoringEngine

# Initialize truck: 10 units long, 8 wide, 8 high
vtl_engine = ScoringEngine(truck_dims=(10, 8, 8))

# Test Case 1: A stable, balanced layout
good_layout = [
    {'l': 5, 'w': 4, 'h': 2, 'x': 0, 'y': 0, 'z': 0, 'mass': 100, 'supported_area': 20},
    {'l': 5, 'w': 4, 'h': 2, 'x': 5, 'y': 4, 'z': 0, 'mass': 100, 'supported_area': 20}
]

# Test Case 2: An unstable, unbalanced layout (Floating box + All weight on one side)
bad_layout = [
    {'l': 2, 'w': 2, 'h': 2, 'x': 0, 'y': 0, 'z': 0, 'mass': 500, 'supported_area': 4},
    {'l': 2, 'w': 2, 'h': 2, 'x': 0, 'y': 2, 'z': 5, 'mass': 10, 'supported_area': 0} # Floating!
]

print(f"Good Layout Score: {vtl_engine.get_total_score(good_layout)}")
print(f"Bad Layout Score: {vtl_engine.get_total_score(bad_layout)}")