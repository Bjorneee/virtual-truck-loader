from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties

from vconfig import (
    WINDOW_TITLE,
    BACKGROUND_COLOR,
    GRID_SIZE,
    GRID_STEP,
    GROUND_SIZE
)
from camera.camera import OrbitCameraController
from scene.lighting import setup_lighting
from scene.grid import create_grid
from scene.ground import create_ground_plane

from .loader import load_boxes, spawn_truck
from .api_client import fetch_packing_result
from utils.json_loader import load_payload_from_file

class SimpleSceneViewer(ShowBase):
    def __init__(self, input_json_path: str):
        super().__init__()

        self.disableMouse()
        self._setup_window()

        self.input_json_path = input_json_path
        self.render.setShaderAuto()

        setup_lighting(self.render)

        ground = create_ground_plane(GROUND_SIZE)
        ground.setHpr(0, -90, 0)  # make X-Z ground plane
        ground.setPos(0, 0, 0)
        ground.setColor(0.32, 0.33, 0.35, 1.0)
        ground.reparentTo(self.render)

        grid = create_grid(GRID_SIZE, GRID_STEP)
        grid.setHpr(0, -90, 0)
        grid.setPos(0, 0.001, 0)
        grid.reparentTo(self.render)

        self.camera_controller = OrbitCameraController(
            base=self,
            camera=self.camera,
            render=self.render,
        )

        self.box_nodes = []
        self.truck_nodes = []
        self.load_from_api()

    def _setup_window(self):
        props = WindowProperties()
        props.setTitle(WINDOW_TITLE)
        self.win.requestProperties(props)
        self.setBackgroundColor(*BACKGROUND_COLOR)

    def clear_load(self):
        for node in self.box_nodes:
            node.removeNode()
        self.box_nodes.clear()

    def load_from_api(self):

        try:
            payload = load_payload_from_file(self.input_json_path)

            result = fetch_packing_result("http://127.0.0.1:8000/pack", payload)
            self.clear_load()

            self.truck_nodes = spawn_truck(self.render, payload["truck"])
            self.box_nodes = load_boxes(self.render, result["placed"], payload["boxes"])

            print("Truck: ", payload["truck"].get("id"))
            print("Utilization: ", result.get("utilization"))
            print("Notes: ", result.get("notes"))
        
        except Exception as e:
            print("Failed to load from API: ", e)
