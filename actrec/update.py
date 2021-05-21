# region Import
# external modules
from typing import Optional
import requests
import json
import base64
import os
import zipfile
import subprocess
from collections import defaultdict

# blender modules
import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import BoolProperty, IntProperty, StringProperty
from bpy_extras.io_utils import ExportHelper

# realtive imports
from .config import config
from .log import logger
from .preferences import AR_preferences
# endregion

classes = []

# region functions
def on_start() -> None:
    check_for_update()

def get_json_from_content(content : bytes) -> dict:
    data = json.loads(content)
    content = base64.b64decode(data["content"]).decode("utf-8")
    return json.loads(content)

def check_for_update() -> tuple:
        download_file = get_online_download_file()
        if download_file is None:
            return (False, "No Internet Connection")
        old_download_file = get_local_download_file()
        if download_file["version"] > old_download_file["version"]:
            return (True, download_file["version"])
        else:
            return (False, old_download_file["version"])

def start_update() -> bool:
    download_paths = get_download_paths()
    if download_paths is None:
        return False
    for path in download_paths:
        AR_preferences.update_responds[path] = requests.get(config["repoSource_URL"] + path, stream= True)

def update(AR, update_responds: dict, download_chunks: dict) -> bool:
    finished_downloaded = True
    complet_length = 0
    complet_progress = 0
    for path in update_responds:
        res = update_responds[path]
        total_length = res.headers.get('content-length', None)
        complet_length += total_length
        if total_length is None:
            download_chunks[path]["chunks"].append(res.content)
        else:
            for chunk in res.iter_content(chunk_size=4096):
                download_chunks[path]["chunks"].append(chunk)
                length_chunk = len(chunk)
                download_chunks[path]["progress_length"] += length_chunk
                complet_progress += length_chunk
            finished_progress = download_chunks[path]["progress_length"] == total_length
            if finished_progress:
                res.close()
                del update_responds[path]
            finished_downloaded = finished_progress and finished_downloaded
    AR.update_progress = 100 * complet_progress / complet_length
    return finished_downloaded

def install_update(AR, download_chunks: dict) -> None:
    zip_path = os.path.join(bpy.app.tempdir, "AR_Update/" + __package__ +".zip")
    zip_it = zipfile.ZipFile(zip_path, 'w')
    for path in download_chunks:
        zip_it.writestr(path, get_json_from_content(b''.join(download_chunks['path']["chunks"])))
    bpy.ops.preferences.addon_install(filepath= zip_path)
    version = tuple(AR.version.split("."))
    logger.info("Updated Action Recorder to Version: " + str(version))
    os.remove(zip_path)
    update_download_file(download_chunks.keys(), version)
    download_chunks.clear()

def get_online_download_file() -> Optional[dict]:
    try:
        res = requests.get(config["checkSource_URL"])
        logger.info("downloaded: download_file")
        return get_json_from_content(res.content)
    except Exception as err:
        logger.warning("no Connecation (" + err + ")")
        return None

def get_local_download_file() -> dict:
    path = os.path.join(AR_preferences.addon_directory, "download_file.json")
    if not os.path.exists(path):
        new_file = open(path, "w", encoding= 'utf-8')
        new_file.write("{}")
        new_file.close()
    download_file = open(path, "r", encoding= 'utf-8')
    download_text = download_file.read()
    download_file.close()
    return json.loads(download_text)

def update_download_file(download_list: list, current_version: tuple) -> None:
    download_file = get_local_download_file()
    files = []
    for path in download_list: 
        files.append({path : current_version})
    download_file["files"] = files
    download_file["version"] = current_version
    with open("download_file.json", "w", encoding= "utf-8") as open_files:
        open_files.write(json.dumps(download_file))

def get_download_paths() -> Optional[list]:
    download_file = get_online_download_file()["files"]
    if download_file is None:
        return None
    old_download_file = get_local_download_file()["files"]
    download_list = []
    old_keys = old_download_file.keys()
    for key in download_file.keys():
        key_exists = key in old_keys 
        if (key_exists and download_file[key] > old_download_file[key]) or not key_exists:
            download_list.append(key)
    return download_list

def draw_update_button(layout, AR):
    if AR.update_progress >= 0:
        row = layout.row()
        row.enable = False
        row.prop(AR, 'update_progress', text= "Progress", slider=True)
    else:
        layout.operator(AR_OT_update.bl_idname, text= 'Update')
# endregion functions

# region Operator
class AR_OT_update_check(Operator):
    bl_idname = "ar.update_check"
    bl_label = "Check for Update"
    bl_description = "check for available update"



    def execute(self, context):
        update = check_for_update()
        AR = context.preferences.addons[__package__].preferences
        AR.Update = update[0]
        if isinstance(update[1], str):
            AR.version = update[1]
        else:
            AR.version = ".".join([str(i) for i in update[1]])
        return {"FINISHED"}
classes.append(AR_OT_update_check)

class AR_OT_update(Operator):
    bl_idname = "ar.update"
    bl_label = "Update"
    bl_description = "install the new version"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return AR.update

    def invoke(self, context, event):
        launch = start_update()
        if launch:
            return {'RUNNING_MODAL'}
        self.report({'ERROR'}, "No Internet Connection")
        return {'CANCELLED'}

    def modal(self, context, event):
        AR = context.preferences.addons[__package__].preferences
        if update(AR, AR_preferences.update_responds, AR_preferences.update_data_chunks):
            return self.execute(context)
        return {'PASS_THROUGH'}

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        AR.update = False
        AR.restart = True
        install_update(AR, AR_preferences.update_data_chunks)
        AR.update_progress = -1
        bpy.ops.ar.show_restart_menu('INVOKE_DEFAULT')
        return {"FINISHED"}
classes.append(AR_OT_update)

class AR_OT_restart(Operator, ExportHelper):
    bl_idname = "ar.restart"
    bl_label = "Restart Blender"
    bl_description = "Restart Blender"

    save : BoolProperty(default= False)
    filename_ext = ".blend"
    filter_folder : BoolProperty(default= True, options={'HIDDEN'})
    filter_blender : BoolProperty(default= True, options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return AR.restart

    def execute(self, context):
        path = bpy.data.filepath
        if self.save:
            if path == '':
                bpy.ops.wm.save_mainfile(filepath= self.filepath)
            else:
                bpy.ops.wm.save_mainfile(filepath= path)
        subprocess.Popen([bpy.app.binary_path, path])
        bpy.ops.wm.quit_blender()
        return {"FINISHED"}

    def invoke(self, context, event):
        if self.save and bpy.data.filepath == '':
            return ExportHelper.invoke(self, context, event)
        else:
            return self.execute(context)
classes.append(AR_OT_restart)

class AR_OT_show_restart_menu(Operator):
    bl_idname = "ar.show_restart_menu"
    bl_label = "Restart Blender"
    bl_description = "Restart Blender"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return AR.restart
    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text= "You need to restart Blender to complete the Update")
        row = self.layout.row()
        row.operator(AR_OT_restart.bl_idname, text= "Save & Restart").save = True
        row.operator(AR_OT_restart.bl_idname, text= "Restart")

    def execute(self, context):
        context.window_manager.popup_menu(self.draw, title= "Action Recorder Restart")
        return {"FINISHED"}
classes.append(AR_OT_show_restart_menu)
# endregion

# region Preferences
class preferences(AddonPreferences):
    launch_update : BoolProperty()
    restart : BoolProperty()
    version : StringProperty()
    auto_update : BoolProperty(default= True, name= "Auto Update", description= "automatically search for a new Update")
    update_progress : IntProperty(name= "Update Progress", default= -1, min= -1, max= 100, soft_min= 0, soft_max= 100, subtype= 'PERCENTAGE') # use as slider
    update_responds = {}
    update_data_chunks = defaultdict(lambda: {"chunks": [], 'progress_length': 0})
# endregion

# region Regestration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion 
