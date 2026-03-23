from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    NodePath,
)


def create_cube(size=1.0):
    half = size / 2.0

    fmt = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData("cube", fmt, Geom.UHStatic)

    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")

    faces = [
        ((0, -1, 0), [(-half, -half, -half), (half, -half, -half),
                      (half, -half, half), (-half, -half, half)]),
        ((0, 1, 0), [(-half, half, -half), (-half, half, half),
                     (half, half, half), (half, half, -half)]),
        ((-1, 0, 0), [(-half, -half, -half), (-half, -half, half),
                      (-half, half, half), (-half, half, -half)]),
        ((1, 0, 0), [(half, -half, -half), (half, half, -half),
                     (half, half, half), (half, -half, half)]),
        ((0, 0, -1), [(-half, -half, -half), (-half, half, -half),
                      (half, half, -half), (half, -half, -half)]),
        ((0, 0, 1), [(-half, -half, half), (half, -half, half),
                     (half, half, half), (-half, half, half)]),
    ]

    for n, verts in faces:
        for v in verts:
            vertex.addData3(*v)
            normal.addData3(*n)

    tris = GeomTriangles(Geom.UHStatic)
    for i in range(0, 24, 4):
        tris.addVertices(i, i + 1, i + 2)
        tris.addVertices(i, i + 2, i + 3)

    geom = Geom(vdata)
    geom.addPrimitive(tris)

    node = GeomNode("cube")
    node.addGeom(geom)
    return NodePath(node)