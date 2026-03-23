from panda3d.core import NodePath
from scene.primitives import create_box
import utils.helpers as BoxUtils

def spawn_box(render, box_data, box_specs):

    width = box_specs["width"]
    height = box_specs["height"]
    depth = box_specs["depth"]

    x = box_data["x"] + width / 2
    y = box_data["y"] + height / 2
    z = box_data["z"] + depth / 2

    group = NodePath(f"box_{box_data['id']}")
    group.setPos(x, y, z)                         # IMPORTANT: Panda3D positions from CENTER, not corner
    group.reparentTo(render)

    # Main Box
    box = create_box(width, height, depth)
    box.setColor(BoxUtils.color_from_id(box_data["id"]))
    box.reparentTo(group)

    # Outline
    outline = create_box(width, height, depth)
    outline.setScale(1.001, 1.001, 1.001)
    outline.setRenderModeWireframe()
    outline.setRenderModeThickness(2)
    outline.setLightOff()
    outline.setColor(0, 0, 0, 1)
    outline.setDepthWrite(False)
    outline.reparentTo(group)

    BoxUtils.attach_labels_to_box_faces(group, box_data["id"], width, height, depth)

    return group

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