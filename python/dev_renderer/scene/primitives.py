from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    NodePath,
)

def create_box(width, height, depth):
    hx = width / 2.0
    hy = height / 2.0
    hz = depth / 2.0

    fmt = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData("box", fmt, Geom.UHStatic)

    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")

    # Faces: (normal, vertices)
    faces = [
        # Front (−Y)
        ((0, -1, 0), [(-hx, -hy, -hz), (hx, -hy, -hz),
                      (hx, -hy,  hz), (-hx, -hy,  hz)]),

        # Back (+Y)
        ((0, 1, 0), [(-hx, hy, -hz), (-hx, hy,  hz),
                     (hx, hy,  hz), (hx, hy, -hz)]),

        # Left (−X)
        ((-1, 0, 0), [(-hx, -hy, -hz), (-hx, -hy,  hz),
                      (-hx,  hy,  hz), (-hx,  hy, -hz)]),

        # Right (+X)
        ((1, 0, 0), [(hx, -hy, -hz), (hx,  hy, -hz),
                     (hx,  hy,  hz), (hx, -hy,  hz)]),

        # Bottom (−Z)
        ((0, 0, -1), [(-hx, -hy, -hz), (-hx,  hy, -hz),
                      (hx,  hy, -hz), (hx, -hy, -hz)]),

        # Top (+Z)
        ((0, 0, 1), [(-hx, -hy, hz), (hx, -hy, hz),
                     (hx,  hy, hz), (-hx,  hy, hz)]),
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

    node = GeomNode("box")
    node.addGeom(geom)

    return NodePath(node)

def create_box_outline(width, height, depth):
    hx = width / 2.0
    hy = height / 2.0
    hz = depth / 2.0

    fmt = GeomVertexFormat.getV3()
    vdata = GeomVertexData("box_outline", fmt, Geom.UHStatic)
    vertex = GeomVertexWriter(vdata, "vertex")

    # 8 corners of the box
    corners = [
        (-hx, -hy, -hz),
        ( hx, -hy, -hz),
        ( hx,  hy, -hz),
        (-hx,  hy, -hz),
        (-hx, -hy,  hz),
        ( hx, -hy,  hz),
        ( hx,  hy,  hz),
        (-hx,  hy,  hz),
    ]

    for c in corners:
        vertex.addData3(*c)

    lines = GeomLines(Geom.UHStatic)

    edges = [
        (0,1),(1,2),(2,3),(3,0),  # bottom
        (4,5),(5,6),(6,7),(7,4),  # top
        (0,4),(1,5),(2,6),(3,7)   # verticals
    ]

    for a, b in edges:
        lines.addVertices(a, b)

    geom = Geom(vdata)
    geom.addPrimitive(lines)

    node = GeomNode("box_outline")
    node.addGeom(geom)

    return NodePath(node)