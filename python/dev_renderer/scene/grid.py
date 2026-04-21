from panda3d.core import (
    Geom,
    GeomLines,
    GeomNode,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    NodePath,
)


def create_grid(size=20, step=1):
    fmt = GeomVertexFormat.getV3()
    vdata = GeomVertexData("grid", fmt, Geom.UHStatic)
    vertex = GeomVertexWriter(vdata, "vertex")

    lines = GeomLines(Geom.UHStatic)
    half = size / 2
    index = 0

    for i in range(-size // 2, size // 2 + 1, step):
        vertex.addData3(i, -half, 0.001)
        vertex.addData3(i, half, 0.001)
        lines.addVertices(index, index + 1)
        index += 2

        vertex.addData3(-half, i, 0.001)
        vertex.addData3(half, i, 0.001)
        lines.addVertices(index, index + 1)
        index += 2

    geom = Geom(vdata)
    geom.addPrimitive(lines)

    node = GeomNode("grid")
    node.addGeom(geom)

    np = NodePath(node)
    np.setColor(0.52, 0.54, 0.57, 1.0)
    np.setLightOff()
    return np