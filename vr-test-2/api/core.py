"""
"""

import sys

if not sys.platform == "win32":
    if 1 == 1:
        exit("This API is only supported on Windows.")

from OpenGL import GL
import xr
import numpy as np
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
    ConfigVariableString,
    LVecBase3,
    LQuaternionf,
)
from direct.showbase.ShowBase import ShowBase
from time import sleep
import ctypes
from math import asin, degrees
from pyquaternion import Quaternion


class BaseVrApp(ShowBase):
    def __init__(
        self,
        lensResolution=[800, 800],
        wantDevMode=False,
        FOV=95.5,
        autoCamPositioning=False,
        autoCamRotation=False,
        autoControllerPositioning=False,
        autoControllerRotation=False,
    ):
        super().__init__()
        _Thread(target=main.start).start()
        self.setBackgroundColor(0, 0, 0)
        self.lensResolution = lensResolution
        self.wantDevMode = wantDevMode
        self.FOV = FOV
        if wantDevMode:
            ConfigVariableString.setValue("want-pstats", "1")

        self.camList = []
        self.view_left = True  # Flag to track which buffer to display

        # Create the left camera buffer
        self.vrLens = PerspectiveLens()
        self.buffer_left = self.make_buffer()
        self.cam_left = self.makeCamera(
            self.buffer_left, scene=self.render, lens=self.vrLens
        )
        self.cam_left.setPos(-0.25, 0, 0)  # Adjusted offset to the left
        self.camList.append(self.cam_left)

        # Create the right camera buffer
        self.buffer_right = self.make_buffer()
        self.cam_right = self.makeCamera(
            self.buffer_right, scene=self.render, lens=self.vrLens
        )
        self.cam_right.setPos(0.25, 0, 0)  # Adjusted offset to the right
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
        self.player = self.render.attachNewNode("vrCamRoot")
        self.vrCam = self.player.attachNewNode("vrCam")
        self.cam_left.reparentTo(self.vrCam)
        self.cam_right.reparentTo(self.vrCam)
        self.camRootNode = self.player.attachNewNode("camRootNode")
        self.vrCam.reparentTo(self.camRootNode)
        self.camera.reparentTo(self.camRootNode)
        self.vrCameraPose = None

        self.vrCamPos = (0, 0, 0)
        self.vrCamHpr = (0, 0, 0)
        self.vrCamPosOffset = (0, 0, -1.6)
        self.vrControllerPosOffset = (0, 0, -1.6)
        self.vrCamHprOffset = (0, 0, 0)
        self.vrControllerHprOffset = (0, 0, 0)

        self.lastException = ""
        self.lastExceptionTime = 0

        self.handRootNode = self.player.attachNewNode("handRootNode")
        self.hand_left = self.handRootNode.attachNewNode("hand_left")
        self.hand_right = self.handRootNode.attachNewNode("hand_right")
        self.vrControllerPose = None

        def getHeadsetTask(task):
            try:
                while main.pose_quat is None:
                    GraphicsEngine.get_global_ptr().render_frame()
                    sleep(0.01)
                self.vrCameraPose = main.pose_quat
                self.vrControllerPose = main.controller
                self.camera.setPos(self.vrCam.getPos())
                self.camera.setHpr(self.vrCam.getHpr())
                self.camLens.setFov(self.vrLens.getFov())
                self.camLens.setAspectRatio(
                    self.lensResolution[0] / self.lensResolution[1]
                )
                if autoCamPositioning:
                    self.vrCam.setPos(
                        ((self.vrCameraPose.position.x + self.vrCamPosOffset[0]) * 7)
                        + self.vrCamPos[0],
                        ((self.vrCameraPose.position.z + self.vrCamPosOffset[1]) * -7)
                        + self.vrCamPos[1],
                        ((self.vrCameraPose.position.y + self.vrCamPosOffset[2]) * 7)
                        + self.vrCamPos[2],
                    )
                if autoCamRotation:
                    self.vrCam.setQuat(
                        LQuaternionf(
                            -self.vrCameraPose.orientation.w,
                            -self.vrCameraPose.orientation.x,
                            -self.vrCameraPose.orientation.z,
                            -self.vrCameraPose.orientation.y,
                        )
                    )
                    self.vrCam.setR(-self.vrCam.getR())
                if autoControllerPositioning:
                    try:
                        self.hand_left.setPos(
                            (
                                (self.vrControllerPose["left"].position.x)
                                + self.vrControllerPosOffset[0]
                            )
                            * 7,
                            (
                                (self.vrControllerPose["left"].position.z)
                                + self.vrControllerPosOffset[1]
                            )
                            * -7,
                            (
                                (self.vrControllerPose["left"].position.y)
                                + self.vrControllerPosOffset[2]
                            )
                            * 7,
                        )
                        self.hand_right.setPos(
                            (
                                (self.vrControllerPose["right"].position.x)
                                + self.vrControllerPosOffset[0]
                            )
                            * 7,
                            (
                                (self.vrControllerPose["right"].position.z)
                                + self.vrControllerPosOffset[1]
                            )
                            * -7,
                            (
                                (self.vrControllerPose["right"].position.y)
                                + self.vrControllerPosOffset[2]
                            )
                            * 7,
                        )
                    except:
                        pass
                if autoControllerRotation:
                    try:
                        self.hand_left.setQuat(
                            LQuaternionf(
                                -self.vrControllerPose["left"].orientation.w,
                                -self.vrControllerPose["left"].orientation.x,
                                -self.vrControllerPose["left"].orientation.z,
                                -self.vrControllerPose["left"].orientation.y,
                            )
                        )
                        self.hand_left.setR(-self.hand_left.getR())
                        self.hand_right.setQuat(
                            LQuaternionf(
                                -self.vrControllerPose["right"].orientation.w,
                                -self.vrControllerPose["right"].orientation.x,
                                -self.vrControllerPose["right"].orientation.z,
                                -self.vrControllerPose["right"].orientation.y,
                            )
                        )
                        self.hand_right.setR(-self.hand_right.getR())
                    except:
                        pass
            except Exception as e:
                print(str(e))
                print("\n")
                sleep(0.1)

            return task.cont

        self.taskMgr.add(getHeadsetTask, "getHeadsetTask")

        if wantDevMode:
            self.doMethodLater(
                2, lambda task: self.toggle_dev_win_view(), "toggle_dev_win_view"
            )
            self.accept("v", self.toggle_dev_win_view)
            self.accept(
                "p",
                lambda: print(
                    f"Lens FOV: {self.vrLens.getFov()}\nLens Distance: {self.cam_left.getX(), self.cam_right.getX()}\nImage Offset: {main.image_offset}"
                ),
            )
            self.accept(
                "wheel_up",
                lambda: (
                    self.vrLens.setFov(self.vrLens.getFov() + 0.5),
                    print("FOV: ", self.vrLens.getFov()),
                ),
            )
            self.accept(
                "wheel_down",
                lambda: (
                    self.vrLens.setFov(self.vrLens.getFov() - 0.5),
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
            self.accept(
                "alt-wheel_up",
                lambda: (
                    self.cam_left.setPos(self.cam_left.getX() - 0.01, 0, 0),
                    self.cam_right.setPos(self.cam_right.getX() + 0.01, 0, 0),
                    print(
                        "Lens Distance: ", (self.cam_left.getX(), self.cam_right.getX())
                    ),
                ),
            )
            self.accept(
                "alt-wheel_down",
                lambda: (
                    self.cam_left.setPos(self.cam_left.getX() + 0.01, 0, 0),
                    self.cam_right.setPos(self.cam_right.getX() - 0.01, 0, 0),
                    print(
                        "Lens Distance: ", (self.cam_left.getX(), self.cam_right.getX())
                    ),
                ),
            )
            self.accept("r", self.reset_view_orientation)

        self.vrLens.setFov(FOV)
        self.vrLens.setAspectRatio(self.lensResolution[0] / self.lensResolution[1])
        self.cam_left.setPos(-0.25, 0, 0)
        self.cam_right.setPos(0.25, 0, 0)

    def resetView(self):
        self.vrLens.setFov(self.FOV)
        self.vrLens.setAspectRatio(self.lensResolution[0] / self.lensResolution[1])
        self.cam_left.setPos(-0.25, 0, 0)
        self.cam_right.setPos(0.25, 0, 0)
        self.vrCamPos = (0, 0, 0)
        self.vrCamHpr = (0, 0, 0)
        self.vrCamPosOffset = (0, 0, 0)
        self.vrControllerPosOffset = (0, 0, -0.8)
        self.vrCamHprOffset = (0, 0, 0)
        self.vrControllerHprOffset = (0, 0, 0)
        self.vrCam.setPos(self.vrCamPos)

    def reset_view_orientation(self):
        self.vrCamPosOffset = (
            -self.vrCameraPose.position.x,
            -self.vrCameraPose.position.y,
            -self.vrCameraPose.position.z,
        )
        self.vrCamHprOffset = (
            -self.vrCameraPose.orientation.y,
            -self.vrCameraPose.orientation.x,
            -self.vrCameraPose.orientation.z,
        )
        self.resetView()

    def make_buffer(self):
        winprops = WindowProperties.size(
            self.lensResolution[0],
            self.lensResolution[1],
        )
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
                try:
                    frame_left = self.get_camera_image(self.cam_left_tex)
                    frame_right = self.get_camera_image(self.cam_right_tex)

                    frame_data_left = np.flipud(
                        np.array(frame_left, dtype=np.uint8)[:, :, ::-1]
                    )
                    frame_data_right = np.flipud(
                        np.array(frame_right, dtype=np.uint8)[:, :, ::-1]
                    )

                    # Create or update windows to display the frames
                    left_window_name = "Left View"
                    right_window_name = "Right View"
                    cv2.namedWindow(left_window_name, cv2.WINDOW_NORMAL)
                    cv2.namedWindow(right_window_name, cv2.WINDOW_NORMAL)
                    cv2.imshow(left_window_name, frame_data_left)
                    cv2.imshow(right_window_name, frame_data_right)

                    # Add a small delay to allow the window to refresh
                    cv2.waitKey(1)
                except Exception as e:
                    print(str(e))
                    print()
                    sleep(0.1)

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
        self.lastException = ""
        self.lastExceptionTime = 0
        self.pose_quat = None
        self.controller = {"left": None, "right": None}
        self.context = None  # Add this line to store the context object

        while True:
            while True:
                try:
                    cam_left_tex
                    cam_right_tex
                    break
                except NameError as e:
                    print(str(e))
                    print("\n")
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
                self.context = context  # Store the context object
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

                controller_paths = (xr.Path * 2)(
                    xr.string_to_path(context.instance, "/user/hand/left"),
                    xr.string_to_path(context.instance, "/user/hand/right"),
                )
                controller_pose_action = xr.create_action(
                    action_set=context.default_action_set,
                    create_info=xr.ActionCreateInfo(
                        action_type=xr.ActionType.POSE_INPUT,
                        action_name="hand_pose",
                        localized_action_name="Hand Pose",
                        count_subaction_paths=len(controller_paths),
                        subaction_paths=controller_paths,
                    ),
                )
                suggested_bindings = (xr.ActionSuggestedBinding * 2)(
                    xr.ActionSuggestedBinding(
                        action=controller_pose_action,
                        binding=xr.string_to_path(
                            instance=context.instance,
                            path_string="/user/hand/left/input/grip/pose",
                        ),
                    ),
                    xr.ActionSuggestedBinding(
                        action=controller_pose_action,
                        binding=xr.string_to_path(
                            instance=context.instance,
                            path_string="/user/hand/right/input/grip/pose",
                        ),
                    ),
                )
                xr.suggest_interaction_profile_bindings(
                    instance=context.instance,
                    suggested_bindings=xr.InteractionProfileSuggestedBinding(
                        interaction_profile=xr.string_to_path(
                            context.instance,
                            "/interaction_profiles/khr/simple_controller",
                        ),
                        count_suggested_bindings=len(suggested_bindings),
                        suggested_bindings=suggested_bindings,
                    ),
                )
                xr.suggest_interaction_profile_bindings(
                    instance=context.instance,
                    suggested_bindings=xr.InteractionProfileSuggestedBinding(
                        interaction_profile=xr.string_to_path(
                            context.instance,
                            "/interaction_profiles/htc/vive_controller",
                        ),
                        count_suggested_bindings=len(suggested_bindings),
                        suggested_bindings=suggested_bindings,
                    ),
                )

                action_spaces = [
                    xr.create_action_space(
                        session=context.session,
                        create_info=xr.ActionSpaceCreateInfo(
                            action=controller_pose_action,
                            subaction_path=controller_paths[0],
                        ),
                    ),
                    xr.create_action_space(
                        session=context.session,
                        create_info=xr.ActionSpaceCreateInfo(
                            action=controller_pose_action,
                            subaction_path=controller_paths[1],
                        ),
                    ),
                ]

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
                    if flags & xr.ViewStateFlags.ORIENTATION_VALID_BIT:
                        self.pose_quat = views[0].pose
                    else:
                        self.pose = None

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
                    if context.session_state == xr.SessionState.FOCUSED:
                        active_action_set = xr.ActiveActionSet(
                            action_set=context.default_action_set,
                            subaction_path=xr.NULL_PATH,
                        )
                        xr.sync_actions(
                            session=context.session,
                            sync_info=xr.ActionsSyncInfo(
                                count_active_action_sets=1,
                                active_action_sets=ctypes.pointer(active_action_set),
                            ),
                        )
                        for index, space in enumerate(action_spaces):
                            space_location = xr.locate_space(
                                space=space,
                                base_space=context.space,
                                time=frame_state.predicted_display_time,
                            )
                            if (
                                space_location.location_flags
                                & xr.SPACE_LOCATION_POSITION_VALID_BIT
                            ):

                                if index == 0:
                                    self.controller["left"] = space_location.pose
                                elif index == 1:
                                    self.controller["right"] = space_location.pose

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
