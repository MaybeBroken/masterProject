# This script reads a file and generates a blender model based off of the file

import os
import csv
import bpy
import math

with open("/Users/david.sponseller/Code/masterProject/ExcelToBlend/file.csv") as file:
    data = file.readlines()

with open(
    "/Users/david.sponseller/Code/masterProject/ExcelToBlend/file.csv", "w"
) as file:
    file.writelines(
        line
        for line in data
        if line != ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,\n"
    )

file = csv.reader(
    open("/Users/david.sponseller/Code/masterProject/ExcelToBlend/file.csv")
)

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


def add_mesh(name, verts, faces, edges=None, col_name="Collection"):
    if edges is None:
        edges = []
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(mesh.name, mesh)
    col = bpy.data.collections[col_name]
    col.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    mesh.from_pydata(verts, edges, faces)


def create_circle(radius, segments):
    verts = []
    faces = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        verts.append((x, y, 0))
    faces.append([i for i in range(segments)])
    return verts, faces


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


planetId = 0
for radius in DATA["Radius (Earth radii)"]:
    if (
        radius != " "
        and radius != ""
        and radius != "0"
        and radius != "0.0"
        and radius != "(Earth radii)"
    ):
        if float(radius) > 0:
            _radius = float(radius)
            segments = 30
            rings = 30
            verts, faces = create_uv_sphere(_radius, segments, rings)
            add_mesh(str(planetId), verts, faces)
            planetId += 1

planetId = 0
for au in DATA["Semimajor axis (AU)"]:
    if au != " " and au != "0" and au != "0.0" and au != "axis (AU)" and au != "":
        if float(au) > 0:
            obj = bpy.data.objects[str(planetId)]
            obj.location = (float(au), 0, 0)
            planetId += 1
