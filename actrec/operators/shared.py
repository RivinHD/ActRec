# region Imports
# external modules
import webbrowser

# blender modules
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
# endregion

classes = []

# region Operators
class AR_OT_check_ctrl(Operator):
    bl_idname = "ar.check_ctrl"
    bl_label = "Check Ctrl"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        if event.ctrl:
            return {"FINISHED"}
        return {"CANCELLED"}
classes.append(AR_OT_check_ctrl)

class AR_OT_open_url(Operator):
    bl_idname = "ar.url_open"
    bl_label = "Open URL"

    url : StringProperty()
    description : StringProperty()

    def execute(self, context):
        webbrowser.open(self.url)
        return {"FINISHED"}

    @classmethod
    def description(context, properties):
        return properties.description
classes.append(AR_OT_open_url)
# endregion

# region Registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion