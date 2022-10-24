# region Imports
# external modules
import os
import sys
import subprocess

# blender modules
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper

# relative imports
from ..log import logger
from ..functions.shared import get_preferences
# endregion


# region Operator


class AR_OT_preferences_directory_selector(Operator, ExportHelper):
    bl_idname = "ar.preferences_directory_selector"
    bl_label = "Select Directory"
    bl_description = " "
    bl_options = {'REGISTER', 'INTERNAL'}

    filename_ext = "."
    use_filter_folder = True
    filepath: StringProperty(name="File Path", maxlen=0, default=" ")

    preference_name: StringProperty()
    path_extension: StringProperty()

    def execute(self, context):
        ActRec_pref = get_preferences(bpy.context)
        user_path = self.properties.filepath
        if(not os.path.isdir(user_path)):
            msg = "Please select a directory not a file\n" + user_path
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}
        ActRec_pref = get_preferences(context)
        setattr(ActRec_pref, self.preference_name, os.path.join(user_path, self.path_extension))
        return {'FINISHED'}


class AR_OT_preferences_recover_directory(Operator):
    bl_idname = "ar.preferences_recover_directory"
    bl_label = "Recover Standard Directory"
    bl_description = "Recover the standard Storage directory"
    bl_options = {'REGISTER', 'INTERNAL'}

    preference_name: StringProperty()
    path_extension: StringProperty()

    def execute(self, context):
        ActRec_pref = get_preferences(context)
        setattr(ActRec_pref, self.preference_name, os.path.join(ActRec_pref.addon_directory, self.path_extension))
        return {'FINISHED'}


class AR_OT_preferences_open_explorer(Operator):
    bl_idname = "ar.preferences_open_explorer"
    bl_label = "Open Explorer"
    bl_description = "Open the Explorer with the given path"
    bl_options = {'REGISTER', 'INTERNAL'}

    path: StringProperty(name="Path", description="Open the explorer with the given path")

    def open_file_in_explorer(self, path: str):
        """
        opens the file in the os file explorer

        Args:
            path (str): path to file to open
        """
        if sys.platform == "win32":
            subprocess.call(["explorer", "/select,", path])
        elif sys.platform == "darwin":  # Mac OS X
            subprocess.call(["open", "-R", path])
        else:  # Linux
            subprocess.call(["xdg-open", os.path.dirname(path)])

    def open_directory_in_explorer(self, directory: str):
        """
        open the directory in the os file explorer

        Args:
            directory (str): path to directory to open
        """
        if sys.platform == "win32":
            os.startfile(self.directory)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, self.directory])

    def execute(self, context):
        self.path = os.path.normpath(self.path)
        if os.path.isdir(self.path):
            self.open_directory_in_explorer(self.path)
        elif os.path.isfile(self.path):
            try:
                self.open_file_in_explorer(self.path)
            except Exception as err:
                self.open_directory_in_explorer(os.path.dirname(self.path))
                logger.info("Fallback to show directory: %s" % err)
        return {'FINISHED'}
# endregion


classes = [
    AR_OT_preferences_directory_selector,
    AR_OT_preferences_recover_directory,
    AR_OT_preferences_open_explorer
]

# region Registration


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion
