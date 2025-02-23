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

NULL = None
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
        keyboard.add_word_listener(
            word="exit",
            callback=lambda: os.system(f"taskkill /F /PID {os.getpid()}"),
            triggers=["enter"],
            timeout=1,
        )

    def makeCard(self, name):
        cm = CardMaker(name)
        cm.setFrameFullscreenQuad()
        return cm.generate()

    def launch(self):
        self.backgroundImageNp = self.render2d.attachNewNode(
            self.makeCard("backgroundTexture")
        )
        self.backgroundImage = self.loader.loadTexture("movies/background-1.png")
        self.backgroundImageNp.setTexture(self.backgroundImage)
        self.backgroundImageNp.setBin("background", 0)

        self.creditsText = OnscreenText(text="Programmed by David Sponseller\n")
        self.creditsText.setScale(0.05)
        self.creditsText.setPos(-0.95 * (1920 / 1080), -0.9)
        self.creditsText.setFg((1, 1, 1, 1))
        self.creditsText.setAlign(TextNode.ALeft)

        self.panel = Panel()
        for tutorialImage in os.listdir("Training/tutorials/VR/"):
            if tutorialImage.endswith(".png"):
                name = os.path.splitext(tutorialImage)[0]
                texture = self.loader.loadTexture(
                    os.path.join("Training/tutorials/VR/", tutorialImage)
                )
                name = name.split("_")
                self.panel.addPage(
                    name=name[0],
                    texture=texture,
                    description=name[2],
                    title=name[1],
                    mediaType="texture",
                )
            elif tutorialImage.endswith(".mp4"):
                name = os.path.splitext(tutorialImage)[0]


Launcher = Launcher()


class Page:
    def __init__(self, name, texture, description, title, mediaType):
        self.name = name
        self.texture = texture
        self.button = NULL
        self.description = description
        self.title = title
        self.mediaType = mediaType
        self.uiElements: dict = {}


class Panel:
    def __init__(self):
        self.pageNode = Launcher.render2d.attachNewNode("pageNode")
        self.mainImg = Launcher.loader.loadTexture("movies/background-1.png")
        self.mainCard = Launcher.makeCard("mainCard")
        self.mainNodePath = self.pageNode.attachNewNode(self.mainCard)
        self.mainNodePath.setTransparency(TransparencyAttrib.MAlpha)
        self.mainNodePath.setTexture(self.mainImg)
        self.mainNodePath.setScale(0.75)
        self.pages: list[Page] = []
        self.buttons: list = []
        self.pageIndex: int = NULL

    def addPage(self, name, texture, description, title, mediaType):
        page = Page(name, texture, description, title, mediaType)
        page.button = DirectButton(
            text=len(self.pages) + 1,
            scale=0.05,
            command=self.openPage,
            extraArgs=[page],
            parent=Launcher.aspect2d,
        )
        self.buttons.append(page.button)
        self.pages.append(page)
        self.sortButtons()
        return page

    def openPage(self, page: Page):
        if page.mediaType == "texture":
            self.mainNodePath.setTexture(page.texture)

    def sortButtons(self):
        length = len(self.buttons)
        if length == 0:
            return

        spacing = 1.5 / length
        scale = 0.05

        if spacing < 0.12:
            scale *= spacing / 0.12

        for i in range(length):
            self.buttons[i].setScale(scale)
            self.buttons[i].setPos(
                -0.75 + (i * spacing) - (spacing * (length - 1) / 2), 0, -0.75
            )

    def setPageIndex(self, index):
        if index < len(self.pages):
            self.pageIndex = index
            self.mainNodePath.setTexture(self.pages[index].texture)
            self.mainNodePath.setPos(0, 0, -0.75 + (index * (1.5 / len(self.pages))))
        else:
            print("Page index out of range")


Launcher.launch()
Launcher.run()
