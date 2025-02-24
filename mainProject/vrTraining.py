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
    Texture,
    AmbientLight,
    DirectionalLight,
    TransparencyAttrib,
    Vec4,
    TextNode,
)
from direct.stdpy.threading import Thread
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
win-size {get_monitors()[0].width} {get_monitors()[0].height}
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
        self.setBackgroundColor(0, 0, 0, 1)
        if sys.platform == "win32":
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
        self.backgroundImageNp.setTransparency(TransparencyAttrib.MAlpha)
        self.backgroundImageNp.setColor(0, 0, 0, 1)
        self.backgroundImageNp.setBin("background", 0)
        self.backgroundImage = self.loader.loadTexture("movies/background-1.png")
        self.backgroundImageNp.setTexture(self.backgroundImage)
        self.backgroundImageNp.setColor(1, 1, 1, 1)
        self.panel = Panel()
        runOnce = False
        os.chdir("mainProject")
        for tutorialImage in os.listdir(os.path.join("training", "tutorials", "VR")):
            if tutorialImage.endswith(".png"):
                name = os.path.splitext(tutorialImage)[0]
                texture = self.loader.loadTexture(
                    os.path.join("training", "tutorials", "VR", tutorialImage)
                )
                name = name.split("--")
                self.panel.addPage(
                    name=name[0],
                    texture=texture,
                    description=name[2],
                    title=name[1],
                    mediaType="texture",
                )
            elif tutorialImage.endswith(".mp4"):
                name = os.path.splitext(tutorialImage)[0]
            if not runOnce:
                runOnce = True
        if runOnce:
            self.panel.setPageIndex(0)
            self.accept("arrow_left", self.panel.previousPage)
            self.accept("arrow_right", self.panel.nextPage)


Launcher = Launcher()


class Page:
    def __init__(self, name, texture, description, title, mediaType):
        self.name = name
        self.texture = texture
        self.button = NULL
        self.buttonText = NULL
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
        self.box_default = Launcher.loader.loadTexture("textures/box-default.png")
        self.box_focused = Launcher.loader.loadTexture("textures/box-focused.png")
        self.pages: list[Page] = []
        self.buttons: list = []
        self.pageIndex: int = 0
        self.lastPageIndex: int = NULL

    def addPage(self, name, texture, description, title, mediaType):
        page = Page(name, texture, description, title, mediaType)
        page.button = DirectButton(
            image=self.box_default,
            scale=(0.05 * (6000 / 3375), 0.05, 0.05),
            command=self.openPage,
            extraArgs=[page],
            parent=Launcher.aspect2d,
            geom=None,
            relief=DGG.FLAT,
            frameColor=(0.5, 0.5, 0.5, 0),
        )
        page.button.setTransparency(TransparencyAttrib.MAlpha)
        self.buttons.append(page.button)
        self.pages.append(page)
        page.buttonText = OnscreenText(
            text=str(len(self.pages) + 1),
            scale=(1 * (3375 / 6000), 1, 1),
            parent=page.button,
            pos=(0.8, 0),
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
        )
        self.sortButtons()
        return page

    def openPage(self, page: Page):
        self.lastPageIndex = self.pageIndex
        self.pageIndex = self.pages.index(page)
        self.buttons[self.pageIndex].setImage(self.box_focused)
        if self.lastPageIndex != self.pageIndex:
            self.buttons[self.lastPageIndex].setImage(self.box_default)
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
            self.buttons[i].setScale(scale * (6000 / 3375), 1, scale)
            self.buttons[i].setTransparency(TransparencyAttrib.MAlpha)
            self.buttons[i].setPos(-0.75 + (i * spacing), 0, -0.875)

    def setPageIndex(self, index):
        if index < len(self.pages):
            self.lastPageIndex = self.pageIndex
            self.pageIndex = index
            self.mainNodePath.setTexture(self.pages[index].texture)
            self.buttons[self.pageIndex].setImage(self.box_focused)
            if self.lastPageIndex != self.pageIndex:
                self.buttons[self.lastPageIndex].setImage(self.box_default)

    def nextPage(self):
        if self.pageIndex + 1 < len(self.pages):
            self.setPageIndex(self.pageIndex + 1)

    def previousPage(self):
        if self.pageIndex - 1 >= 0:
            self.setPageIndex(self.pageIndex - 1)

    def navigatePages(self, direction):
        if direction == "next":
            self.nextPage()
        elif direction == "previous":
            self.previousPage()


Thread(target=Launcher.launch).start()
Launcher.run()
