from api import BaseVrApp


class VrApp(BaseVrApp):
    def __init__(self):
        super().__init__()
        self.model = self.loader.load_model("models/box")
        self.model.reparent_to(self.render)
        self.vrCam.setPos(0, 0, 5)
        self.vrCam.lookAt(0, 0, 0)


VrApp().run()
