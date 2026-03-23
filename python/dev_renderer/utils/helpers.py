import hashlib

from panda3d.core import NodePath, TextNode


def create_face_label(text, scale=0.2):
    text_node = TextNode("face_label")
    text_node.setText(text)
    text_node.setAlign(TextNode.ACenter)

    text_node.setTextColor(1, 1, 1, 1)
    text_node.setCardColor(0, 0, 0, 0.25)
    text_node.setCardAsMargin(0.5, 0.5, 0.25, 0.25)

    label = NodePath(text_node.generate())
    label.setScale(scale)
    label.setLightOff()
    label.setTwoSided(True)
    label.setDepthWrite(False)
    label.setBin("fixed", 0)
    return label


def attach_labels_to_box_faces(parent, box_id, width, height, depth):
    eps = 0.01
    scale = max(0.12, min(0.28, min(width, height, depth) * 0.22))

    labels = []

    # Front (+Z)
    front = create_face_label(box_id, scale)
    front.setPos(0, 0, depth / 2.0 + eps)
    front.setHpr(0, -90, 0)
    labels.append(front)

    # Back (-Z)
    back = create_face_label(box_id, scale)
    back.setPos(0, 0, -depth / 2.0 - eps)
    back.setHpr(180, 90, 0)
    labels.append(back)

    # Right (+X)
    right = create_face_label(box_id, scale)
    right.setPos(width / 2.0 + eps, 0, 0)
    right.setHpr(-90, 180, -90)
    labels.append(right)

    # Left (-X)
    left = create_face_label(box_id, scale)
    left.setPos(-width / 2.0 - eps, 0, 0)
    left.setHpr(90, 180, 90)
    labels.append(left)

    # Top (+Y)
    top = create_face_label(box_id, scale)
    top.setPos(0, height / 2.0 + eps, 0)
    top.setHpr(0, 180, 0)
    labels.append(top)

    # Bottom (-Y)
    bottom = create_face_label(box_id, scale)
    bottom.setPos(0, -height / 2.0 - eps, 0)
    bottom.setHpr(0, 0, 0)
    labels.append(bottom)

    for label in labels:
        label.reparentTo(parent)


def color_from_id(box_id: str):
    digest = hashlib.md5(box_id.encode("utf-8")).digest()
    r = 0.35 + (digest[0] / 255.0) * 0.55
    g = 0.35 + (digest[1] / 255.0) * 0.55
    b = 0.35 + (digest[2] / 255.0) * 0.55
    return (r, g, b, 1.0)