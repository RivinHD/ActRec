# region Import
# external modules
from typing import Optional, Union
import requests
import json
import base64
import os
import subprocess
from collections import defaultdict
import threading
from contextlib import suppress
import sys

# blender modules
import bpy
from bpy.types import Operator
from bpy.props import BoolProperty
from bpy_extras.io_utils import ExportHelper
from bpy.app.handlers import persistent

# realtive imports
from . import config
from .log import logger
# endregion

__module__ = __package__.split(".")[0]
class update_manager:
    update_responds = {}
    update_data_chunks = defaultdict(lambda: {"chunks": b''})
    version_file = {} # used to store downloaded file from "AR_OT_update_check"
    version_file_thread = None

# region functions
@persistent
def on_start(dummy= None) -> None:
    AR = bpy.context.preferences.addons[__module__].preferences
    if AR.auto_update and update_manager.version_file_thread is None:
        t = threading.Thread(target= no_stream_download_version_file, args= [__module__], daemon= True)
        t.start()
        update_manager.version_file_thread = t

@persistent
def on_scene_update(dummy= None) -> None:
    t = update_manager.version_file_thread
    if t and update_manager.version_file.get("version", None):
        t.join()
        bpy.app.handlers.depsgraph_update_post.remove(on_scene_update)
        bpy.app.handlers.load_post.remove(on_start)

def check_for_update(version_file: Optional[dict]) -> tuple[bool, Union[str, tuple[int, int, int]]]:
    if version_file is None:
        return (False, "No Internet Connection")
    version = config.version
    download_version = tuple(version_file["version"])
    if download_version > version:
        return (True, download_version)
    else:
        return (False, version)

def start_update(version_file) -> Optional[bool]:
    download_paths = get_download_paths(version_file)
    if download_paths is None:
        return False
    try:
        for path in download_paths:
            update_manager.update_responds[path] = requests.get(config.repo_source_url %path, stream= True)
        logger.info("Start Update Process")
        return True
    except Exception as err:
        logger.warning("no Connection (%s)" %err)
        return None

def update(AR, update_responds: dict, download_chunks: dict) -> Optional[bool]:
    finished_downloaded = True
    complet_length = 0
    complet_progress = 0
    try:
        for path, res in update_responds.items():
            total_length = res.headers.get('content-length', None)
            if total_length is None:
                complet_progress += res.raw._fp_bytes_read
                download_chunks[path]["chunks"] += res.content
                res.close()
                update_responds[path] = None
            else:
                total_length = int(total_length)
                complet_length += total_length
                for chunk in res.iter_content(chunk_size= 1024):
                    if chunk:
                        download_chunks[path]["chunks"] += chunk

                length = res.raw._fp_bytes_read
                complet_progress += length
                finished_progress = length == total_length
                if finished_progress:
                    res.close()
                    update_responds[path] = None
                finished_downloaded = finished_progress and finished_downloaded
        AR.update_progress = 100 * complet_progress / complet_length
        return finished_downloaded
    except Exception as err:
        logger.warning("no Connection (%s)" %err)
        return None

def install_update(AR, download_chunks: dict, version_file: dict) -> None:
    for path in download_chunks:
        absolute_path = os.path.join(AR.addon_directory, path)
        absolute_directory = os.path.dirname(absolute_path)
        if not os.path.exists(absolute_directory):
            os.makedirs(absolute_directory)
        with open(absolute_path, 'w', encoding= 'utf-8') as ar_file:
            ar_file.write(path, download_chunks[path]["chunks"])
    for path in version_file['remove']:
        remove_path = os.path.join(AR.addon_directory, path)
        if os.path.exists(remove_path):
            for root, dirs, files in os.walk(remove_path, topdown= False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
    version = tuple(AR.version.split("."))
    download_chunks.clear()
    version_file.clear()
    logger.info("Updated Action Recorder to Version: %s" %str(version))

def start_get_version_file() -> Optional[bool]:
    try:
        update_manager.version_file['respond'] = requests.get(config.check_source_url, stream= True)
        update_manager.version_file['chunk'] = b''
        logger.info("Start Download: version_file")
        return True
    except Exception as err:
        logger.warning("no Connection (%s)" %err)
        return None

def get_version_file(res: requests.Response) -> Union[bool, dict, None]:
    try:
        total_length = res.headers.get('content-length', None)
        if total_length is None:
            logger.info("Finsihed Download: version_file")
            content = res.content
            res.close()
            return json.loads(content)
        else:
            for chunk in res.iter_content(chunk_size= 1024):
                update_manager.version_file['chunk'] += chunk
            length = res.raw._fp_bytes_read
            if int(total_length) == length:
                res.close()
                logger.info("Finsihed Download: version_file")
                return json.loads(update_manager.version_file['chunk'])
            return True
    except Exception as err:
        logger.warning("no Connection (%s)" %err)
        res.close()
        return None

def apply_version_file_result(AR, version_file, update):
    AR.update = update[0]
    if not update[0]:
        res = version_file.get('respond')
        if res:
            res.close()
        version_file.clear()
    if isinstance(update[1], str):
        AR.version = update[1]
    else:
        AR.version = ".".join(map(str, update[1]))

def get_download_paths(version_file) -> Optional[list]:
    download_files = version_file["files"]
    if download_files is None:
        return None
    download_list = []
    version = config.version
    for key in download_files:
        if tuple(download_files[key]) > version:
            download_list.append(key)
    return download_list

def no_stream_download_version_file(module_name):
    try:
        logger.info("Start Download: version_file")
        res = requests.get(config.check_source_url)
        logger.info("Finsihed Download: version_file")
        update_manager.version_file = json.loads(res.content)
        version_file = update_manager.version_file
        update = check_for_update(version_file)
        AR = bpy.context.preferences.addons[module_name].preferences
        apply_version_file_result(AR, version_file, update)
    except Exception as err:
        logger.warning("no Connection (%s)" %err)
        return None
# endregion functions

# region UI functions
def draw_update_button(layout, AR) -> None:
    if AR.update_progress >= 0:
        row = layout.row()
        row.enable = False
        row.prop(AR, 'update_progress', text= "Progress", slider= True)
    else:
        layout.operator('ar.update', text= 'Update')
# endregion

# region Operator
class AR_OT_update_check(Operator):
    bl_idname = "ar.update_check"
    bl_label = "Check for Update"
    bl_description = "check for available update"
    
    def invoke(self, context, event):
        res = start_get_version_file()
        if res:
            self.timer = context.window_manager.event_timer_add(0.1)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        self.report({'WARNING'}, "No Internet Connection")
        return {'CANCELLED'}

    def modal(self, context, event):
        version_file = get_version_file(update_manager.version_file['respond'])
        if isinstance(version_file, dict) or version_file is None:
            update_manager.version_file = version_file
            return self.execute(context)
        return {'PASS_THROUGH'}

    def execute(self, context):
        version_file = update_manager.version_file
        if not version_file:
            return {'CANCELLED'}
        if version_file.get('respond'):
            return {'RUNNING_MODAL'}
        update = check_for_update(version_file)
        AR = context.preferences.addons[__module__].preferences
        apply_version_file_result(AR, version_file, update)
        context.window_manager.event_timer_remove(self.timer)
        return {"FINISHED"}

    def cancel(self, context):
        if update_manager.version_file:
            res = update_manager.version_file.get('respond')
            if res:
                res.close()
            update_manager.version_file.clear()
        context.window_manager.event_timer_remove(self.timer)

class AR_OT_update(Operator):
    bl_idname = "ar.update"
    bl_label = "Update"
    bl_description = "install the new version"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        return AR.update

    def invoke(self, context, event):
        launch = start_update(update_manager.version_file)
        if launch:
            self.timer = context.window_manager.event_timer_add(0.1)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        self.report({'WARNING'}, "No Internet Connection")
        return {'CANCELLED'}

    def modal(self, context, event):
        AR = context.preferences.addons[__module__].preferences
        res = update(AR, update_manager.update_responds, update_manager.update_data_chunks)
        if res:
            return self.execute(context)
        elif res is None:
            self.report({'WARNING'}, "No Internet Connection")
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        if not(update_manager.version_file and update_manager.update_data_chunks):
            return {'CANCELLED'}
        AR = context.preferences.addons[__module__].preferences
        AR.update = False
        AR.restart = True
        install_update(AR, update_manager.update_data_chunks, update_manager.version_file)
        AR.update_progress = -1
        self.cancel(context)
        bpy.ops.ar.show_restart_menu('INVOKE_DEFAULT')
        return {"FINISHED"}

    def cancel(self, context):
        for res in update_manager.update_responds.values():
            res.close()
        update_manager.update_responds.clear()
        update_manager.update_data_chunks.clear()
        context.window_manager.event_timer_remove(self.timer)

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
        AR = context.preferences.addons[__module__].preferences
        return AR.restart

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        path = bpy.data.filepath
        if self.save:
            if path == '':
                path = self.filepath
            bpy.ops.wm.save_mainfile(filepath= path)
        AR.restart = False
        if os.path.exists(path):
            args = [*sys.argv, path]
        else:
            args = sys.argv
        subprocess.Popen(args)
        bpy.ops.wm.quit_blender()
        return {"FINISHED"}

    def invoke(self, context, event):
        if self.save and bpy.data.filepath == '':
            return ExportHelper.invoke(self, context, event)
        else:
            return self.execute(context)

class AR_OT_show_restart_menu(Operator):
    bl_idname = "ar.show_restart_menu"
    bl_label = "Restart Blender"
    bl_description = "Restart Blender"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
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
# endregion

classes = [
    AR_OT_update_check,
    AR_OT_update,
    AR_OT_restart,
    AR_OT_show_restart_menu
]

# region Registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.handlers.load_post.append(on_start)
    bpy.app.handlers.depsgraph_update_post.append(on_scene_update)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    with suppress(Exception):
        bpy.app.handlers.load_post.remove(on_start)
    with suppress(Exception):
        bpy.app.handlers.depsgraph_update_post.remove(on_scene_update)
    update_manager.update_data_chunks.clear()
    update_manager.update_responds.clear()
    update_manager.version_file.clear()
    update_manager.version_file_thread = None
# endregion 
