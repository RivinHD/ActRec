# region Imports
# external modules
import webbrowser
import time

# blender modules
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty

# relative import
from .. import shared_data, functions
# endregion

__module__ = __package__.split(".")[0]

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

class AR_OT_run_queued_macros(Operator):
    bl_idname = "ar.run_queued_macros"
    bl_label = "Run Queued Commands"
    bl_options = {'INTERNAL'}

    timer = None

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        for execute_time, action_type, action_id, start in shared_data.timed_macros:
            if time.time() == execute_time:
                action = getattr(AR, action_type)[action_id]
                functions.play(context.copy(), action.macros[start: ], action, action_type)
        return {"FINISHED"}
    
    def modal(self, context, event):
        if len(shared_data.timed_macros):
            self.execute(context)
            return {'PASS_THROUGH'}
        else:
            self.cancel(context)
            return {'FINISHED'}

    def invoke(self, context, event):
        if self.timer is None:
            wm = context.window_manager
            self.timer = wm.event_timer_add(0.05, window= context.window)
            wm.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        return {'CANCELLED'}
    
    def cancel(self, context):
        if self.timer:
            wm = context.window_manager
            wm.event_timer_remove(self._timer)
            self.timer = None

class id_based(Operator):
    id : StringProperty(name= "id", description= "id of the action (1. indicator)")
    index : IntProperty(name= "index", description= "index of the action (2. indicator)", default= -1)

    def clear(self):
        self.id = ""
        self.index = -1
# endregion

classes = [
    AR_OT_check_ctrl,
    AR_OT_run_queued_macros
]

# region Registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion