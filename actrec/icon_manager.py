# region Imports
# external modules
from typing import Optional
import os

# blender modules
import bpy
from bpy.types import Operator, PropertyGroup
from bpy.props import IntProperty, StringProperty, BoolProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper
# endregion

classes = []
preview_collections = {}

# region functions
def get_icons_values():
    return [icon.value for icon in bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.values()[1:]]

def get_icons():
    return bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.keys()[1:]

def load_icons(filepath: str, only_new: bool = False) -> Optional[str]:
    img = bpy.data.images.load(filepath)
    if img.size[0] == img.size[1]:
        AR = bpy.context.preferences.addons[__package__].preferences
        img.scale(32, 32)
        name = '.'.join(img.name.split('.')[:-1]) # last element is format of file
        internalpath = os.path.join(AR.IconFilePath, img.name) # img.name has format included
        img.save_render(internalpath)
        register_icon(preview_collections['ar_custom'], "AR_%s" %name, internalpath, only_new)
        bpy.data.images.remove(img)
    else:
        bpy.data.images.remove(img)
        return 'The Image must be a square'

def register_icon(pcoll, name: str, filepath: str, only_new: bool):
    try:
        if only_new and not(name in pcoll):
            pcoll.load(name, filepath, 'IMAGE', force_reload= True)
    except:
        split = name.split('.')
        if len(split) > 1 and split[-1].isnumeric():
            name = "%s%s" %(".".join(split[:-1]), str(int(split[-1]) + 1))
        else:
            name = "%s.1" % name
        register_icon(pcoll, name, filepath)

def unregister_icon(pcoll, name: str):
    if name in pcoll:
        del pcoll[name]

def check_icon(icon):
    if isinstance(icon, int):
        return icon
    if icon.isnumeric():
        icon = int(icon)
    else:
        iconlist = get_icons()
        if icon in iconlist:
            icon = get_icons_values()[iconlist.index(icon)]
        else:
            icon = 101 # Icon: BLANK1
    return icon
#endregion

# region Operators
class icontable(Operator):
    bl_label = "Icons"
    bl_description = "Press to select an Icon"
    
    search : StringProperty(name= "Icon Search", description= "search Icon by name", options= {'TEXTEDIT_UPDATE'})

    def draw(self, context):
        AR = context.preferences.addons[__package__].preferences
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.label(text= "Selected Icon:")
        row.label(text=" ", icon_value= AR.selected_icon)
        row.prop(self, 'search', text= 'Search:')
        row.operator('ar.icon_selector', text= "Clear Icon").icon = 101 #Icon: BLANK1
        box = layout.box()
        gridf = box.grid_flow(row_major=True, columns= 35, even_columns= True, even_rows= True, align= True)
        icon_values = get_icons_values()
        for i, icon_name in enumerate(get_icons()):
            normalname = icon_name.lower().replace("_"," ")
            if self.search == '' or self.search.lower() in normalname:
                gridf.operator('ar.icon_selector', text= "", icon_value= icon_values[i]).icon = icon_values[i]
        box = layout.box()
        row = box.row().split(factor= 0.5)
        row.label(text= "Custom Icons")
        row2 = row.row()
        row2.operator('ar.add_custom_icon', text= "Add Custom Icon", icon= 'PLUS').activat_pop_up = self.bl_idname
        row2.operator('ar.delete_custom_icon', text= "Delete", icon= 'TRASH')
        gridf = box.grid_flow(row_major=True, columns= 35, even_columns= True, even_rows= True, align= True)
        custom_icon_values = [icon.icon_id for icon in preview_collections['ar_custom'].values()]
        for i, ic in enumerate(list(preview_collections['ar_custom'])):
            normalname = ic.lower().replace("_"," ")
            if self.search == '' or self.search.lower() in normalname:
                gridf.operator('ar.icon_selector', text= "", icon_value= custom_icon_values[i]).icon = custom_icon_values[i]

    def check(self, context):
        return True

class AR_OT_icon_selector(Operator):
    bl_idname = "ar.icon_selector"
    bl_label = "Icon"
    bl_options = {'REGISTER','INTERNAL'}
    bl_description = "Select the Icon"

    icon : IntProperty(default= 101) #Icon: BLANK1

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        AR.selected_icon = self.icon
        return {"FINISHED"}
classes.append(AR_OT_icon_selector)

class AR_OT_add_custom_icon(Operator, ImportHelper):
    bl_idname = "ar.add_custom_icon"
    bl_label = "Add Custom Icon"
    bl_description = "Adds a custom Icon"

    filter_image : BoolProperty(default=True, options={'HIDDEN'} )
    filter_folder : BoolProperty(default=True, options={'HIDDEN'} )
    activat_pop_up : StringProperty(default= "")

    def execute(self, context):
        if os.path.isfile(self.filepath) and self.filepath.lower().endswith(tuple(bpy.path.extensions_image)): # supported blender image formats https://docs.blender.org/manual/en/latest/files/media/image_formats.html
            err = load_icons(self.filepath)
            if err is not None:
                self.report({'ERROR'}, err)
        else:
            self.report({'ERROR'}, 'The selected File is not an Image or an Image Format supported bp Blender')
        if self.activat_pop_up != "":
            exec("bpy.ops.%s%s" %(".".join(self.activat_pop_up.split("_OT_")).lower(), "('INVOKE_DEFAULT')"))
        return {"FINISHED"}
classes.append(AR_OT_add_custom_icon)

class AR_OT_delete_custom_icon(Operator):
    bl_idname = "ar.delete_custom_icon"
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
        icon_list = list(preview_collections['ar_custom'])
        icon_list_values = [icon.icon_id for icon in preview_collections['ar_custom'].values()]
        for i in range(len(icon_list)):
            new = coll.add()
            new.icon_id = icon_list_values[i]
            new.icon_name = icon_list[i]
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        for ele in self.icons:
            if ele.select or self.select_all:
                iconpath = ele.icon_name[3:]
                filenames = os.listdir(AR.IconFilePath)
                names = [os.path.splitext(os.path.basename(path))[0] for path in filenames]
                if iconpath in names:
                    os.remove(os.path.join(AR.IconFilePath,  filenames[names.index(iconpath)]))
                unregister_icon(preview_collections['ar_custom'], ele.icon_name)
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
classes.append(AR_OT_delete_custom_icon)
# endregion

# region Registration 
def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)
    preview_collections['ar_custom'] = bpy.utils.previews.new()

def unregister() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
# endregion 