from api import BaseVrApp


class VrApp(BaseVrApp):
    def __init__(self):
        super().__init__()
        self.model = self.loader.load_model("Environment/environment.egg")
        self.model.reparent_to(self.render)


VrApp().run()
