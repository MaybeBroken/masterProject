# Module to handle intersection of meshes and report their collisions

from .intersection import (
    do_meshes_intersect,
    compute_intersection_points,
    panda_mesh_to_numpy,
)
from panda3d.core import GeomNode, Sphere
from time import sleep


def create_uv_sphere(radius, resolution: tuple = (30, 30)):
    """
    Create a UV sphere mesh with the given radius and position.
    """
    sphere = Sphere(radius, resolution[0], resolution[0])
    node = GeomNode("sphere")
    node.add_geom(sphere)
    return node


class BaseActor:
    def __init__(self, radius, position, mesh=None):
        self.radius = radius
        self.position = position
        if not mesh:
            mesh = create_uv_sphere(radius)
        self.mesh = mesh
        self.collision_report = []
        return self


class BaseCollider:
    def __init__(self, radius, position, mesh=None):
        self.radius = radius
        self.position = position
        if not mesh:
            mesh = create_uv_sphere(radius)
        self.mesh = mesh
        return self


class ComplexActor:
    def __init__(self, mesh):
        self.mesh = mesh
        self.array = panda_mesh_to_numpy(mesh)
        self.collision_report = []
        return self


class ComplexCollider:
    def __init__(self, mesh):
        self.mesh = mesh
        self.array = panda_mesh_to_numpy(mesh)
        return self


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
        return self


class Mgr:
    def __init__(self):
        self.base_actors: list[BaseActor] = []
        self.complex_actors: list[ComplexActor] = []
        self.base_colliders: list[BaseCollider] = []
        self.complex_colliders: list[ComplexCollider] = []
        self.reportedCollisions: list[CollisionReport] = []

    def add_base_actor(self, radius, position, mesh=None):
        actor = BaseActor(radius, position, mesh)
        self.base_actors.append(actor)
        return actor

    def add_complex_actor(self, mesh):
        actor = ComplexActor(mesh)
        self.complex_actors.append(actor)
        return actor

    def add_base_collider(self, radius, position, mesh=None):
        collider = BaseCollider(radius, position, mesh)
        self.base_colliders.append(collider)
        return collider

    def add_complex_collider(self, mesh):
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
        if len(self.base_actors) == 0 and len(self.complex_actors) == 0:
            return self.reportedCollisions
        if len(self.base_colliders) != 0:
            for actor in self.base_actors:
                for collider in self.base_colliders:
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
