from api import *
from panda3d.core import *
from panda3d.core import (
    loadPrcFileData,
    AmbientLight,
    DirectionalLight,
    Texture,
    Shader,
    Vec4,
    TransparencyAttrib,
    CardMaker,
    NodePath,
    GraphicsOutput,
    TextureStage,
    OrthographicLens,
    MovieTexture,
)
from direct.filter.FilterManager import FilterManager
from math import sin, cos, pi
from screeninfo import get_monitors
import os
import sys
from time import sleep
from direct.interval.IntervalGlobal import *


def degToRad(degrees):
    return degrees * (pi / 180.0)


if sys.platform == "darwin":
    pathSeparator = "/"
elif sys.platform == "win32":
    pathSeparator = "\\"
os.chdir(os.path.dirname(os.path.abspath(__file__)))

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
            launchShowBase=True,
        )
        self.tex = {}
        print("VrApp init")
        self.intro()

    def startPlayer(self, media_file, name):
        times = 0
        while True:
            self.tex[name] = MovieTexture(name)
            if self.tex[name].read(media_file):
                return self.tex[name]
            else:
                times += 1
                del self.tex[name]
                print("failed to load texture, retrying...")
                if times == 5:
                    print("failed to load texture, exiting...")
                    break
                else:
                    continue

    def stopTex(self, name):
        try:
            self.tex[name].stop()
        except:
            pass

    def playTex(self, name):
        try:
            self.tex[name].play()
        except:
            pass

    def setTexSpeed(self, name, speed):
        try:
            self.tex[name].setPlayRate(speed)
        except:
            pass

    def getTexSpeed(self, name):
        try:
            return self.tex[name].getPlayRate()
        except:
            return 0

    def intro(self):
        # plays the intro animation of the simulator
        self.cam_left_tex.setCompression(Texture.CMOff)  # Disable compression
        self.cam_right_tex.setCompression(Texture.CMOff)  # Disable compression
        self.buffer_left.setClearColorActive(True)
        self.buffer_left.setClearColor((0, 0, 0, 0))
        self.buffer_right.setClearColorActive(True)
        self.buffer_right.setClearColor((0, 0, 0, 0))

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
        self.sceneDirectionalLight.setShadowCaster(True, 1024, 1024)
        self.render.setLight(self.sceneDirectionalLightNodePath)

        self.blackoutModel = self.loader.load_model("models/box")
        self.blackoutModel.setScale(1000)
        self.blackoutModel.setPos(-500, -500, -500)
        self.blackoutModel.reparentTo(self.render)
        self.blackoutModel.setBin("background", 0)
        self.blackoutModel.setColor(0, 0, 0, 1)

        self.introAnimCard = self.render.attachNewNode(
            CardMaker("introAnimCard").generate()
        )
        self.introAnimCard.setTexture(self.cam_left_tex)
        self.introAnimCard.setScale(100, 100, 100)
        self.introAnimCard.setPos(-50, 100, -50)
        self.introAnimCard.setHpr(0, 0, 0)
        self.introAnimCard.setTransparency(TransparencyAttrib.MAlpha)
        self.introAnimCard.setColorScale(1, 1, 1, 1)

        self.autoCamPositioning = False

        self.introMovieTexture = self.startPlayer(
            "movies/intro-1.mp4", "introMovieTexture"
        )
        self.introAnimCard.setTexture(self.introMovieTexture)
        self.introMovieTexture.setLoop(False)
        sleep(5)

        self.introMovieTexture.play()
        self.taskMgr.add(self.introTask, "introTask")

    def introTask(self, task):
        if self.introMovieTexture.getTime() >= 4:

            def hideMethod(task):
                self.introAnimCard.hide()
                self.introMovieTexture.stop()
                self.introMovieTexture = None
                self.introAnimCard.removeNode()
                self.introAnimCard = None
                self.blackoutModel.removeNode()
                self.launch()

            self.doMethodLater(
                2,
                hideMethod,
                "hideMethod",
            )
            LerpColorInterval(
                nodePath=self.introAnimCard,
                duration=1.5,
                color=Vec4(0, 0, 0, 0),
                startColor=Vec4(1, 1, 1, 1),
            ).start()
        else:
            self.UpdateHeadsetTracking()
            return task.cont

    def launch(self):
        self.autoCamPositioning = True
        self.ship = self.loader.load_model("models/control1.bam")
        self.ship.reparent_to(self.render)
        self.ship.setScale(13)
        self.ship.setPos(0, 0, -8.5)
        self.ship.setHpr(-90, 0, 0)

        self.hand_left_model = self.loader.load_model("models/misc/sphere")
        self.hand_left_model.setScale(0.7)
        self.hand_left_model.reparentTo(self.hand_left)

        self.hand_right_model = self.loader.load_model("models/misc/sphere")
        self.hand_right_model.setScale(0.7)
        self.hand_right_model.reparentTo(self.hand_right)

        self.controlBoard = self.ship.find("**/Display")
        self.controlBoard.setColor(0, 0, 0, 1)
        self.controlBoard.setTransparency(TransparencyAttrib.MAlpha)

        self.planetRenderScene = NodePath("planetRenderScene")

        self.planetRenderLens = OrthographicLens()
        self.planetBuffer = self.make_buffer((900, 900))
        self.planetBuffer.setClearColorActive(True)
        self.planetBuffer.setClearColor((0, 0, 0, 0))
        self.planetCam = self.makeCamera(
            self.planetBuffer, scene=self.planetRenderScene, lens=self.planetRenderLens
        )
        self.planetBufferText = Texture()
        self.planetBufferText.setFormat(Texture.F_rgba)
        self.planetBufferText.setKeepRamImage(True)
        self.planetBuffer.addRenderTexture(
            self.planetBufferText, GraphicsOutput.RTMCopyRam, GraphicsOutput.RTPColor
        )
        self.planetBufferText.setWrapU(Texture.WMClamp)
        self.planetBufferText.setWrapV(Texture.WMClamp)

        self.solarSystem = self.loader.load_model("models/Systems/strangeSystem.bam")
        self.solarSystemNode = self.solarSystem.instanceTo(self.planetRenderScene)
        self.solarSystemNode.setPos(0, 0, 0)
        self.solarSystem.setScale(0.001)
        for geom in self.solarSystem.findAllMatches("**/+GeomNode"):
            if geom.getName().startswith("orbit"):
                # geom.removeNode()
                None
            elif geom.getName().startswith("atmosphere") or geom.getName().endswith(
                ".001"
            ):
                geom.removeNode()
            elif geom.getName().startswith("flare"):
                geom.removeNode()
            elif geom.getName().startswith("sun"):
                geom.setScale(10)
            elif geom.getName().startswith("planet"):
                geom.setScale(250)

        self.texCard = self.render.attachNewNode(CardMaker("texCard").generate())
        self.texCard.setTexture(self.planetBufferText)
        self.texCard.setPos(self.controlBoard.getPos(self.render))
        self.texCard.setScale(6, 1, 4)
        self.texCard.setX(self.texCard.getX() - self.texCard.getScale()[0] / 2)
        self.texCard.setY(self.texCard.getY() - (self.texCard.getScale()[2] / 2))
        self.texCard.setZ(self.texCard.getZ() - self.texCard.getScale()[1] / 2)
        self.texCard.setZ(self.texCard.getZ() - 0.1)
        self.texCard.setP(-60)

        self.texCard.setTexScale(TextureStage.getDefault(), 1, 1 * (4 / 6) - 0.05)

        self.texCard.setTransparency(TransparencyAttrib.MAlpha)
        self.texCard.setColorScale(0, 0.2, 1.5, 0.7)
        self.controlBoardCollider: ComplexCollider = (
            NodeIntersection.add_complex_collider(
                name="controlBoard",
                mesh=self.texCard.node(),
            )
        )

        self.loadSkybox()
        self.setupControls()
        self.setupShaders()
        self.player.setPos(0, -0.2, 3.9)

        self.leftThrottle = self.ship.find("**/leftHandle")
        self.rightThrottle = self.ship.find("**/rightHandle")

        self.leftThrottle.wrtReparentTo(self.render)
        self.rightThrottle.wrtReparentTo(self.render)

        self.baseLeftThrottlePos = self.leftThrottle.getPos()
        self.baseLeftThrottleHpr = self.leftThrottle.getHpr()

        self.baseRightThrottlePos = self.rightThrottle.getPos()
        self.baseRightThrottleHpr = self.rightThrottle.getHpr()

        self.leftThrottleCollider: BaseCollider = NodeIntersection.add_base_collider(
            radius=1.75,
            position=self.leftThrottle.getPos(),
            name="leftThrottle",
            mesh=self.leftThrottle,
        )
        self.rightThrottleCollider: BaseCollider = NodeIntersection.add_base_collider(
            radius=1.75,
            position=self.rightThrottle.getPos(),
            name="rightThrottle",
            mesh=self.rightThrottle,
        )

        self.hand_left_actor: BaseActor = NodeIntersection.add_base_actor(
            radius=0.25,
            position=self.hand_left.getPos(),
            name="hand_left",
            mesh=Sphere(radius=0.25, lat=20, lon=20),
        )
        self.hand_right_actor: BaseActor = NodeIntersection.add_base_actor(
            radius=0.25,
            position=self.hand_right.getPos(),
            name="hand_right",
            mesh=Sphere(radius=0.25, lat=20, lon=20),
        )
        self.hand_left_actor.sphere.reparentTo(self.render)
        self.hand_right_actor.sphere.reparentTo(self.render)

        self.leftThrottleCollider.sphere.reparentTo(self.render)
        self.rightThrottleCollider.sphere.reparentTo(self.render)

        NodeIntersection.hideCollisions()
        self.taskMgr.add(self.update, "update")

    def changePlanetLensSize(self, size):
        self.planetRenderLens.setFilmSize(size, size)

    def getPlanetLensSize(self):
        return self.planetRenderLens.getFilmSize()[0]

    def changePlanetLensPos(self, x, y):
        self.planetRenderLens.setFilmOffset(x, y)

    def getPlanetLensPos(self):
        return self.planetRenderLens.getFilmOffset()

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
            tex.setCompression(Texture.CMOff)
        self.skybox.setBin("background", 0)

    def update(self, task):
        self.UpdateHeadsetTracking()
        NodeIntersection.update()
        result = task.cont
        playerMoveSpeed = Wvars.speed / 10
        try:
            self.controlBoard.setTexture(self.cam_left_tex)
        except:
            self.controlBoard.setTextureOff()

        if self.HandState[0].trigger_value > self.HandState[0].haptic_threshold:
            self.hand_left.setScale(0.65)
            self.hand_left_model.setColor(0.2, 0.5, 0.7, 1)
        else:
            self.hand_left.setScale(0.7)
            self.hand_left_model.setColor(0.6, 0.6, 0.6, 1)
        if self.HandState[1].trigger_value > self.HandState[1].haptic_threshold:
            self.hand_right.setScale(0.65)
            self.hand_right_model.setColor(0.2, 0.5, 0.7, 1)
        else:
            self.hand_right.setScale(0.7)
            self.hand_right_model.setColor(0.6, 0.6, 0.6, 1)

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

        if self.planetCam:
            self.planetCam.setPos(self.planetRenderScene, 0, 0, 10)
            self.planetCam.setHpr(self.planetRenderScene, 0, -90, 0)

        if self.leftThrottleCollider.collision_report is not None:
            self.leftThrottle.setColorScale(1.5, 1.5, 1.5, 1)
            if self.HandState[0].trigger_value > self.HandState[0].haptic_threshold:
                self.leftThrottle.lookAt(self.hand_left)
                self.leftThrottle.setH(0)
                self.leftThrottle.setR(0)
                new_pitch = -self.leftThrottle.getP()
                if -65 <= new_pitch <= -1:
                    self.leftThrottle.setP(new_pitch)
                    self.baseLeftThrottleHpr = self.leftThrottle.getHpr()
                else:
                    self.leftThrottle.setHpr(self.baseLeftThrottleHpr)
        else:
            self.leftThrottle.setColorScale(1, 1, 1, 1)

        if self.rightThrottleCollider.collision_report is not None:
            self.rightThrottle.setColorScale(1.5, 1.5, 1.5, 1)
            if self.HandState[1].trigger_value > self.HandState[1].haptic_threshold:
                self.rightThrottle.lookAt(self.hand_right)
                self.rightThrottle.setH(0)
                self.rightThrottle.setR(0)
                new_pitch = -self.rightThrottle.getP()
                if -65 <= new_pitch <= -1:
                    self.rightThrottle.setP(new_pitch)
                    self.baseRightThrottleHpr = self.rightThrottle.getHpr()
                else:
                    self.rightThrottle.setHpr(self.baseRightThrottleHpr)
        else:
            self.rightThrottle.setColorScale(1, 1, 1, 1)
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
        self.accept("wheel_up", lambda: setattr(Wvars, "speed", Wvars.speed + 0.1))
        self.accept("wheel_down", lambda: setattr(Wvars, "speed", Wvars.speed - 0.1))
        self.accept(
            "control-wheel_up",
            lambda: setattr(Wvars, "speed", Wvars.speed + 1),
        )
        self.accept(
            "control-wheel_down",
            lambda: setattr(Wvars, "speed", Wvars.speed - 1),
        )

    def updateKeyMap(self, key, value):
        self.keyMap[key] = value


VrApp().run()
