from math import cos, radians, sin
from panda3d.core import Point3, Vec3
from direct.task import Task

from vconfig import (
    CAM_TARGET,
    CAM_DISTANCE,
    CAM_YAW,
    CAM_PITCH,
    CAM_MIN_PITCH,
    CAM_MAX_PITCH,
)


class OrbitCameraController:
    def __init__(self, base, camera, render):
        self.base = base
        self.camera = camera
        self.render = render

        self.target = Point3(*CAM_TARGET)
        self.cam_distance = CAM_DISTANCE
        self.cam_yaw = CAM_YAW
        self.cam_pitch = CAM_PITCH

        self.min_pitch = CAM_MIN_PITCH
        self.max_pitch = CAM_MAX_PITCH

        self.mouse_last = None
        self.rotating = False
        self.panning = False

        self._bind_inputs()
        self.base.taskMgr.add(self.update_camera, "update_camera")
        self.update_camera_position()

    def _bind_inputs(self):
        self.base.accept("mouse1", self.start_rotate)
        self.base.accept("mouse1-up", self.stop_rotate)
        self.base.accept("mouse3", self.start_pan)
        self.base.accept("mouse3-up", self.stop_pan)
        self.base.accept("wheel_up", self.zoom_in)
        self.base.accept("wheel_down", self.zoom_out)
        self.base.accept("+", self.zoom_in)
        self.base.accept("-", self.zoom_out)
        self.base.accept("escape", self.base.userExit)

    def start_rotate(self):
        self.rotating = True
        self.mouse_last = None

    def stop_rotate(self):
        self.rotating = False
        self.mouse_last = None

    def start_pan(self):
        self.panning = True
        self.mouse_last = None

    def stop_pan(self):
        self.panning = False
        self.mouse_last = None

    def zoom_in(self):
        self.cam_distance = max(2.0, self.cam_distance - 0.6)

    def zoom_out(self):
        self.cam_distance = min(50.0, self.cam_distance + 0.6)

    def update_camera(self, task):
        if self.base.mouseWatcherNode.hasMouse():
            mouse = self.base.mouseWatcherNode.getMouse()
            current = (mouse.getX(), mouse.getY())

            if self.mouse_last is None:
                self.mouse_last = current
                return Task.cont

            dx = current[0] - self.mouse_last[0]
            dy = current[1] - self.mouse_last[1]
            self.mouse_last = current

            if self.rotating:
                self.cam_yaw += dx * 120.0
                self.cam_pitch += dy * 90.0
                self.cam_pitch = max(
                    self.min_pitch,
                    min(self.max_pitch, self.cam_pitch)
                )

            elif self.panning:
                pan_speed = self.cam_distance * 0.0035

                cam_right = self.camera.getQuat(self.render).getRight()
                cam_up = self.camera.getQuat(self.render).getUp()

                self.target -= cam_right * (dx * 100.0 * pan_speed)
                self.target -= cam_up * (dy * 100.0 * pan_speed)
        else:
            self.mouse_last = None

        self.update_camera_position()
        return Task.cont

    def update_camera_position(self):
        yaw_rad = radians(self.cam_yaw)
        pitch_rad = radians(self.cam_pitch)

        # Y-up orbit:
        # x = horizontal left/right
        # y = vertical
        # z = depth forward/back
        x = self.target.x + self.cam_distance * cos(pitch_rad) * sin(yaw_rad)
        y = self.target.y + self.cam_distance * sin(pitch_rad)
        z = self.target.z - self.cam_distance * cos(pitch_rad) * cos(yaw_rad)

        self.camera.setPos(x, y, z)
        self.camera.lookAt(self.target, Vec3(0, 1, 0))   # Y is up