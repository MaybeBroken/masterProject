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


def getTotalDistance(actor, collider):
    """
    Calculate the total distance between two actors or colliders.
    """
    return np.linalg.norm(np.array(actor.position) - np.array(collider.position))


class BaseActor:
    def __init__(self, radius: float, position: tuple[3], name: str, mesh=None):
        self.radius: float = radius
        self.position: tuple[3] = position
        self.sphere = create_uv_sphere(radius)
        self.mesh: NodePath = mesh
        self.name: str = name
        self.collision_report: CollisionReport = None


class BaseCollider:
    def __init__(self, radius: float, position: tuple[3], name: str, mesh=None):
        self.radius: float = radius
        self.position: tuple[3] = position
        self.sphere: NodePath = create_uv_sphere(radius)
        self.mesh: NodePath = mesh
        self.name: str = name
        self.collision_report: CollisionReport = None


class ComplexActor:
    def __init__(self, mesh: NodePath, name: str):
        self.mesh: NodePath = mesh
        self.array = panda_mesh_to_numpy(mesh)
        self.name: str = name
        self.collision_report: CollisionReport = None


class ComplexCollider:
    def __init__(self, mesh: NodePath, name: str):
        self.mesh: NodePath = mesh
        self.array = panda_mesh_to_numpy(mesh)
        self.name: str = name
        self.collision_report: CollisionReport = None


class CollisionReport:
    def __init__(
        self,
        actor: BaseActor,
        collider: BaseCollider,
        actor_position: tuple[3],
        collider_position: tuple[3],
    ):
        self.actor = actor
        self.collider = collider
        self.actorStr = actor.name
        self.colliderStr = collider.name
        self.actor_position = actor_position
        self.collider_position = collider_position
        self.report = {
            "actor": actor,
            "collider": collider,
            "actor_position": actor_position,
            "collider_position": collider_position,
        }

    def __str__(self):
        return f"CollisionReport(actor: {self.actorStr}, collider: {self.colliderStr}, actor_position: {self.actor_position}, collider_position: {self.collider_position})"

    def __repr__(self):
        return self.__str__()


class Mgr:
    def __init__(self):
        self.base_actors: list[BaseActor] = []
        self.complex_actors: list[ComplexActor] = []
        self.base_colliders: list[BaseCollider] = []
        self.complex_colliders: list[ComplexCollider] = []
        self.reportedCollisions: list[CollisionReport] = []

    def add_base_actor(self, radius, position, name, mesh=None) -> BaseActor:
        actor = BaseActor(radius, position, name, mesh)
        self.base_actors.append(actor)
        return actor

    def add_complex_actor(self, name, mesh) -> ComplexActor:
        actor = ComplexActor(mesh, name)
        self.complex_actors.append(actor)
        return actor

    def add_base_collider(self, radius, position, name, mesh=None) -> BaseCollider:
        collider = BaseCollider(radius, position, name, mesh)
        self.base_colliders.append(collider)
        return collider

    def add_complex_collider(self, mesh, name) -> ComplexCollider:
        collider = ComplexCollider(mesh, name)
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
        del self.reportedCollisions[:]
        for actor in self.base_actors:
            actor.collision_report = None
        for collider in self.base_colliders:
            collider.collision_report = None

        if len(self.base_actors) == 0 and len(self.complex_actors) == 0:
            return self.reportedCollisions
        if len(self.base_colliders) != 0:
            collider: BaseCollider
            for collider in self.base_colliders:
                if collider.mesh is not None:
                    collider.position = collider.mesh.getPos(base.render)  # type: ignore
                    collider.sphere.setPos(collider.position)
                actor: BaseActor
                for actor in self.base_actors:
                    if actor.mesh is not None:
                        actor.position = actor.mesh.getPos(base.render)  # type: ignore
                        actor.sphere.setPos(actor.position)
                    for positionIndex in range(len(actor.position)):
                        if (
                            getTotalDistance(actor, collider)
                            <= actor.radius + collider.radius
                        ):
                            colReport = CollisionReport(
                                actor,
                                collider,
                                actor.position,
                                collider.position,
                            )
                            self.reportedCollisions.append(colReport)
                            actor.collision_report = colReport
                            collider.collision_report = colReport
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
                        actor.collision_report = CollisionReport(
                            actor,
                            collider,
                            intersection_points,
                            intersection_points,
                        )
                        collider.collision_report = CollisionReport(
                            collider,
                            actor,
                            intersection_points,
                            intersection_points,
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
