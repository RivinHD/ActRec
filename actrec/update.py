# region Import
# external modules
import requests
import json
import base64
import os
import zipfile

# blender modules
import bpy
from bpy.types import Operator
from requests.models import Response

# realtive imports
from .config import config
from .log import logger
# endregion

classes = []

# region functions
def on_start(dummy = None) -> None:
    check_for_update()

def get_json_from_content(res : Response) -> dict:
    data = json.loads(res.content.decode("utf-8"))
    content = base64.b64decode(data["content"]).decode("utf-8")
    return json.loads(content)

def check_for_update() -> tuple:
        download_file = get_online_download_file()
        if download_file is None:
            return (False, "no Connection")
        old_download_file = get_local_download_file()
        if download_file["version"] > old_download_file["version"]:
            return (True, download_file["version"])
        else:
            return (False, old_download_file["version"])

def update() -> None:
    AR = bpy.context.preferences.addons[__package__].preferences
    download_paths = get_download_paths()
    zippath = os.path.join(bpy.app.tempdir, "AR_Update/" + __package__ +".zip")
    zip_it = zipfile.ZipFile(zippath, 'w')
    for path in download_paths:
        zip_it.writestr(path, get_json_from_content(requests.get(config["repoSource_URL"] + path)))
    bpy.ops.preferences.addon_install(filepath= zippath)
    version = tuple(AR.Version.split("."))
    logger.info("Updated Action Recorder to Version: " + str(version))
    os.remove(zippath)
    update_download_file(download_paths, version)

def get_online_download_file() -> dict:
    try:
        res = requests.get(config["checkSource_URL"])
        logger.info("downloaded: download_file")
        return get_json_from_content(res)
    except Exception as err:
        logger.warning("no Connecation (" + err + ")")
        return None

def get_local_download_file() -> dict:
    if not os.path.exists("download_file.json"):
        new_file = open("download_file.json", "w", encoding= 'utf-8')
        new_file.write("{}")
        new_file.close()
    download_file = open("download_file.json", "r", encoding= 'utf-8')
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

def get_download_paths() -> list:
    download_file = get_online_download_file()["files"]
    old_download_file = get_local_download_file()["files"]
    download_list = []
    old_keys = old_download_file.keys()
    for key in download_file.keys():
        if (key in old_keys and download_file[key] > old_download_file) or not(key in old_keys):
            download_list.append(key)
    return download_list

# endregion functions

# region Operator
class AR_OT_CheckUpdate(Operator):
    bl_idname = "ar.check_update"
    bl_label = "Check for Update"
    bl_description = "check for available update"

    def execute(self, context):
        update = check_for_update()
        AR = context.preferences.addons[__package__].preferences
        AR.Update = update[0]
        if isinstance(update[1], str):
            AR.Version = update[1]
        else:
            AR.Version = ".".join([str(i) for i in update[1]])
        return {"FINISHED"}
classes.append(AR_OT_CheckUpdate)

class AR_OT_Update(Operator):
    bl_idname = "ar.update"
    bl_label = "Update"
    bl_description = "install the new version"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return AR.Update

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        AR.Update = False
        AR.Restart = True
        update()
        bpy.ops.ar.restart('INVOKE_DEFAULT')
        return {"FINISHED"}
classes.append(AR_OT_Update)

class AR_OT_Restart(Operator):
    bl_idname = "ar.restart"
    bl_label = "Restart Blender"
    bl_description = "Restart Blender"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return AR.Restart

    def execute(self, context):
        path = bpy.data.filepath
        if path == '':
            os.startfile(bpy.app.binary_path)
        else:
            bpy.ops.wm.save_mainfile(filepath= path)
            os.startfile(path)
        bpy.ops.wm.quit_blender()
        return {"FINISHED"}
    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text= "You need to restart Blender to complete the Update")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
classes.append(AR_OT_Restart)
# endregion

# region Regestration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion 
