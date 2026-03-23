from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties

from vconfig import (
    WINDOW_TITLE,
    BACKGROUND_COLOR,
    GRID_SIZE,
    GRID_STEP,
    GROUND_SIZE,
    CUBE_SIZE,
    CUBE_COLOR,
    CUBE_POS,
)
from camera.camera import OrbitCameraController
from scene.lighting import setup_lighting
from scene.grid import create_grid
from scene.ground import create_ground_plane
from scene.primitives import create_cube


class SimpleSceneViewer(ShowBase):
    def __init__(self):
        super().__init__()

        self.disableMouse()
        self._setup_window()

        self.render.setShaderAuto()

        setup_lighting(self.render)

        ground = create_ground_plane(GROUND_SIZE)
        ground.reparentTo(self.render)
        ground.setColor(0.32, 0.33, 0.35, 1.0)

        grid = create_grid(GRID_SIZE, GRID_STEP)
        grid.reparentTo(self.render)

        cube = create_cube(CUBE_SIZE)
        cube.reparentTo(self.render)
        cube.setPos(*CUBE_POS)
        cube.setColor(*CUBE_COLOR)

        self.camera_controller = OrbitCameraController(
            base=self,
            camera=self.camera,
            render=self.render,
        )

    def _setup_window(self):
        props = WindowProperties()
        props.setTitle(WINDOW_TITLE)
        self.win.requestProperties(props)
        self.setBackgroundColor(*BACKGROUND_COLOR)