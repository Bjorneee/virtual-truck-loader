from scene.primitives import create_box
from utils.helpers import color_from_id

def spawn_box(render, box_data, box_specs):

    width = box_specs["width"]
    height = box_specs["height"]
    depth = box_specs["depth"]

    x = box_data["x"] + width / 2
    y = box_data["y"] + height / 2
    z = box_data["z"] + depth / 2

    # Main Box
    box = create_box(width, height, depth)
    
    # IMPORTANT: Panda3D positions from CENTER, not corner
    box.setPos(x, y, z)
    box.setColor(color_from_id(box_data["id"]))
    box.reparentTo(render)

    # Outline
    outline = create_box(width, height, depth)
    outline.setPos(x, y, z)
    outline.setScale(1.001, 1.001, 1.001)
    outline.setRenderModeWireframe()
    outline.setLightOff()
    outline.setColor(0, 0, 0, 1)
    outline.setDepthWrite(False)
    outline.reparentTo(render)

    return box

def load_boxes(render, boxes, box_specs):
    nodes = []

    box_map = {b["id"]: b for b in box_specs}

    for b in boxes:

        matching = box_map.get(b["id"])
        if matching is None:
            raise ValueError(f"Response Box cannot be mapped to a valid request box\n")
        
        node = spawn_box(render, b, matching)
        nodes.append(node)

    return nodes