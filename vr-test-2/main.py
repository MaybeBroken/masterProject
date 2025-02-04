from api import *
from panda3d.core import *
from panda3d.core import (
    loadPrcFileData,
    AmbientLight,
    DirectionalLight,
    Texture,
    Shader,
    Vec4,
)
from direct.filter.FilterManager import FilterManager
from math import sin, cos, pi
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
window-title Vr-Test-2
""",
)


class Wvars:
    speed = 0.25
    swingSpeed = 10


class VrApp(BaseVrApp):
    def __init__(self):
        super().__init__(
            lensResolution=(1000, 1000),
            FOV=95.5,
            autoCamPositioning=True,
            autoCamRotation=True,
            autoControllerPositioning=True,
            autoControllerRotation=True,
        )
        self.model = self.loader.load_model("models/control1.bam")
        self.model.reparent_to(self.render)
        self.model.setScale(13)
        self.model.setPos(0, 0, -8.5)
        self.model.setHpr(-90, 0, 0)

        self.cam_left_tex.setCompression(Texture.CMOff)  # Disable compression
        self.cam_right_tex.setCompression(Texture.CMOff)  # Disable compression

        self.render.setShaderAuto()
        self.sceneAmbientLight = AmbientLight("sceneAmbientLight")
        self.sceneAmbientLight.setColor((0.5, 0.5, 0.5, 1))
        self.sceneAmbientLightNodePath = self.render.attachNewNode(
            self.sceneAmbientLight
        )
        self.render.setLight(self.sceneAmbientLightNodePath)
        self.sceneDirectionalLight = DirectionalLight("sceneDirectionalLight")
        self.sceneDirectionalLight.setDirection((-1, -1, -1))
        self.sceneDirectionalLight.setColor((0.8, 0.8, 0.8, 1))
        self.sceneDirectionalLightNodePath = self.render.attachNewNode(
            self.sceneDirectionalLight
        )
        self.render.setLight(self.sceneDirectionalLightNodePath)
        self.vrCamPos = (0, 0, 0)

        self.vrCamHpr = (0, 0, 0)
        self.sphereModel = self.loader.load_model("models/misc/sphere")
        self.sphereModel.setScale(0.7)
        self.sphereModel.setColor(0.5, 0.5, 0.5, 1)
        self.sphereModel.setBin("fixed", 10)
        self.sphereModel.instanceTo(self.hand_left)
        self.sphereModel.instanceTo(self.hand_right)

        self.loadSkybox()
        self.setupControls()
        self.setupShaders()
        self.player.setPos(0, -0.9, 3.9)
        self.taskMgr.add(self.update, "update")

    def setupShaders(self):
        for win, cam in [
            [self.win, self.cam],
            [self.buffer_left, self.cam_left],
            [self.buffer_right, self.cam_right],
        ]:
            try:
                threshold = Vec4(0.88, 0.9, 0.85, 0.4)
                manager = FilterManager(win, cam)
                tex1 = Texture()
                tex2 = Texture()
                tex3 = Texture()
                tex1.setCompression(Texture.CMOff)  # Disable compression
                tex2.setCompression(Texture.CMOff)  # Disable compression
                tex3.setCompression(Texture.CMOff)  # Disable compression
                finalquad = manager.renderSceneInto(colortex=tex1)
                interquad = manager.renderQuadInto(colortex=tex2)
                interquad.setShader(Shader.load("shaders/invert_threshold_r_blur.sha"))
                interquad.setShaderInput("tex1", tex1)
                interquad.setShaderInput("threshold", threshold)
                interquad2 = manager.renderQuadInto(colortex=tex3)
                interquad2.setShader(Shader.load("shaders/gaussian_blur.sha"))
                interquad2.setShaderInput("tex2", tex2)
                finalquad.setShader(Shader.load("shaders/lens_flare.sha"))
                finalquad.setShaderInput("tex1", tex1)
                finalquad.setShaderInput("tex2", tex2)
                finalquad.setShaderInput("tex3", tex3)
                # lf_settings = Vec3(lf_samples, lf_halo_width, lf_flare_dispersal)
                # finalquad.setShaderInput("lf_settings", lf_settings)
                # finalquad.setShaderInput("lf_chroma_distort", lf_chroma_distort)
            except Exception as e:
                print("Shader error: ", e)

    def loadSkybox(self):
        self.skybox = self.loader.load_model("skybox/box.bam")
        self.skybox.reparent_to(self.render)
        self.skybox.setScale(1000)
        for tex in self.skybox.findAllTextures():
            tex.setMinfilter(Texture.FTLinearMipmapLinear)
            tex.setMagfilter(Texture.FTLinear)
            tex.setCompression(Texture.CMOff)  # Disable compression to avoid JPEG artifacts
        self.skybox.setBin("background", 0)

    def update(self, task):
        result = task.cont
        playerMoveSpeed = Wvars.speed / 10

        x_movement = 0
        y_movement = 0
        z_movement = 0

        if self.keyMap["forward"]:
            y_movement = playerMoveSpeed
        if self.keyMap["backward"]:
            y_movement = -playerMoveSpeed
        if self.keyMap["left"]:
            x_movement = -playerMoveSpeed
        if self.keyMap["right"]:
            x_movement = playerMoveSpeed
        if self.keyMap["up"]:
            z_movement = playerMoveSpeed
        if self.keyMap["down"]:
            z_movement = -playerMoveSpeed
        dt = globalClock.getDt()  # type: ignore

        self.player.setPos(
            self.player.getX() + x_movement,
            self.player.getY() + y_movement,
            self.player.getZ() + z_movement,
        )
        self.skybox.setPos(self.player.getPos())

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
        self.accept("r", self.reset_view_orientation)
        self.accept("p", lambda: print(self.player.getPos()))

    def updateKeyMap(self, key, value):
        self.keyMap[key] = value


VrApp().run()
