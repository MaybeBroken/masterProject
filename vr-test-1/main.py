"""
"""

import glfw
from OpenGL import GL
import xr
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
)
from direct.showbase.ShowBase import ShowBase
from time import sleep


class MyApp(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        self.setBackgroundColor(0, 0, 0)
        self.accept("wheel_up", lambda: main.update_image_offset(0.0025))
        self.accept("wheel_down", lambda: main.update_image_offset(-0.0025))
        self.accept("q", exit)
        self.accept("escape", exit)
        self.camList = []

        # Create the left camera
        self.vrCam = self.render.attachNewNode("vrCam")
        self.cam_left = self.makeCamera(self.win, scene=self.render)
        self.cam_left.reparentTo(self.vrCam)
        self.cam_left.setPos(-0.1, 0, 0)  # Slight offset to the left
        self.camList.append(self.cam_left)
        self.cam_right = self.makeCamera(self.win, scene=self.render)
        self.cam_right.reparentTo(self.vrCam)
        self.cam_right.setPos(0.1, 0, 0)  # Slight offset to the right
        self.camList.append(self.cam_right)
        self.focusObject = self.vrCam.attachNewNode("focusObject")
        self.focusObject.setPos(0, 0, 0)

        def vrFocusTask(task):
            self.cam_left.lookAt(self.focusObject)
            self.cam_right.lookAt(self.focusObject)
            return task.cont

        # self.taskMgr.add(vrFocusTask, "vrFocusTask")

        # self.cam = self.cam_right
        self.vrCam.setPos(10, 10, 10)
        self.vrCam.lookAt(0, 0, 0)

        model = self.loader.loadModel("models/box")
        model.reparentTo(self.render)


class main:
    def start(self):
        glfw.init()
        self.image_offset = 0.1225
        self.cap = cv2.VideoCapture(0)  # Open the system camera
        if not self.cap.isOpened():
            print("Error: Could not open system camera.")
            return

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read frame from system camera.")
                break

            frame_left = frame
            frame_right = frame

            frame_left = cv2.flip(frame_left, 0)  # Flip the frame vertically
            frame_right = cv2.flip(frame_right, 0)  # Flip the frame vertically
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
                # self.cam_left = app.camList[0]
                # self.cam_right = app.camList[1]

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
                    frame = self.capture_frame()
                    if frame is not None:
                        frame_left = frame
                        frame_right = frame

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
                            GL.GL_BGR,
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
                            GL.GL_BGR,
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

    def capture_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Error: Could not read frame from system camera.")
            return None
        frame = cv2.flip(frame, 0)  # Flip the frame vertically
        return frame

    def update_image_offset(self, new_offset):
        self.image_offset += new_offset

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
_Thread(target=main.start).start()
app = MyApp()
app.run()

while True:
    sleep(0.1)
