from api import BaseVrApp


class VrApp(BaseVrApp):
    def __init__(self):
        super().__init__(wantDevMode=True, lensResolution=(1000, 1000), FOV=84)
        self.model = self.loader.load_model("Environment/environment.egg")
        self.model.reparent_to(self.render)
        self.model.setScale(15)
        self.vrCamPos = (15, 10, 2)
        self.vrCamHpr = (0, 0, 0)


VrApp().run()
