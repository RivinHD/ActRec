# region Import
# external modules
from typing import Optional, Union
import requests
import json
import base64
import os
import subprocess
from collections import defaultdict

# blender modules
import bpy
from bpy.types import Operator
from bpy.props import BoolProperty
from bpy_extras.io_utils import ExportHelper

# realtive imports
from . import config
from .log import logger
# endregion

classes = []

class update_manager:
    update_responds = {}
    update_data_chunks = defaultdict(lambda: {"chunks": [], 'progress_length': 0})
    download_file = {} # used to store downloaded file from "AR_OT_update_check"

# region functions
def on_start() -> None:
    bpy.ops.ar.update_check()

def get_json_from_content(content : bytes) -> dict:
    data = json.loads(content)
    content = base64.b64decode(data["content"]).decode("utf-8")
    return json.loads(content)

def check_for_update(download_file: Optional[dict]) -> tuple[bool, Union[str, tuple[int, int, int]]]:
    if download_file is None:
        return (False, "No Internet Connection")
    old_download_file = get_local_download_file()
    if download_file["version"] > old_download_file["version"]:
        return (True, download_file["version"])
    else:
        return (False, old_download_file["version"])

def start_update(download_file) -> bool:
    download_paths = get_download_paths(download_file)
    if download_paths is None:
        return False
    for path in download_paths:
        update_manager.update_responds[path] = requests.get(config.repo_source_url + path, stream= True)
    logger.info("Start Update Process")

def update(AR, update_responds: dict, download_chunks: dict) -> bool:
    finished_downloaded = True
    complet_length = 0
    complet_progress = 0
    for path, res in update_responds.items():
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

def install_update(AR, download_chunks: dict, download_file: dict) -> None:
    for path in download_chunks:
        absolute_path = os.path.join(AR.addon_directory, path)
        absolute_directory = os.path.dirname(absolute_path)
        if not os.path.exists(absolute_directory):
            os.makedirs(absolute_directory)
        with open(absolute_path, 'w', encoding= 'utf-8') as ar_file:
            ar_file.write(path, get_json_from_content(b''.join(download_chunks[path]["chunks"])))
    for path in download_file['remove']:
        remove_path = os.path.join(AR.addon_directory, path)
        if os.path.exists(remove_path):
            for root, dirs, files in os.walk(remove_path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
    version = tuple(AR.version.split("."))
    update_download_file(download_chunks.keys(), download_file['remove'], version)
    download_chunks.clear()
    download_file.clear()
    logger.info("Updated Action Recorder to Version: " + str(version))

def start_get_online_download_file() -> None:
    try:
        update_manager.download_file['respond'] = requests.get(config.check_source_url, stream= True)
        update_manager.download_file['chunk'] = []
        logger.info("Start Download: download_file")
    except Exception as err:
        logger.warning("no Connection (" + err + ")")
        return None

def get_online_download_file(res: requests.Response) -> Optional[Union[bool, dict]]:
    try:
        total_length = res.headers.get('content-length', None)
        if total_length is None:
            logger.info("Finsihed Download: download_file")
            res.close()
            return get_json_from_content(res.content)
        else:
            for chunk in res.iter_content(chunk_size=4096):
                update_manager.download_file['chunk'].append(chunk)
            if total_length == len(update_manager.download_file['chunk']):
                res.close()
                logger.info("Finsihed Download: download_file")
                return get_json_from_content(res.content)
            return True
    except Exception as err:
        logger.warning("no Connection (" + err + ")")
        return None

def get_local_download_file() -> dict:
    AR = bpy.context.preferences.addons[__package__].preferences
    path = os.path.join(AR.addon_directory, "download_file.json")
    if not os.path.exists(path):
        new_file = open(path, "w", encoding= 'utf-8')
        new_file.write("{}")
        new_file.close()
    download_file = open(path, "r", encoding= 'utf-8')
    download_text = download_file.read()
    download_file.close()
    return json.loads(download_text)

def update_download_file(download_list: list, remove_list: list, current_version: tuple) -> None:
    AR = bpy.context.preferences.addons[__package__].preferences
    download_file = get_local_download_file()
    files = []
    for path in filter(lambda x: x not in remove_list, download_list + download_file['files']):
        files.append({path : current_version})
    download_file["files"] = files
    download_file["version"] = current_version
    with open(os.path.join(AR.addon_directory, "download_file.json"), "w", encoding= "utf-8") as open_files:
        json.dump(download_file, open_files, ensure_ascii= False, indent= 4)

def get_download_paths(download_file) -> Optional[list]:
    download_files = download_file["files"]
    if download_files is None:
        return None
    old_download_files = get_local_download_file()["files"]
    download_list = []
    old_keys = old_download_files.keys()
    for key in download_files.keys():
        key_exists = key in old_keys 
        if (key_exists and download_files[key] > old_download_files[key]) or not key_exists:
            download_list.append(key)
    return download_list
# endregion functions

# region UI functions
def draw_update_button(layout, AR) -> None:
    if AR.update_progress >= 0:
        row = layout.row()
        row.enable = False
        row.prop(AR, 'update_progress', text= "Progress", slider=True)
    else:
        layout.operator('ar.update', text= 'Update')
# endregion

# region Operator
class AR_OT_update_check(Operator):
    bl_idname = "ar.update_check"
    bl_label = "Check for Update"
    bl_description = "check for available update"
    
    def invoke(self, context, event):
        start_get_online_download_file()
        self.timer = context.window_manager.event_timer_add(0.1)
        return context.window_manager.modal_handler_add(self)

    def modal(self, context, event):
        download_file = get_online_download_file(update_manager.download_file['respond'])
        if isinstance(download_file, (dict, None)):
            update_manager.download_file = download_file
            return self.execute(context)
        return {'PASS_THROUGH'}

    def execute(self, context):
        update = check_for_update(update_manager.download_file)
        AR = context.preferences.addons[__package__].preferences
        AR.Update = update[0]
        if not update[0]:
            update_manager.download_file.clear()
        if isinstance(update[1], str):
            AR.version = update[1]
        else:
            AR.version = ".".join(map(str, update[1]))
        context.window_manager.event_timer_remove(self.timer)
        return {"FINISHED"}

    def cancel(self, context):
        res = update_manager.download_file.get('respond')
        if res:
            res.close()
        update_manager.download_file.clear()
        context.window_manager.event_timer_remove(self.timer)
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
        launch = start_update(update_manager.download_file)
        if launch:
            self.timer = context.window_manager.event_timer_add(0.1)
            return {'RUNNING_MODAL'}
        self.report({'ERROR'}, "No Internet Connection")
        return {'CANCELLED'}

    def modal(self, context, event):
        AR = context.preferences.addons[__package__].preferences
        if update(AR, update_manager.update_responds, update_manager.update_data_chunks):
            return self.execute(context)
        return {'PASS_THROUGH'}

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        AR.update = False
        AR.restart = True
        install_update(AR, update_manager.update_data_chunks, update_manager.download_file)
        AR.update_progress = -1
        context.window_manager.event_timer_remove(self.timer)
        bpy.ops.ar.show_restart_menu('INVOKE_DEFAULT')
        return {"FINISHED"}

    def cancel(self, context):
        for res in update_manager.update_responds.values():
            res.close()
        update_manager.update_responds.clear()
        update_manager.update_data_chunks.clear()
        context.window_manager.event_timer_remove(self.timer)
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

# region Regestration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion 
