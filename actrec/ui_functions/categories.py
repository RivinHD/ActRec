# region Imports
# externals modules
from contextlib import suppress

# blender modules
import bpy
from bpy.types import Panel

# relative imports
from . import globals
from .. import panels
# endregion

__module__ = __package__.split(".")[0]

classes = []
space_mode_attribute = {
    'IMAGE_EDITOR': 'ui_mode',
    'NODE_EDITOR': 'texture_type',
    'SEQUENCE_EDITOR': 'view_type',
    'CLIP_EDITOR': 'mode',
    'DOPESHEET_EDITOR': 'ui_mode'
}
areas_to_spaces = {
    'VIEW_3D': 'VIEW_3D', 
    'IMAGE_EDITOR': 'IMAGE_EDITOR', 
    'UV': 'IMAGE_EDITOR', 
    'CompositorNodeTree': 'NODE_EDITOR', 
    'TextureNodeTree': 'NODE_EDITOR', 
    'GeometryNodeTree': 'NODE_EDITOR', 
    'ShaderNodeTree': 'NODE_EDITOR', 
    'SEQUENCE_EDITOR': 'SEQUENCE_EDITOR', 
    'CLIP_EDITOR': 'CLIP_EDITOR', 
    'DOPESHEET': 'DOPESHEET_EDITOR', 
    'TIMELINE': 'DOPESHEET_EDITOR', 
    'FCURVES': 'GRAPH_EDITOR', 
    'DRIVERS': 'GRAPH_EDITOR', 
    'NLA_EDITOR': 'NLA_EDITOR', 
    'TEXT_EDITOR': 'TEXT_EDITOR', 
    'FILES': 'FILE_BROWSER'
}

# region Panel
def register_category(AR, category):
    index = AR.categories.find(category.id)
    if len(category.areas):
        space_types = [areas_to_spaces[area.type] for area in category.areas]
        register_unregister_category(index, space_types)
    else:
        register_unregister_category(index)

def unregister_category(AR, category):
    index = AR.categories.find(category.id)
    register_unregister_category(index, register = False)

def show_category(context, category):
    if not len(category.areas):
        return True
    area_type = context.area.ui_type
    area_space = context.area.type
    for area in category.areas:
        if area.type == area_type:
            if len(area.modes) == 0:
                return True
            if area_space == 'VIEW_3D' or area_space == 'FILE_BROWSER':
                mode = context.mode
            else:
                mode = getattr(context.space_data, space_mode_attribute[area_space])
            return mode in set(mode.type for mode in area.modes)
    return False

def register_unregister_category(index, space_types = panels.ui_space_types, register = True): #Register/Unregister one Category
    for spaceType in space_types:
        class AR_PT_category(Panel):
            bl_space_type = spaceType
            bl_region_type = 'UI'
            bl_category = 'Action Recorder'
            bl_label = ' '
            bl_idname = "AR_PT_category_%s_%s" %(index, spaceType)
            bl_parent_id = "AR_PT_global_%s" % spaceType
            bl_order = index + 1

            @classmethod
            def poll(self, context):
                AR = context.preferences.addons[__module__].preferences
                index = int(self.bl_idname.split("_")[3])
                category = AR.categories[index]
                return show_category(context, category)

            def draw_header(self, context):
                AR = context.preferences.addons[__module__].preferences
                index = int(self.bl_idname.split("_")[3])
                category = AR.categories[index]
                layout = self.layout
                row = layout.row()
                row.prop(AR.categories[index], 'selected', text= '', icon= 'LAYER_ACTIVE' if AR.categories[index].selected else 'LAYER_USED', emboss= False)
                row.label(text= category.label)

            def draw(self, context):
                AR = context.preferences.addons[__module__].preferences
                index = int(self.bl_idname.split("_")[3])
                category = AR.categories[index]
                layout = self.layout
                col = layout.column()
                for id in [x.id for x in category.actions]:
                    globals.draw_global_action(col, AR, id)
        AR_PT_category.__name__ = "AR_PT_category_%s_%s" %(index, spaceType)
        if register:
            bpy.utils.register_class(AR_PT_category)
            classes.append(AR_PT_category)
        else:
            with suppress(Exception):
                if hasattr(bpy.types, AR_PT_category.__name__):
                    panel = getattr(bpy.types, AR_PT_category.__name__)
                    bpy.utils.unregister_class(panel)
                    classes.remove(panel)
    AR = bpy.context.preferences.addons[__module__].preferences
    if AR.selected_category == '' and len(AR.categories):
        AR.categories[0].selected = True
# endregion