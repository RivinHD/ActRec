# region Imports
# external modules
import os

# blender modules
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper
# endregion

classes = []

# region Operator
class AR_OT_preferences_directory_selector(Operator, ExportHelper):
    bl_idname = "ar.preferences_directory_selector"
    bl_label = "Select Directory"
    bl_description = " "
    bl_options = {'REGISTER','INTERNAL'}

    filename_ext = "."
    use_filter_folder = True
    filepath : StringProperty (name = "File Path", maxlen = 0, default = " ")

    directory : StringProperty()

    def execute(self, context):
        AR = bpy.context.preferences.addons[__package__].preferences
        userpath = self.properties.filepath
        if(not os.path.isdir(userpath)):
            msg = "Please select a directory not a file\n" + userpath
            self.report({'ERROR'}, msg)
            return{'CANCELLED'}
        AR = context.preferences.addons[__package__].preferences
        AR.storage_path = os.path.join(userpath, self.directory)
        return{'FINISHED'}
classes.append(AR_OT_preferences_directory_selector)

class AR_OT_preferences_recover_directory(Operator):
    bl_idname = "ar.preferences_recover_directory"
    bl_label = "Recover Standart Directory"
    bl_description = "Recover the standart Storage directory"
    bl_options = {'REGISTER','INTERNAL'}

    directory : StringProperty()

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        AR.storage_path = os.path.join(os.path.dirname(__file__), self.directory)
        return{'FINISHED'}
classes.append(AR_OT_preferences_recover_directory)
# endregion
