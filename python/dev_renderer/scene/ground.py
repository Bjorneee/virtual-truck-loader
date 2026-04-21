from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    NodePath,
)


def create_ground_plane(size=20):
    half = size / 2.0
    fmt = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData("ground", fmt, Geom.UHStatic)

    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")

    verts = [
        (-half, -half, 0),
        (half, -half, 0),
        (half, half, 0),
        (-half, half, 0),
    ]

    for v in verts:
        vertex.addData3(*v)
        normal.addData3(0, 0, 1)

    tris = GeomTriangles(Geom.UHStatic)
    tris.addVertices(0, 1, 2)
    tris.addVertices(0, 2, 3)

    geom = Geom(vdata)
    geom.addPrimitive(tris)

    node = GeomNode("ground")
    node.addGeom(geom)
    return NodePath(node)