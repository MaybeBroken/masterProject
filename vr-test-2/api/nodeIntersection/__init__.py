# Module to handle intersection of meshes and report their collisions

from .intersection import (
    do_meshes_intersect,
    compute_intersection_points,
    panda_mesh_to_numpy,
)
from panda3d.core import (
    NodePath,
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexFormat,
    GeomVertexData,
    GeomVertexWriter,
)
from time import sleep
import numpy as np


def Sphere(radius, lat, lon):
    """
    Create a UV sphere mesh with the given radius and position.
    """

    # Create vertex data format
    format = GeomVertexFormat.get_v3n3c4t2()
    vdata = GeomVertexData("vertices", format, Geom.UH_static)

    # Create vertex writer
    vertex_writer = GeomVertexWriter(vdata, "vertex")
    normal_writer = GeomVertexWriter(vdata, "normal")
    color_writer = GeomVertexWriter(vdata, "color")
    texcoord_writer = GeomVertexWriter(vdata, "texcoord")

    # Generate vertices
    for i in range(lat + 1):
        lat_angle = np.pi * i / lat
        for j in range(lon + 1):
            lon_angle = 2 * np.pi * j / lon
            x = radius * np.sin(lat_angle) * np.cos(lon_angle)
            y = radius * np.sin(lat_angle) * np.sin(lon_angle)
            z = radius * np.cos(lat_angle)
            vertex_writer.add_data3f(x, y, z)
            normal_writer.add_data3f(x / radius, y / radius, z / radius)
            color_writer.add_data4f(1.0, 1.0, 1.0, 1.0)
            texcoord_writer.add_data2f(j / lon, i / lat)

    # Create triangles
    tris = []
    for i in range(lat):
        for j in range(lon):
            tris.append(
                (
                    i * (lon + 1) + j,
                    (i + 1) * (lon + 1) + j,
                    (i + 1) * (lon + 1) + (j + 1),
                )
            )
            tris.append(
                (
                    i * (lon + 1) + j,
                    (i + 1) * (lon + 1) + (j + 1),
                    i * (lon + 1) + (j + 1),
                )
            )

    # Create geom and add triangles
    geom = Geom(vdata)
    triangles = GeomTriangles(Geom.UH_static)
    for tri in tris:
        triangles.add_vertices(*tri)
    geom.add_primitive(triangles)
    node = GeomNode("sphere")
    node.add_geom(geom)
    return node


def create_uv_sphere(radius, resolution: tuple = (30, 30)):
    """
    Create a UV sphere mesh with the given radius and position.
    """
    sphere = Sphere(radius, resolution[0], resolution[0])
    sphereNode = NodePath("sphere")
    sphereNode.attach_new_node(sphere)
    return sphereNode


class BaseActor:
    def __init__(self, radius, position, mesh=None):
        self.radius = radius
        self.position = position
        self.sphere = create_uv_sphere(radius)
        self.mesh = mesh
        self.collision_report = []


class BaseCollider:
    def __init__(self, radius, position, mesh=None):
        self.radius = radius
        self.position = position
        self.sphere = create_uv_sphere(radius)
        self.mesh = mesh


class ComplexActor:
    def __init__(self, mesh):
        self.mesh = mesh
        self.array = panda_mesh_to_numpy(mesh)
        self.collision_report = []


class ComplexCollider:
    def __init__(self, mesh):
        self.mesh = mesh
        self.array = panda_mesh_to_numpy(mesh)


class CollisionReport:
    def __init__(self, actor, collider, actor_position, collider_position):
        self.actor = actor
        self.collider = collider
        self.actor_position = actor_position
        self.collider_position = collider_position
        self.report = {
            "actor": actor,
            "collider": collider,
            "actor_position": actor_position,
            "collider_position": collider_position,
        }


class Mgr:
    def __init__(self):
        self.base_actors: list[BaseActor] = []
        self.complex_actors: list[ComplexActor] = []
        self.base_colliders: list[BaseCollider] = []
        self.complex_colliders: list[ComplexCollider] = []
        self.reportedCollisions: list[CollisionReport] = []

    def add_base_actor(self, radius, position, mesh=None) -> BaseActor:
        actor = BaseActor(radius, position, mesh)
        self.base_actors.append(actor)
        return actor

    def add_complex_actor(self, mesh) -> ComplexActor:
        actor = ComplexActor(mesh)
        self.complex_actors.append(actor)
        return actor

    def add_base_collider(self, radius, position, mesh=None) -> BaseCollider:
        collider = BaseCollider(radius, position, mesh)
        self.base_colliders.append(collider)
        return collider

    def add_complex_collider(self, mesh) -> ComplexCollider:
        collider = ComplexCollider(mesh)
        self.complex_colliders.append(collider)
        return collider

    def remove_base_actor(self, actor):
        self.base_actors.remove(actor)
        return actor

    def remove_complex_actor(self, actor):
        self.complex_actors.remove(actor)
        return actor

    def remove_base_collider(self, collider):
        self.base_colliders.remove(collider)
        return collider

    def remove_complex_collider(self, collider):
        self.complex_colliders.remove(collider)
        return collider

    def update(self):
        for report in self.reportedCollisions:
            report.actor.collision_report.remove(report)
            report.collider.collision_report.remove(report)

        if len(self.base_actors) == 0 and len(self.complex_actors) == 0:
            return self.reportedCollisions
        if len(self.base_colliders) != 0:
            for actor in self.base_actors:
                if actor.mesh is not None:
                    actor.position = actor.mesh.getPos(base.render)  # type: ignore
                    actor.sphere.setPos(actor.position)
                for collider in self.base_colliders:
                    if collider.mesh is not None:
                        collider.position = collider.mesh.getPos(base.render)  # type: ignore
                        collider.sphere.setPos(collider.position)
                    for positionIndex in range(len(actor.position)):
                        if (
                            actor.position[positionIndex]
                            - collider.position[positionIndex]
                        ) ** 2 < (actor.radius + collider.radius) ** 2:
                            self.reportedCollisions.append(
                                CollisionReport(
                                    actor,
                                    collider,
                                    actor.position,
                                    collider.position,
                                )
                            )
        if len(self.complex_colliders) != 0:
            for actor in self.complex_actors:
                for collider in self.complex_colliders:
                    if do_meshes_intersect(actor.array, collider.array):
                        intersection_points = compute_intersection_points(
                            actor.array, collider.array
                        )
                        self.reportedCollisions.append(
                            CollisionReport(
                                actor,
                                collider,
                                intersection_points,
                                intersection_points,
                            )
                        )

    def execute(self, frame_rate=60):
        while True:
            self.update()
            sleep(1 / frame_rate)

    def start(self, frame_rate=60, threaded=True):
        if threaded:
            from threading import Thread

            thread = Thread(target=self.execute, args=(frame_rate,))
            thread.start()
            return thread
        else:
            self.execute(frame_rate)


Mgr = Mgr()
