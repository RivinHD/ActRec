# region Imports
# external modules
import os

# blender modules
import bpy
from bpy.types import Operator, PropertyGroup
from bpy.props import IntProperty, StringProperty, BoolProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper

# relative imports
from ..preferences import AR_preferences
from .. import icon_manager

# endregion
classes = []

# region Operators
class IconTable(Operator):
    bl_label = "Icons"
    bl_description = "Press to select an Icon"

    def draw(self, execute):
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.label(text= "Selected Icon:")
        row.label(text=" ", icon_value= AR_preferences.icon_selected)
        row.prop(self, 'search', text= 'Search:')
        row.operator(AR_OT_Icon_Selector.bl_idname, text= "Clear Icon").icon = 101 #Icon: BLANK1
        box = layout.box()
        gridf = box.grid_flow(row_major=True, columns= 35, even_columns= True, even_rows= True, align= True)
        icon_values = icon_manager.functions.get_icons_values()
        for i, icon_name in enumerate(icon_manager.functions.get_icons()):
            normalname = icon_name.lower().replace("_"," ")
            if self.search == '' or self.search.lower() in normalname:
                gridf.operator(AR_OT_Icon_Selector.bl_idname, text= "", icon_value= icon_values[i]).icon = icon_values[i]
        box = layout.box()
        row = box.row().split(factor= 0.5)
        row.label(text= "Custom Icons")
        row2 = row.row()
        row2.operator(AR_OT_Add_Custom_Icon.bl_idname, text= "Add Custom Icon", icon= 'PLUS').activat_pop_up = self.bl_idname
        row2.operator(AR_OT_Delete_Custom_Icon.bl_idname, text= "Delete", icon= 'TRASH')
        gridf = box.grid_flow(row_major=True, columns= 35, even_columns= True, even_rows= True, align= True)
        customIconValues = [icon.icon_id for icon in AR_preferences.preview_collections['ar_custom'].values()]
        for i,ic in enumerate(list(AR_preferences.preview_collections['ar_custom'])):
            normalname = ic.lower().replace("_"," ")
            if self.search == '' or self.search.lower() in normalname:
                gridf.operator(AR_OT_Icon_Selector.bl_idname, text= "", icon_value= customIconValues[i]).icon = customIconValues[i]

    def check(self, context):
        return True

class AR_OT_Icon_Selector(Operator):
    bl_idname = "ar.icon_selector"
    bl_label = "Icon"
    bl_options = {'REGISTER','INTERNAL'}
    bl_description = "Select the Icon"

    icon : IntProperty(default= 101) #Icon: BLANK1

    def execute(self, context):
        AR_preferences.icon_selected = self.icon
        return {"FINISHED"}
classes.append(AR_OT_Icon_Selector)

class AR_OT_Add_Custom_Icon(Operator, ImportHelper):
    bl_idname = "ar.add_custom_icon"
    bl_label = "Add Custom Icon"
    bl_description = "Adds a custom Icon"

    filter_image : BoolProperty(default=True, options={'HIDDEN'} )
    filter_folder : BoolProperty(default=True, options={'HIDDEN'} )
    activat_pop_up : StringProperty(default= "")

    def execute(self, context):
        if os.path.isfile(self.filepath) and self.filepath.lower().endswith(('.bmp','.sgi','.rgb','.bw','.png','.jpg', '.jpeg', '.jp2', '.j2c', '.jp2', '.tga', '.cin', '.dpx', '.exr', '.hdr', '.tif', '.tiff')): # supported blender image formats https://docs.blender.org/manual/en/latest/files/media/image_formats.html
            err = icon_manager.functions.load_icons(self.filepath)
            if err is not None:
                self.report({'ERROR'}, err)
        else:
            self.report({'ERROR'}, 'The selected File is not an Image or an Image Format supported bp Blender')
        if self.activat_pop_up != "":
            exec("bpy.ops." + ".".join(self.activat_pop_up.split("_OT_")).lower() + "('INVOKE_DEFAULT')")
        return {"FINISHED"}
classes.append(AR_OT_Add_Custom_Icon)

class AR_OT_Delete_Custom_Icon(Operator):
    bl_idname = "ar.deletecustomicon"
    bl_label = "Delete Icon"
    bl_description = "Delete a custom added icon"

    class AR_Icon(PropertyGroup):
        icon_id : IntProperty()
        icon_name : StringProperty()
        selected : BoolProperty(default= False, name= 'Select')
    classes.append(AR_Icon)
    icons : CollectionProperty(type= AR_Icon)
    select_all : BoolProperty(name= "All Icons", description= "Select all Icons")

    def invoke(self, context, event):
        coll = self.icons
        coll.clear()
        icon_list = list(AR_preferences.preview_collections['ar_custom'])
        icon_list_values = [icon.icon_id for icon in AR_preferences.preview_collections['ar_custom'].values()]
        for i in range(len(icon_list)):
            new = coll.add()
            new.icon_id = icon_list_values[i]
            new.icon_name = icon_list[i]
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        for ele in self.icons:
            if ele.select or self.select_all:
                iconpath = ele.icon_name[3:]
                filenames = os.listdir(AR_Var.IconFilePath)
                names = [os.path.splitext(os.path.basename(path))[0] for path in filenames]
                if iconpath in names:
                    os.remove(os.path.join(AR_Var.IconFilePath,  filenames[names.index(iconpath)]))
                icon_manager.functions.unregister_icon(AR_preferences.preview_collections['ar_custom'], ele.icon_name)
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'select_all')
        box = layout.box()
        coll = self.icons
        if self.select_all:
            for ele in coll:
                row = box.row()
                row.label(text= '', icon= "CHECKBOX_HLT")
                row.label(text= ele.icon_name[3:], icon_value= ele.icon_id)
        else:
            for ele in coll:
                row = box.row()
                row.prop(ele, 'select', text= '')
                row.label(text= ele.icon_name[3:], icon_value= ele.icon_id)
classes.append(AR_OT_Delete_Custom_Icon)
# endregion

# region Registration 
def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)
# endregion 