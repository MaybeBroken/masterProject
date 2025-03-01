from api import *
import os
import sys
import subprocess
import atexit
from screeninfo import get_monitors

if sys.platform == "win32":
    import keyboard
from direct.gui.DirectGui import *
from panda3d.core import *
from panda3d.core import (
    loadPrcFileData,
    MovieTexture,
    CardMaker,
    TransparencyAttrib,
    TextNode,
)
from direct.interval.IntervalGlobal import *

MAIN_SCRIPT_PATH = os.path.abspath(os.path.join(".", "main.py"))
VR_TUTORIAL_SCRIPT_PATH = os.path.abspath(os.path.join(".", "vrTraining.py"))
PROGRAM_TUTORIAL_SCRIPT_PATH = os.path.abspath(os.path.join(".", "programTraining.py"))
SELF_PATH = os.path.abspath(__file__)


loadPrcFileData(
    "",
    f"""want-pstats 0
win-size {get_monitors()[0].width} {get_monitors()[0].height}
fullscreen 0
undecorated 0
show-frame-rate-meter 0
clock-mode normal
sync-video 0
clock-frame-rate 0
window-title Terra: VR Launcher
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
        if sys.platform == "win32":
            keyboard.add_word_listener(
                word="exit-program",
                callback=lambda: os.system(f"taskkill /F /PID {os.getpid()}"),
                triggers=["enter"],
                timeout=5,
            )
        self.launch()

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

    def launch(self):
        cm = CardMaker("backgroundQuad")
        cm.setFrameFullscreenQuad()
        self.backgroundImageNp = self.render2d.attachNewNode(cm.generate())
        self.backgroundImage = self.loader.loadTexture("movies/background-1.png")
        self.backgroundImageNp.setTexture(self.backgroundImage)
        self.backgroundImageNp.setBin("background", 0)

        self.creditsText = OnscreenText(text="Programmed by David Sponseller\n")
        self.creditsText.setScale(0.05)
        self.creditsText.setPos(-0.95 * (1920 / 1080), -0.9)
        self.creditsText.setFg((1, 1, 1, 1))
        self.creditsText.setAlign(TextNode.ALeft)

        self.VrTutorialButton = DirectButton(
            scale=(0.15 * (6000 / 3375), 0.15, 0.15),
            pos=(0, 0, 0.5),
            command=self.launchVRTutorial,
            frameColor=(0.5, 0.5, 0.5, 0),
            relief=DGG.FLAT,
            text_fg=(0, 0, 0, 1),
            image="textures/vrTutorial.png",
        )
        self.ProgramTutorialButton = DirectButton(
            scale=(0.15 * (6000 / 3375), 0.15, 0.15),
            pos=(0, 0, 0),
            command=self.launchProgramTutorial,
            frameColor=(0.5, 0.5, 0.5, 0),
            relief=DGG.FLAT,
            text_fg=(0, 0, 0, 1),
            image="textures/programTutorial.png",
        )
        self.mainProgramButton = DirectButton(
            scale=(0.15 * (6000 / 3375), 0.15, 0.15),
            pos=(0, 0, -0.5),
            command=self.launchMainProgram,
            frameColor=(0.5, 0.5, 0.5, 0),
            relief=DGG.FLAT,
            text_fg=(0, 0, 0, 1),
            image="textures/mainProgram.png",
        )

        self.VrTutorialButton.setTransparency(TransparencyAttrib.MAlpha)
        self.ProgramTutorialButton.setTransparency(TransparencyAttrib.MAlpha)
        self.mainProgramButton.setTransparency(TransparencyAttrib.MAlpha)

    def launchMainProgram(self):
        subprocess.Popen(
            [sys.executable, MAIN_SCRIPT_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(MAIN_SCRIPT_PATH),
        )
        print("Launched main program")

    def launchVRTutorial(self):
        subprocess.Popen(
            [sys.executable, VR_TUTORIAL_SCRIPT_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(VR_TUTORIAL_SCRIPT_PATH),
        )
        print("Launched VR tutorial")

    def launchProgramTutorial(self):
        subprocess.Popen(
            [sys.executable, PROGRAM_TUTORIAL_SCRIPT_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(PROGRAM_TUTORIAL_SCRIPT_PATH),
        )
        print("Launched program tutorial")


def blocker():
    subprocess.Popen(
        [
            sys.executable,
            SELF_PATH,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(SELF_PATH),
    )


atexit.register(blocker)


Launcher().run()
