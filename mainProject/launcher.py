from api import *
import os
import sys
import subprocess
import atexit
import keyboard
from direct.gui.DirectGui import *
from panda3d.core import *
from panda3d.core import (
    loadPrcFileData,
    MovieTexture,
    CardMaker,
    Texture,
    AmbientLight,
    DirectionalLight,
    TransparencyAttrib,
    Vec4,
    TextNode,
)
from direct.interval.IntervalGlobal import *
from time import sleep

MAIN_SCRIPT_PATH = os.path.abspath(os.path.join(".", "main.py"))
VR_TUTORIAL_SCRIPT_PATH = os.path.abspath(
    os.path.join(".", "Training", "vrTraining.py")
)
PROGRAM_TUTORIAL_SCRIPT_PATH = os.path.abspath(
    os.path.join(".", "Training", "programTraining.py")
)
loadPrcFileData(
    "",
    f"""want-pstats 0
win-size 1920 1080
fullscreen 0
undecorated 0
show-frame-rate-meter 1
frame-rate-meter-scale 0.035
frame-rate-meter-update-interval 0.1
clock-mode normal
sync-video 0
clock-frame-rate 0
window-title Master Project Launcher
""",
)


class Launcher(BaseVrApp):
    def __init__(self):
        super().__init__(
            lensResolution=(1000, 1000),
            wantDevMode=False,
            FOV=95.5,
            autoCamPositioning=False,
            autoCamRotation=False,
            autoControllerPositioning=False,
            autoControllerRotation=False,
            launchShowBase=True,
            wantVr=False,
        )
        self.tex = {}
        self.accept("q", sys.exit)
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
        self.introAnimCard.setPos(-50, 75, -25)
        self.introAnimCard.setHpr(0, 0, 0)
        self.introAnimCard.setTransparency(TransparencyAttrib.MAlpha)
        self.introAnimCard.setColorScale(1, 1, 1, 1)

        self.autoCamPositioning = False

        self.introMovieTexture = self.startPlayer(
            "movies/intro-1.mp4", "introMovieTexture"
        )
        self.introAnimCard.setTexture(self.introMovieTexture)
        self.introMovieTexture.setLoop(False)
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
        cm = CardMaker("backgroundQuad")
        cm.setFrameFullscreenQuad()
        self.backgroundImageNp = self.render2d.attachNewNode(cm.generate())
        self.backgroundImage = self.loader.loadTexture("movies/background-1.png")
        self.backgroundImageNp.setTexture(self.backgroundImage)
        self.backgroundImageNp.setBin("background", 0)

        self.creditsText = OnscreenText(text="Programmed by David Sponseller\n")
        self.creditsText.setScale(0.05)
        self.creditsText.setPos(-0.95, -0.9)
        self.creditsText.setFg((1, 1, 1, 1))
        self.creditsText.setAlign(TextNode.ALeft)


Launcher().run()
