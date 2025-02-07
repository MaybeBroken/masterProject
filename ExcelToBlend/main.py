# This script reads a file and generates a blender model based off of the file

import os
import csv
import bpy  # type: ignore
import math
from random import randint
from bpy_extras.io_utils import ImportHelper  # type: ignore
from bpy.types import Operator  # type: ignore
from bpy.props import StringProperty  # type: ignore

bl_info = {
    "name": "CSV Planet Importer",
    "blender": (4, 0, 0),
    "category": "Import-Export",
    "version": (0, 0, 2),
    "author": "MaybeBroken",
    "description": "Import a solar system CSV file to generate planet meshes.",
}


class ImportCSV(Operator, ImportHelper):
    bl_idname = "import_csv.some_data"
    bl_label = "Import CSV"
    filename_ext = ".csv"
    filter_glob: StringProperty(
        default="*.csv",
        options={"HIDDEN"},
        maxlen=255,
    ) # type: ignore

    def execute(self, context=None):
        FILEPATH = self.filepath
        with open(FILEPATH) as file:
            data = file.readlines()

        with open(FILEPATH, "w") as file:
            file.writelines(
                line
                for line in data
                if line
                != ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,\n"
            )

        file = csv.reader(open(FILEPATH))

        fileData = []

        for row in file:
            _row = []
            for column in row:
                _row.append(column)
            fileData.append(_row)

        INDEXES = []
        DATA = {}

        for id in range(len(fileData[1])):
            fileData[1][id] += f" {fileData[2][id]}"

        for id in fileData[1]:
            if id != " ":
                INDEX = fileData[1].index(id)
                INDEXES.append(INDEX)
                DATA[id] = []
                print(f"Found {id} at {INDEX}")

        del fileData[0]
        INDEXDATA = fileData[0]
        del fileData[0]

        for INDEX in INDEXES:
            ID = INDEXDATA[INDEX]
            for row in fileData:
                try:
                    DATA[ID].append(row[INDEX])
                except:
                    None

        PLANETNUM = 0

        for name in DATA:
            if name == "Mass (Earth masses)":
                for data in DATA[name]:
                    try:
                        if float(data) > 0:
                            PLANETNUM += 1
                    except:
                        None

        print()
        print(f"Found {PLANETNUM} planets\n")

        # Create meshes in blender

        PLANETIDS = []
        for radius in DATA["Radius (Earth radii)"]:
            if (
                radius != " "
                and radius != ""
                and radius != "0"
                and radius != "0.0"
                and radius != "(Earth radii)"
            ):
                planetId = randint(0, 100000000)
                if float(radius) > 0:
                    _radius = float(radius)
                    segments = 150
                    rings = 150
                    verts, faces = create_uv_sphere(_radius, segments, rings)
                    if str(planetId) in bpy.data.objects:
                        bpy.data.objects.remove(
                            bpy.data.objects[str(planetId)], do_unlink=True
                        )
                    add_mesh(str(planetId), verts, faces)
                    PLANETIDS.append(planetId)

        planetIndex = 0
        for au in DATA["Semimajor axis (AU)"]:
            if (
                au != " "
                and au != "0"
                and au != "0.0"
                and au != "axis (AU)"
                and au != ""
            ):
                au = float(au) * 10
                planetId = PLANETIDS[planetIndex]
                if str(planetId) in bpy.data.objects:
                    obj = bpy.data.objects[str(planetId)]
                else:
                    continue
                randomRotation = randint(0, 360)
                circle_radius = float(au)
                verts, edges = create_circle(circle_radius, 100)
                add_mesh(f"orbit-{planetId}", verts, [], edges)
                obj.location = (
                    circle_radius * math.cos(math.radians(randomRotation)),
                    circle_radius * math.sin(math.radians(randomRotation)),
                    0,
                )
                planetIndex += 1

        return {"FINISHED"}


def menu_func_import(self, context):
    self.layout.operator(ImportCSV.bl_idname, text="Import CSV")


def register():
    bpy.utils.register_class(ImportCSV)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportCSV)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
    # bpy.ops.import_csv.some_data('INVOKE_DEFAULT')  # Removed to run from import menu


def add_mesh(name, verts, faces, edges=None, col_name="Collection"):
    if edges is None:
        edges = []
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    if name in bpy.data.meshes:
        bpy.data.meshes.remove(bpy.data.meshes[name], do_unlink=True)
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(mesh.name, mesh)
    col = bpy.data.collections[col_name]
    col.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    mesh.from_pydata(verts, edges, faces)


def create_circle(radius, segments):
    verts = []
    edges = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        verts.append((x, y, 0))
        edges.append((i, (i + 1) % segments))
    return verts, edges


def create_uv_sphere(radius, segments, rings):
    verts = []
    faces = []
    for i in range(rings + 1):
        lat = math.pi * i / rings
        for j in range(segments):
            lon = 2 * math.pi * j / segments
            x = radius * math.sin(lat) * math.cos(lon)
            y = radius * math.sin(lat) * math.sin(lon)
            z = radius * math.cos(lat)
            verts.append((x, y, z))
    for i in range(rings):
        for j in range(segments):
            next_i = (i + 1) % (rings + 1)
            next_j = (j + 1) % segments
            faces.append(
                [
                    i * segments + j,
                    next_i * segments + j,
                    next_i * segments + next_j,
                    i * segments + next_j,
                ]
            )
    return verts, faces


if __name__ == "__main__":
    unregister()
    ImportCSV.filepath = os.path.join(os.path.dirname(__file__.replace("\\test.blend", "")), "file.csv")
    ImportCSV.execute(ImportCSV)
