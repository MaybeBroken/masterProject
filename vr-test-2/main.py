from api import *
from panda3d.core import loadPrcFileData
from math import sin, cos, radians, degrees, atan2, sqrt, pi
from screeninfo import get_monitors
import os
import sys


def degToRad(degrees):
    return degrees * (pi / 180.0)


if sys.platform == "darwin":
    pathSeparator = "/"
elif sys.platform == "win32":
    pathSeparator = "\\"
os.chdir(__file__.replace(__file__.split(pathSeparator)[-1], ""))

monitor = get_monitors()

loadPrcFileData(
    "",
    f"""want-pstats 0
win-size 800 800
fullscreen 0
undecorated 0
show-frame-rate-meter 1
frame-rate-meter-scale 0.035
frame-rate-meter-update-interval 0.1
clock-mode normal
sync-video 0
clock-frame-rate 0
""",
)


class Wvars:
    speed = 150
    swingSpeed = 10


class VrApp(BaseVrApp):
    def __init__(self):
        super().__init__(
            wantDevMode=True,
            lensResolution=(1000, 1000),
            FOV=95.5,
            autoCamRotation=True,
            autoControllerPositioning=True,
            autoControllerRotation=True,
        )
        self.model = self.loader.load_model("control1.bam")
        self.model.reparent_to(self.render)
        self.model.setScale(3)
        self.model.setHpr(180, 0, 0)
        self.vrCamPos = (0, 0, 0)
        self.vrCamHpr = (0, 0, 0)
        self.boxModel = self.loader.load_model("models/box")
        self.boxModel.setScale(1)
        self.boxModel.instanceTo(self.hand_left)
        self.boxModel.instanceTo(self.hand_right)
        self.setupControls()
        self.taskMgr.add(self.update, "update")

    def update(self, task):
        result = task.cont
        playerMoveSpeed = Wvars.speed / 10

        x_movement = 0
        y_movement = 0
        z_movement = 0

        dt = globalClock.getDt()  # type: ignore

        if self.keyMap["forward"]:
            x_movement -= dt * playerMoveSpeed * sin(degToRad(self.vrCam.getH()))
            y_movement += dt * playerMoveSpeed * cos(degToRad(self.vrCam.getH()))
        if self.keyMap["backward"]:
            x_movement += dt * playerMoveSpeed * sin(degToRad(self.vrCam.getH()))
            y_movement -= dt * playerMoveSpeed * cos(degToRad(self.vrCam.getH()))
        if self.keyMap["left"]:
            x_movement -= dt * playerMoveSpeed * cos(degToRad(self.vrCam.getH()))
            y_movement -= dt * playerMoveSpeed * sin(degToRad(self.vrCam.getH()))
        if self.keyMap["right"]:
            x_movement += dt * playerMoveSpeed * cos(degToRad(self.vrCam.getH()))
            y_movement += dt * playerMoveSpeed * sin(degToRad(self.vrCam.getH()))
        if self.keyMap["up"]:
            z_movement += dt * playerMoveSpeed
        if self.keyMap["down"]:
            z_movement -= dt * playerMoveSpeed

        self.vrCam.setPos(
            self.vrCam.getX() + x_movement,
            self.vrCam.getY() + y_movement,
            self.vrCam.getZ() + z_movement,
        )

        return result

    def setupControls(self):
        self.lastMouseX = 0
        self.lastMouseY = 0
        self.keyMap = {
            "forward": False,
            "backward": False,
            "left": False,
            "right": False,
            "up": False,
            "down": False,
        }
        self.accept("w", self.updateKeyMap, ["forward", True])
        self.accept("w-up", self.updateKeyMap, ["forward", False])
        self.accept("s", self.updateKeyMap, ["backward", True])
        self.accept("s-up", self.updateKeyMap, ["backward", False])
        self.accept("a", self.updateKeyMap, ["left", True])
        self.accept("a-up", self.updateKeyMap, ["left", False])
        self.accept("d", self.updateKeyMap, ["right", True])
        self.accept("d-up", self.updateKeyMap, ["right", False])
        self.accept("space", self.updateKeyMap, ["up", True])
        self.accept("space-up", self.updateKeyMap, ["up", False])
        self.accept("shift", self.updateKeyMap, ["down", True])
        self.accept("shift-up", self.updateKeyMap, ["down", False])

    def updateKeyMap(self, key, value):
        self.keyMap[key] = value


VrApp().run()
