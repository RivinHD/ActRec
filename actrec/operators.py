# region Import
# blender modules
import bpy
from bpy.types import Operator
# endregion

classes = []

# region Operators
class AR_OT_CheckCtrl(Operator):
    bl_idname = "ar.check_ctrl"
    bl_label = "Check Ctrl"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        if event.ctrl:
            return {"FINISHED"}
        return {"CANCELLED"}
classes.append(AR_OT_CheckCtrl)
# endregion

# region Registration 
def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)
# endregion 