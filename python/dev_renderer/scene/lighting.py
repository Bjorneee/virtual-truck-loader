from panda3d.core import AmbientLight, DirectionalLight, Point3
from vconfig import AMBIENT_COLOR, SUN_COLOR, SUN_HPR


def setup_lighting(render):
    ambient = AmbientLight("ambient")
    ambient.setColor((0.45, 0.45, 0.48, 1.0))
    ambient_np = render.attachNewNode(ambient)
    render.setLight(ambient_np)

    sun = DirectionalLight("sun")
    sun.setColor((0.95, 0.95, 0.90, 1.0))
    sun_np = render.attachNewNode(sun)

    # Put the light "above" the scene in +Y, then aim toward origin
    sun_np.setPos(10, 20, -10)
    sun_np.lookAt(Point3(0, 0, 0), Point3(0, 1, 0))

    render.setLight(sun_np)