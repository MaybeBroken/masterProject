"""
"""

from OpenGL import GL  # pip install PyOpenGL
import xr  # pip install pyopenxr
import numpy as np
from PIL import Image
import cv2
from threading import Thread as _Thread

from panda3d.core import *
from panda3d.core import (
    GraphicsPipe,
    FrameBufferProperties,
    WindowProperties,
    GraphicsOutput,
    GraphicsEngine,
    PNMImage,
    Texture,
    PerspectiveLens,
)
from direct.showbase.ShowBase import ShowBase
from time import sleep


class BaseVrApp(ShowBase):
    def __init__(self, lensResolution=[800, 800], wantDevMode=False, FOV=84):
        super().__init__()
        _Thread(target=main.start).start()
        self.setBackgroundColor(0, 0, 0)
        self.lensResolution = lensResolution

        self.camList = []
        self.view_left = True  # Flag to track which buffer to display

        # Create the left camera buffer
        self.vrLens = PerspectiveLens()
        self.buffer_left = self.make_buffer()
        self.cam_left = self.makeCamera(
            self.buffer_left, scene=self.render, lens=self.vrLens
        )
        self.cam_left.setPos(-0.1, 0, 0)  # Slight offset to the left
        self.camList.append(self.cam_left)

        # Create the right camera buffer
        self.buffer_right = self.make_buffer()
        self.cam_right = self.makeCamera(
            self.buffer_right, scene=self.render, lens=self.vrLens
        )
        self.cam_right.setPos(0.1, 0, 0)  # Slight offset to the right
        self.camList.append(self.cam_right)

        self.cam_left_tex = Texture()
        self.cam_right_tex = Texture()
        self.cam_left_tex.setKeepRamImage(True)
        self.cam_right_tex.setKeepRamImage(True)
        global cam_left_tex, cam_right_tex
        cam_left_tex = self.cam_left_tex
        cam_right_tex = self.cam_right_tex
        self.buffer_left.addRenderTexture(
            self.cam_left_tex, GraphicsOutput.RTMCopyRam, GraphicsOutput.RTPColor
        )
        self.buffer_right.addRenderTexture(
            self.cam_right_tex, GraphicsOutput.RTMCopyRam, GraphicsOutput.RTPColor
        )
        self.vrCam = self.render.attachNewNode("vrCam")
        self.cam_left.reparentTo(self.vrCam)
        self.cam_right.reparentTo(self.vrCam)
        self.camRootNode = self.render.attachNewNode("camRootNode")
        self.vrCam.reparentTo(self.camRootNode)
        self.camera.reparentTo(self.camRootNode)
        self.vrCameraPose = None
        self.wantHeadsetControl = True

        self.vrCamPos = (0, 0, 0)
        self.vrCamHpr = (0, 0, 0)

        def getHeadsetTask(task):
            try:
                self.vrCameraPose = main.pose
                if self.wantHeadsetControl:
                    self.vrCam.setPos(
                        (self.vrCameraPose.position.x * 10) + self.vrCamPos[0],
                        (self.vrCameraPose.position.z * 10) + self.vrCamPos[1],
                        (self.vrCameraPose.position.y * 10) + self.vrCamPos[2],
                    )
                    self.vrCam.setHpr(
                        (self.vrCameraPose.orientation.y * -100) + self.vrCamHpr[0],
                        (self.vrCameraPose.orientation.x * -100) + self.vrCamHpr[1],
                        (self.vrCameraPose.orientation.z * 100) + self.vrCamHpr[2],
                    )
                    self.camera.setPos(self.vrCam.getPos())
                    self.camera.setHpr(self.vrCam.getHpr())
            except Exception as e:
                print(e)
                sleep(0.75)

            return task.cont

        self.taskMgr.add(getHeadsetTask, "getHeadsetTask")
        self.doMethodLater(
            2, lambda task: self.toggle_dev_win_view(), "toggle_dev_win_view"
        )

        def resetView():
            self.camLens.setFov(FOV)
            self.cam_left.setPos(0.25, 0, 0)
            self.cam_right.setPos(-0.25, 0, 0)
            self.cam_left.lookAt(self.focusObject)
            self.cam_right.lookAt(self.focusObject),

        if wantDevMode:
            self.accept("f", resetView)
            self.accept("v", self.toggle_dev_win_view)
            self.accept(
                "p",
                lambda: print(
                    f"Lens FOV: {self.vrLens.getFov()}\nLens Distance: {self.cam_left.getX() - self.cam_right.getX()}\n"
                ),
            )
            self.accept(
                "wheel_up",
                lambda: (
                    self.vrLens.setFov(self.vrLens.getFov() + 1),
                    print("FOV: ", self.vrLens.getFov()),
                ),
            )
            self.accept(
                "wheel_down",
                lambda: (
                    self.vrLens.setFov(self.vrLens.getFov() - 1),
                    print("FOV: ", self.vrLens.getFov()),
                ),
            )
            self.accept(
                "control-wheel_up",
                lambda: (
                    main.update_image_offset(0.01),
                    print("Offset: ", main.image_offset),
                ),
            )
            self.accept(
                "control-wheel_down",
                lambda: (
                    main.update_image_offset(-0.01),
                    print("Offset: ", main.image_offset),
                ),
            )

        self.camLens.setFov(FOV)
        self.cam_left.setPos(0.25, 0, 0)
        self.cam_right.setPos(-0.25, 0, 0)

    def make_buffer(self):
        winprops = WindowProperties.size(self.lensResolution[0], self.lensResolution[1])
        fbprops = FrameBufferProperties()
        fbprops.setRgbColor(True)
        fbprops.setDepthBits(1)
        buffer = self.graphicsEngine.makeOutput(
            self.pipe,
            "offscreen buffer",
            -2,
            fbprops,
            winprops,
            GraphicsPipe.BFRefuseWindow,
            self.win.getGsg(),
            self.win,
        )
        return buffer

    def toggle_dev_win_view(self):
        def update_frames():
            while True:
                frame_left = self.get_camera_image(self.cam_left_tex)
                frame_right = self.get_camera_image(self.cam_right_tex)

                frame_data_left = np.array(frame_left, np.uint8)
                frame_data_right = np.array(frame_right, np.uint8)

                # Create or update windows to display the frames
                left_window_name = "Left View"
                right_window_name = "Right View"
                cv2.namedWindow(left_window_name, cv2.WINDOW_NORMAL)
                cv2.namedWindow(right_window_name, cv2.WINDOW_NORMAL)
                cv2.imshow(left_window_name, frame_data_left)
                cv2.imshow(right_window_name, frame_data_right)

                # Add a small delay to allow the window to refresh
                cv2.waitKey(1)
                sleep(0.01)

        # Run the frame update in a separate thread to avoid blocking the main loop
        _Thread(target=update_frames, daemon=True).start()

    def get_camera_image(self, texture):
        while not texture.hasRamImage():
            sleep(0.01)
        image = np.array(texture.getRamImageAs("RGB"), dtype=np.uint8)
        image = image.reshape((texture.getYSize(), texture.getXSize(), 3))
        return image


class main:
    def start(self):
        self.image_offset = 0.1225

        while True:
            while True:
                try:
                    cam_left_tex
                    cam_right_tex
                    break
                except NameError:
                    sleep(0.1)
            frame_left = self.get_camera_image(cam_left_tex)
            frame_right = self.get_camera_image(cam_right_tex)

            frame_data_left = np.array(frame_left, np.uint8)
            frame_data_right = np.array(frame_right, np.uint8)

            # ContextObject is a high level pythonic class meant to keep simple cases simple.
            with xr.ContextObject(
                instance_create_info=xr.InstanceCreateInfo(
                    enabled_extension_names=[
                        # A graphics extension is mandatory (without a headless extension)
                        xr.KHR_OPENGL_ENABLE_EXTENSION_NAME,
                    ],
                ),
            ) as context:

                # Initialize the Panda3D camera
                # self.cam_left = BaseVrApp.camList[0]
                # self.cam_right = BaseVrApp.camList[1]

                texture_id_left = GL.glGenTextures(1)
                texture_id_right = GL.glGenTextures(1)

                def setup_texture(texture_id):
                    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id)
                    GL.glTexParameteri(
                        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR
                    )
                    GL.glTexParameteri(
                        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
                    )

                setup_texture(texture_id_left)
                setup_texture(texture_id_right)

                VERTEX_SHADER_SOURCE = """
                #version 330 core
                layout(location = 0) in vec3 position;
                layout(location = 1) in vec2 texCoord;
                out vec2 TexCoord;
                void main()
                {
                    gl_Position = vec4(position, 1.0);
                    TexCoord = texCoord;
                }
                """

                FRAGMENT_SHADER_SOURCE = """
                #version 330 core
                in vec2 TexCoord;
                out vec4 color;
                uniform sampler2D ourTexture;
                uniform vec2 offset;
                void main()
                {
                    color = texture(ourTexture, TexCoord + offset);
                }
                """

                shader_program = self.create_shader_program(
                    VERTEX_SHADER_SOURCE, FRAGMENT_SHADER_SOURCE
                )
                GL.glUseProgram(shader_program)

                vertices = np.array(
                    [
                        # positions       # texture coords
                        -1.0,
                        -1.0,
                        0.0,
                        0.0,
                        0.0,
                        1.0,
                        -1.0,
                        0.0,
                        1.0,
                        0.0,
                        1.0,
                        1.0,
                        0.0,
                        1.0,
                        1.0,
                        -1.0,
                        1.0,
                        0.0,
                        0.0,
                        1.0,
                    ],
                    dtype=np.float32,
                )

                indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

                VAO = GL.glGenVertexArrays(1)
                VBO = GL.glGenBuffers(1)
                EBO = GL.glGenBuffers(1)

                GL.glBindVertexArray(VAO)

                GL.glBindBuffer(GL.GL_ARRAY_BUFFER, VBO)
                GL.glBufferData(
                    GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW
                )

                GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, EBO)
                GL.glBufferData(
                    GL.GL_ELEMENT_ARRAY_BUFFER,
                    indices.nbytes,
                    indices,
                    GL.GL_STATIC_DRAW,
                )

                GL.glVertexAttribPointer(
                    0,
                    3,
                    GL.GL_FLOAT,
                    GL.GL_FALSE,
                    5 * vertices.itemsize,
                    GL.ctypes.c_void_p(0),
                )
                GL.glEnableVertexAttribArray(0)

                GL.glVertexAttribPointer(
                    1,
                    2,
                    GL.GL_FLOAT,
                    GL.GL_FALSE,
                    5 * vertices.itemsize,
                    GL.ctypes.c_void_p(3 * vertices.itemsize),
                )
                GL.glEnableVertexAttribArray(1)

                GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
                GL.glBindVertexArray(0)

                # Variable to control the distance between images

                for frame_index, frame_state in enumerate(context.frame_loop()):
                    view_state, views = xr.locate_views(
                        session=context.session,
                        view_locate_info=xr.ViewLocateInfo(
                            view_configuration_type=context.view_configuration_type,
                            display_time=frame_state.predicted_display_time,
                            space=context.space,
                        ),
                    )
                    flags = xr.ViewStateFlags(view_state.view_state_flags)
                    if flags & xr.ViewStateFlags.POSITION_VALID_BIT:
                        view = views[xr.Eye.LEFT]
                        self.pose = view.pose
                    else:
                        None
                    frame = self.get_camera_image(cam_left_tex)
                    if frame is not None:
                        frame_left = self.get_camera_image(cam_left_tex)
                        frame_right = self.get_camera_image(cam_right_tex)

                        frame_data_left = np.array(frame_left, np.uint8)
                        frame_data_right = np.array(frame_right, np.uint8)

                        GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id_left)
                        GL.glTexImage2D(
                            GL.GL_TEXTURE_2D,
                            0,
                            GL.GL_RGB,
                            frame_left.shape[1],
                            frame_left.shape[0],
                            0,
                            GL.GL_RGB,
                            GL.GL_UNSIGNED_BYTE,
                            frame_data_left,
                        )

                        GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id_right)
                        GL.glTexImage2D(
                            GL.GL_TEXTURE_2D,
                            0,
                            GL.GL_RGB,
                            frame_right.shape[1],
                            frame_right.shape[0],
                            0,
                            GL.GL_RGB,
                            GL.GL_UNSIGNED_BYTE,
                            frame_data_right,
                        )

                    for view_index, view in enumerate(context.view_loop(frame_state)):
                        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
                        GL.glUseProgram(
                            shader_program
                        )  # Ensure the shader program is active

                        if view_index == 0:  # Left eye
                            GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id_left)
                            GL.glUniform2f(
                                GL.glGetUniformLocation(shader_program, "offset"),
                                -self.image_offset,
                                0.0,
                            )
                        else:  # Right eye
                            GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id_right)
                            GL.glUniform2f(
                                GL.glGetUniformLocation(shader_program, "offset"),
                                self.image_offset,
                                0.0,
                            )

                        GL.glBindVertexArray(VAO)
                        GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)
                        GL.glBindVertexArray(0)
                        GL.glUseProgram(0)
                        GL.glDisable(GL.GL_BLEND)

    def get_camera_image(self, texture):
        while not texture.hasRamImage():
            sleep(0.01)
        image = np.array(texture.getRamImageAs("RGB"), dtype=np.uint8)
        image = image.reshape((texture.getYSize(), texture.getXSize(), 3))
        return image

    def update_image_offset(self, new_offset):
        self.image_offset += new_offset

    def set_image_offset(self, new_offset):
        self.image_offset = new_offset

    def compile_shader(self, source, shader_type):
        shader = GL.glCreateShader(shader_type)
        GL.glShaderSource(shader, source)
        GL.glCompileShader(shader)
        if not GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS):
            raise RuntimeError(GL.glGetShaderInfoLog(shader))
        return shader

    def create_shader_program(self, vertex_source, fragment_source):
        vertex_shader = self.compile_shader(vertex_source, GL.GL_VERTEX_SHADER)
        fragment_shader = self.compile_shader(fragment_source, GL.GL_FRAGMENT_SHADER)
        program = GL.glCreateProgram()
        GL.glAttachShader(program, vertex_shader)
        GL.glAttachShader(program, fragment_shader)
        GL.glLinkProgram(program)
        if not GL.glGetProgramiv(program, GL.GL_LINK_STATUS):
            raise RuntimeError(GL.glGetProgramInfoLog(program))
        GL.glDeleteShader(vertex_shader)
        GL.glDeleteShader(fragment_shader)
        return program


main = main()
if __name__ == "__main__":
    BaseVrApp().run()
