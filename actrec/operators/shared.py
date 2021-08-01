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

class AR_OT_Command_Run_Queued(Operator):
    bl_idname = "ar.command_run_queued"
    bl_label = "Run Queued Commands"
    bl_options ={'INTERNAL'}

    timer = None

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        for execute_time, action_type, action_id, start in shared_data.timed_macros:
            if time.time() == execute_time:
                action = getattr(AR, action_type)[action_id]
                functions.play(action.macros[start: ], action, action_type)
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
            self.timer = wm.event_timer_add(0.05, window=context.window)
            wm.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        return {'CANCELLED'}
    
    def cancel(self, context):
        if self.timer:
            wm = context.window_manager
            wm.event_timer_remove(self._timer)
            self.timer = None
classes.append(AR_OT_Command_Run_Queued)

class id_based(Operator):
    id : StringProperty(name= "id", description= "id of the action (1. indicator)")
    index : IntProperty(name= "index", description= "index of the action (2. indicator)", default= -1)

    def cancel(self, context):
        self.id = ""
        self.index = -1
# endregion