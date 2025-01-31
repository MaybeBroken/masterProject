from api import BaseVrApp


class VrApp(BaseVrApp):
    def __init__(self):
        super().__init__(wantDevMode=True, lensResolution=(1000, 1000), FOV=95.5)
        self.model = self.loader.load_model("Environment/environment.egg")
        self.model.reparent_to(self.render)
        self.model.setScale(15)
        self.vrCamPos = (0, 0, 0)
        self.vrCamHpr = (0, 0, 0)
        self.boxModel = self.loader.load_model("models/box")
        self.boxModel.setScale(5)
        self.boxModel.instanceTo(self.hand_left)
        self.boxModel.instanceTo(self.hand_right)


VrApp().run()
