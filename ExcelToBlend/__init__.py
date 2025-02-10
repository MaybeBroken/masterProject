# This script reads a file and generates a blender model based off of the file

import os
import bpy  # type: ignore
import math
from random import randint
from bpy_extras.io_utils import ImportHelper  # type: ignore
from bpy.types import Operator, Panel  # type: ignore
from bpy.props import StringProperty  # type: ignore
import logging
import sys

if sys.platform != "win32":
    raise OSError("This script is only supported on Windows.")

# Set up logging to Blender console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bl_info = {
    "name": "Excel Planet Importer",
    "blender": (4, 0, 0),
    "location": "File > Import",
    "category": "Import-Export",
    "version": (0, 0, 2),
    "author": "MaybeBroken",
    "description": "Import a solar system Excel file to generate planet meshes.",
}
import subprocess
from threading import Thread
import threading
from time import sleep

jarPath = os.path.abspath(__file__).replace("__init__.py", "excelToCsv.jar")
batPath = os.path.abspath(__file__).replace("__init__.py", "convert.bat")

# Sub-Program to convert the actual excel file to csv
batProgram = f"""
@echo off
echo Converting %1 to %2...
java -jar "{jarPath}" --input %1 --sheet-name "System Builder" >> %2
echo Finished conversion, file saved to %2
"""


# Wrapper function to call the sub-program
def convert_excel_to_csv(input_file, output_file):
    """Takes an `input_file` and `output_file`,and converts the input file to a csvfile at the specified output path."""
    output_file = os.path.abspath(output_file)
    input_file = os.path.abspath(input_file)

    # Make sure the Converter is in the same directory as this script
    if not os.path.exists(jarPath):
        raise FileNotFoundError("The required excelToCsv.jar file is missing.")

    # Make sure the input file exists
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"The input file {input_file} does not exist.")

    # Run the program if the output file does not exist, otherwise read the file and return it
    if os.path.exists(output_file):
        os.remove(output_file)

    # Create the batch file
    with open(batPath, "w") as f:
        f.write(batProgram)

    # Run the batch file
    subprocess.run([batPath, input_file, output_file])

    return output_file


def convert_excel(filepath):
    input_files = filepath

    # Create the output folder if it doesn't exist
    output_folder = os.path.join(
        os.path.expanduser("~"), "AppData", "Roaming", "ExcelToBlend"
    )
    csv_output_folder = os.path.join(output_folder, "CSV_Output")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    if not os.path.exists(csv_output_folder):
        os.makedirs(csv_output_folder)

    # Limit the number of concurrent threads to 6
    semaphore = threading.Semaphore(6)
    CSV_DATA_PATH = None

    # Iterate through the excel files
    for input_file in input_files:

        def _thread(input_file):
            nonlocal CSV_DATA_PATH
            with semaphore:
                # Convert the excel file to csv
                output_file = os.path.join(
                    csv_output_folder,
                    f"{os.path.basename(input_file).removesuffix('.xlsx')}.csv",
                )
                CSV_DATA_PATH = convert_excel_to_csv(input_file, output_file)

        # Start the thread
        sleep(0.5)
        Thread(
            target=_thread,
            args=(input_file if isinstance(input_file, list) else filepath,),
        ).start()

    for thread in threading.enumerate():
        if thread is not threading.current_thread():
            thread.join()

    # Wait for the batch file to finish, then delete it
    if os.path.exists("convert.bat"):
        os.remove("convert.bat")

    return CSV_DATA_PATH


class MessagePopup(Operator):
    bl_idname = "wm.message_popup"
    bl_label = "Message"

    message: StringProperty()  # type: ignore

    def execute(self, context):
        self.report({"INFO"}, self.message)
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def show_message(message):
    bpy.ops.wm.message_popup("INVOKE_DEFAULT", message=message)


class ImportCSV(Operator, ImportHelper):
    bl_idname = "import_csv.some_data"
    bl_label = "Import Excel"
    filename_ext = ".xlsx"
    filter_glob: StringProperty(
        default="*.xlsx",
        options={"HIDDEN"},
        maxlen=255,
    )  # type: ignore

    def execute(self, context):
        # Execute the main function in a separate thread
        Thread(target=self._sub_execute_thread, args=(context,)).start()
        return {"FINISHED"}

    def _sub_execute_thread(self, context=None):
        FILEPATH = convert_excel(os.path.abspath(self.filepath))
        with open(FILEPATH, errors="ignore") as file:
            data = file.read()

        with open(FILEPATH, "w", errors="ignore") as file:
            fileData = []
            for line in data.splitlines():
                fileData.append(",".join(line.split(",")[4:])[1:])
            del fileData[0]
            del fileData[1]
            file.write("\n".join(fileData))

        file = [line.split(",") for line in fileData]

        fileData = []

        for row in file:
            _row = []
            for column in row:
                _row.append(column.strip())
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
                logger.info(f"Found {id} at {INDEX}")

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
        print(f"Sun radius is {fileData[7][3]}")
        print()
        logger.info(f"Found {PLANETNUM} planets\n")

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
                planetId = f"planet-{randint(0, 100000000)}"
                if float(radius) > 0:
                    _radius = float(radius)
                    segments = 150
                    rings = 150
                    verts, faces = create_uv_sphere(_radius / 3.3, segments, rings)
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
                circle_radius = float(au) * 40
                planetId = PLANETIDS[planetIndex]
                if str(planetId) in bpy.data.objects:
                    obj = bpy.data.objects[str(planetId)]
                else:
                    continue
                randomRotation = randint(0, 360)
                verts, edges = create_circle(circle_radius, 100)
                add_mesh(f"orbit-{planetId}", verts, [], edges)
                obj.location = (
                    circle_radius * math.cos(math.radians(randomRotation)),
                    circle_radius * math.sin(math.radians(randomRotation)),
                    0,
                )
                create_material(
                    f"planetMat-{planetId}",
                    (0.5, 0.5, 0.5, 1),
                )
                apply_material(obj, bpy.data.materials[f"planetMat-{planetId}"])
                atmosphere = duplicate_object(
                    obj,
                    f"atmosphere-{planetId}",
                    (0, 0, 0),
                    (1.1, 1.1, 1.1),
                )
                apply_material(
                    atmosphere,
                    create_volume_material(
                        f"atmosphere-{planetId}",
                        (0.38, 0.5, 1, 1),
                        35,
                    ),
                )
                set_parent_for_objects(
                    [obj, atmosphere], bpy.data.objects[f"orbit-{planetId}"]
                )
                random_rotation_x = 360 - randint(0, 720)
                random_rotation_y = 360 - randint(0, 720)
                large_rotation_chance = randint(0, 10)
                if large_rotation_chance == 0:
                    random_rotation_x *= randint(1, 10)
                    random_rotation_y *= randint(1, 10)
                rotate_object(
                    bpy.data.objects[f"orbit-{planetId}"],
                    (
                        math.radians(random_rotation_x / 100),
                        math.radians(random_rotation_y / 100),
                        0,
                    ),
                )
                planetIndex += 1

        verts, faces = create_uv_sphere(float(fileData[7][3]), 150, 150)
        edges = []
        sunId = randint(0, 100000000)
        add_mesh(f"sun-{sunId}", verts, faces, edges)
        create_emission_material(
            f"sun-{sunId}",
            (1, 1, 0.5, 1),
            100000,
        )
        apply_material(
            bpy.data.objects[f"sun-{sunId}"], bpy.data.materials[f"sun-{sunId}"]
        )
        flare = duplicate_object(
            bpy.data.objects[f"sun-{sunId}"],
            f"flare-{sunId}",
            (0, 0, 0),
            (1.05, 1.05, 1.05),
        )
        apply_material(
            flare,
            create_volume_material(
                f"flare-{sunId}",
                (1, 0.7, 0.1, 1),
                1.3,
            ),
        )

        return {"FINISHED"}


def menu_func_import(self, context):
    self.layout.operator(ImportCSV.bl_idname, text="Import Excel")


def register():
    bpy.utils.register_class(ImportCSV)
    bpy.utils.register_class(MessagePopup)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportCSV)
    bpy.utils.unregister_class(MessagePopup)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()


def add_mesh(name, verts, faces, edges=None, col_name="Collection"):
    """Add a mesh to the specified collection."""
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
    """Create a circle mesh."""
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
    """Create a UV sphere mesh."""
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


def create_material(name, color):
    """Create a material with the specified color."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    return mat


def create_emission_material(name, color, strength):
    """Create an emission material with the specified color and strength."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    output_node = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    emission_node = mat.node_tree.nodes.new("ShaderNodeEmission")
    emission_node.inputs["Strength"].default_value = strength
    emission_node.inputs["Color"].default_value = color
    mat.node_tree.links.new(
        emission_node.outputs["Emission"], output_node.inputs["Surface"]
    )
    return mat


def create_volume_material(name, color, density):
    """Create a volume material with the specified color and density."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    output_node = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    volume_node = mat.node_tree.nodes.new("ShaderNodeVolumePrincipled")
    volume_node.inputs["Density"].default_value = density
    volume_node.inputs["Color"].default_value = color
    mat.node_tree.links.new(volume_node.outputs["Volume"], output_node.inputs["Volume"])
    return mat


def duplicate_object(obj, name, location, scale):
    """Duplicate the specified object."""
    new_obj = obj.copy()
    new_obj.data = obj.data.copy()
    new_obj.location = (
        obj.location[0] + location[0],
        obj.location[1] + location[1],
        obj.location[2] + location[2],
    )
    new_obj.scale = (
        obj.scale[0] * scale[0],
        obj.scale[1] * scale[1],
        obj.scale[2] * scale[2],
    )
    new_obj.name = name
    bpy.context.collection.objects.link(new_obj)
    return new_obj


def apply_material(obj, material):
    """Apply the material to the object."""
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)


def reparent(obj, parent):
    """Reparent the object to a new parent."""
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()


def set_parent_for_objects(objects: list, parent):
    """Set the parent for a list of objects."""
    for obj in objects:
        reparent(obj, parent)


def clear_materials(obj):
    """Clear all materials from the object."""
    if obj.data.materials:
        obj.data.materials.clear()


def delete_all_objects():
    """Delete all objects in the current scene."""
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def rotate_object(obj, rotation):
    """Rotate the specified object."""
    obj.rotation_euler = rotation


# if __name__ == "__main__":
#     unregister()
#     ImportCSV.filepath = os.path.join(
#         os.path.dirname(__file__.replace("\\test1.blend", "")), "file.csv"
#     )
#     ImportCSV.execute(ImportCSV)
