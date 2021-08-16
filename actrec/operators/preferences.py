# region Imports
# external modules
import os

# blender modules
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper
# endregion

# region Operator
class AR_OT_preferences_directory_selector(Operator, ExportHelper):
    bl_idname = "ar.preferences_directory_selector"
    bl_label = "Select Directory"
    bl_description = " "
    bl_options = {'REGISTER','INTERNAL'}

    filename_ext = "."
    use_filter_folder = True
    filepath : StringProperty (name = "File Path", maxlen = 0, default = " ")

    pref_property : StringProperty()
    path_extension : StringProperty()

    def execute(self, context):
        AR = bpy.context.preferences.addons[__package__].preferences
        userpath = self.properties.filepath
        if(not os.path.isdir(userpath)):
            msg = "Please select a directory not a file\n" + userpath
            self.report({'ERROR'}, msg)
            return{'CANCELLED'}
        AR = context.preferences.addons[__package__].preferences
        setattr(AR, self.pref_property, os.path.join(userpath, self.path_extension))
        return{'FINISHED'}

class AR_OT_preferences_recover_directory(Operator):
    bl_idname = "ar.preferences_recover_directory"
    bl_label = "Recover Standart Directory"
    bl_description = "Recover the standart Storage directory"
    bl_options = {'REGISTER','INTERNAL'}

    pref_property : StringProperty()
    path_extension : StringProperty()

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        setattr(AR, self.pref_property, os.path.join(AR.addon_directory, self.path_extension))
        return{'FINISHED'}
# endregion

classes = [
    AR_OT_preferences_directory_selector,
    AR_OT_preferences_recover_directory
]

# region Registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion