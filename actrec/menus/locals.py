# region Imports
# external modules
from contextlib import suppress

# blender modules
import bpy
from bpy.types import Menu
# endregion

# region Menus
class AR_MT_action_pie(Menu):
    bl_idname = "ar.action_pie"
    bl_label = "ActRec Pie Menu"
    bl_idname = "AR_MT_Action_Pie"

    def draw(self, context):
        AR = context.preferences.addons[__package__].preferences
        pie = self.layout.menu_pie()
        actions = AR.local_action
        for i in range(len(actions)):
            if i >= 8:
                break
            action = actions[i]
            ops = pie.operator("ar.local_play", text= actions[i].label, icon_value= action.icon if action.icon else 286)
            ops.id = action.ids
            ops.index = i

def menu_func(self, context):
    if bpy.ops.ui.copy_python_command_button.poll():
        layout = self.layout
        layout.separator()
        layout.operator("ar.copy_to_actrec")

class WM_MT_button_context(Menu):
    bl_label = "Add Viddyoze Tag"

    def draw(self, context):
        pass
# endregion

classes = [
    AR_MT_action_pie
]
internal_classes = [
    WM_MT_button_context
]

# region Registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    with suppress(Exception):
        bpy.types.WM_MT_button_context.append(menu_func)
    for cls in internal_classes:
        with suppress(Exception):
            bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    with suppress(Exception):
        bpy.types.WM_MT_button_context.remove(menu_func)
    for cls in internal_classes:
        with suppress(Exception):
            bpy.utils.unregister_class(cls)
# endregion
