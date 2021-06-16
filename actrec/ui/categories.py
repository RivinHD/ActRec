# region Imports
# externals modules
from contextlib import suppress

# blender modules
import bpy
from bpy.types import Panel

# relative imports
from .. import functions
# endregion

classes = []
space_types = [space.identifier for space in bpy.types.Panel.bl_rna.properties['bl_space_type'].enum_items] # get all registered Space Types of Blender

# region Panels
def register_category(index):
    register_unregister_category(index)

def unregister_category(index):
    register_unregister_category(index, False)

def register_unregister_category(index, register = True): #Register/Unregister one Category
    for spaceType in space_types:
        class AR_PT_category(Panel):
            bl_space_type = spaceType
            bl_region_type = 'UI'
            bl_category = 'Action Recorder'
            bl_label = ' '
            bl_idname = "AR_PT_category_%s_%s" %(index, spaceType)
            bl_parent_id = "AR_PT_Global_%s" % spaceType
            bl_order = index + 1

            @classmethod
            def poll(self, context):
                AR = context.preferences.addons[__package__].preferences
                index = int(self.bl_idname.split("_")[3])
                if len(AR.categories) <= index:
                    Load()
                category = AR.categories[index]
                return showCategory(category.label, context)

            def draw_header(self, context):
                AR = context.preferences.addons[__package__].preferences
                index = int(self.bl_idname.split("_")[3])
                category = AR.Categories[index]
                layout = self.layout
                row = layout.row()
                row.prop(AR.Selected_Category[index], 'selected', text= '', icon= 'LAYER_ACTIVE' if AR.Selected_Category[index].selected else 'LAYER_USED', emboss= False)
                row.label(text= category.label)

            def draw(self, context):
                AR = context.preferences.addons[__package__].preferences
                scene = context.scene
                index = int(self.bl_idname.split("_")[3])
                category = AR.Categories[index]
                layout = self.layout
                col = layout.column()
                for i in range(category.Instance_Start, category.Instance_Start + category.Instance_length):
                    globals.draw_actions(col, AR, i)
        AR_PT_category.__name__ = "AR_PT_category_%s_%s" %(index, spaceType)
        if register:
            bpy.utils.register_class(AR_PT_category)
            classes.append(AR_PT_category)
        else:
            with suppress(Exception):
                panel = eval("bpy.types.%s" %AR_PT_category.__name__)
                bpy.utils.unregister_class(panel)
                classes.remove(panel)
    AR = bpy.context.preferences.addons[__package__].preferences
    if register:
        new = AR.selected_category.add()
        new.index = index
    else:
        AR.selected_category.remove(len(AR.Selected_Category) - 1)
    if functions.get_selected_index(AR.selected_category) is None and len(AR.selected_category):
        AR.selected_category[0].selected = True
# endregion