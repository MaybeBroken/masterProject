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
window-title VR Training
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
        keyboard.add_word_listener(
            word="exit-4097",
            callback=lambda: os.system(f"taskkill /F /PID {os.getpid()}"),
            triggers=["return", "enter"],
            timeout=5,
        )
        self.launch()

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

        self.startButton = DirectButton(
            text="Start VR Tutorial",
            scale=0.1,
            command=self.start_vr_tutorial,
            pos=(0, 0, 0),
        )
    
    def start_vr_tutorial(self):
        self.startButton.destroy()
        self.creditsText.destroy()


Launcher().run()
