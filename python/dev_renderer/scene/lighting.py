from panda3d.core import AmbientLight, DirectionalLight
from vconfig import AMBIENT_COLOR, SUN_COLOR, SUN_HPR


def setup_lighting(render):
    ambient = AmbientLight("ambient")
    ambient.setColor(AMBIENT_COLOR)
    ambient_np = render.attachNewNode(ambient)
    render.setLight(ambient_np)

    sun = DirectionalLight("sun")
    sun.setColor(SUN_COLOR)
    sun_np = render.attachNewNode(sun)
    sun_np.setHpr(*SUN_HPR)
    render.setLight(sun_np)