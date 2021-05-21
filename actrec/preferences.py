# region Imports
# external modules
import os

# blender modules
import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty, IntProperty
from bpy.types import PropertyGroup, AddonPreferences, Operator
from bpy_extras.io_utils import ExportHelper
import rna_keymap_ui

# relative imports
from . import categories, globals, update, shared, icon_manager
from .config import config
# endregion

classes = []

# region Operators
class AR_OT_preferences_directory_selector(Operator, ExportHelper):
    bl_idname = "ar.preferences_directory_selector"
    bl_label = "Select Directory"
    bl_description = " "
    bl_options = {'REGISTER','INTERNAL'}

    filename_ext = "."
    use_filter_folder = True
    filepath : StringProperty (name = "File Path", maxlen = 0, default = " ")

    directory : StringProperty()

    def execute(self, context):
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        userpath = self.properties.filepath
        if(not os.path.isdir(userpath)):
            msg = "Please select a directory not a file\n" + userpath
            self.report({'ERROR'}, msg)
            return{'CANCELLED'}
        AR_Var = context.preferences.addons[__package__].preferences
        AR_Var.storage_path = os.path.join(userpath, self.directory)
        return{'FINISHED'}
classes.append(AR_OT_preferences_directory_selector)

class AR_OT_preferences_recover_directory(Operator):
    bl_idname = "ar.preferences_recover_directory"
    bl_label = "Recover Standart Directory"
    bl_description = "Recover the standart Storage directory"
    bl_options = {'REGISTER','INTERNAL'}

    directory : StringProperty()

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        AR_Var.storage_path = os.path.join(os.path.dirname(__file__), self.directory)
        return{'FINISHED'}
classes.append(AR_OT_preferences_recover_directory)
# endregion

# region PropertGroups
class AR_macro(shared.id_system, PropertyGroup):
    label : StringProperty()
    macro : StringProperty()
classes.append(AR_macro)

class AR_action(shared.id_system, PropertyGroup):
    label : StringProperty()
    command: CollectionProperty(type= AR_macro)
    icon : IntProperty(default= 101) #Icon BLANK1
classes.append(AR_action)

# region Preferences
class AR_preferences(
    categories.preferences.preferences,
    globals.preferences.preferences,
    update.preferneces,
    AddonPreferences):
    bl_idname = __package__

    addon_directory = os.path.dirname(os.path.dirname(__file__)) # get the base addon directory
    space_types = [space.identifier for space in bpy.types.Panel.bl_rna.properties['bl_space_type'].enum_items] # get all registered Space Types of Blender

    preview_collections = {}
    icon_selected = 101 # default icon value for BLANK1
    
    # =================================================================================================================================
    Rename : StringProperty()
    Autosave : BoolProperty(default= True, name= "Autosave", description= "automatically saves all Global Buttons to the Storage")
    RecToBtn_Mode : EnumProperty(items=[("copy", "Copy", "Copy the Action over to Global"), ("move", "Move", "Move the Action over to Global and Delete it from Local")], name= "Mode")
    BtnToRec_Mode : EnumProperty(items=[("copy", "Copy", "Copy the Action over to Local"), ("move", "Move", "Move the Action over to Local and Delete it from Global")], name= "Mode")
    SelectedIcon = 101 # Icon: BLANK1

    Instance_Coll : CollectionProperty(type= AR_Struct)
    Instance_Index : IntProperty(default= 0)

    FileDisp_Name = []
    FileDisp_Command = []
    FileDisp_Icon = []
    FileDisp_Index : IntProperty(default= 0)

    HideMenu : BoolProperty(name= "Hide Menu", description= "Hide Menu")
    ShowMacros : BoolProperty(name= "Show Macros" ,description= "Show Macros", default= True)

    Record = False
    Temp_Command = []
    Temp_Num = 0

    Record_Coll : CollectionProperty(type= AR_Record_Merge)
    CreateEmpty : BoolProperty(default= True)
    LastLineIndex : IntProperty()
    LastLine : StringProperty(default= "<Empty>")
    LastLineCmd : StringProperty()
    def hide_show_local_in_texteditor(self, context):
        if self.hideLocal:
            actio_names = [cmd.cname for cmd in self.Record_Coll[0].Command]
            for text in bpy.data.texts:
                if text.name in actio_names:
                    bpy.data.texts.remove(text)
        else:
            for i in range(1, len(self.Record_Coll)):
                UpdateRecordText(i)
    hideLocal : BoolProperty(name= "Hide Local Action in Texteditor", description= "Hide the Local Action in the Texteditor", update=hide_show_local_in_texteditor)

    IconFilePath : StringProperty(name= "Icon Path", description= "The Path to the Storage for the added Icons", default= os.path.join(os.path.dirname(__file__), "Icons"))

    Importsettings : CollectionProperty(type= AR_ImportCategory)
    ShowKeymap : BoolProperty(default= True)
    # (Operator.bl_idname, key, event, Ctrl, Alt, Shift)
    addon_keymaps = []
    key_assign_list = \
    [
    (AR_OT_Command_Add.bl_idname, 'COMMA', 'PRESS', False, False, True, None),
    (AR_OT_Record_Play.bl_idname, 'PERIOD', 'PRESS', False, False, True, None),
    (AR_OT_Record_SelectorUp.bl_idname, 'WHEELUPMOUSE','PRESS', False, False, True, None),
    (AR_OT_Record_SelectorDown.bl_idname, 'WHEELDOWNMOUSE','PRESS', False, False, True, None),
    ("wm.call_menu_pie", 'A', 'PRESS', False, True, True, AR_MT_Action_Pie.bl_idname),
    ]

    def draw(self, context):
        AR = bpy.context.preferences.addons[__package__].preferences
        layout = self.layout
        col = layout.column()
        row = col.row()
        if AR.update:
            update.draw_update_button(row, AR)
            row.operator(shared.AR_OT_open_url.bl_idname, text= "Release Notes").url = config['releasNotes_URL']
        else:
            row.operator(update.AR_OT_update_check.bl_idname, text= "Check For Updates")
            if AR.restart:
                row.operator(update.AR_OT_show_restart_menu.bl_idname, text= "Restart to Finsih")
        if AR.version != '':
            if AR.Update:
                col.label(text= "A new Version is available (" + AR.version + ")")
            else:
                col.label(text= "You are using the latest Vesion (" + AR.version + ")")
        col.separator(factor= 1.5)
        col.label(text= 'Action Storage Folder')
        row = col.row()
        row.operator(AR_OT_preferences_directory_selector.bl_idname, text= "Select Action Button’s Storage Folder", icon= 'FILEBROWSER').directory = "Storage"
        row.operator(AR_OT_preferences_recover_directory.bl_idname, text= "Recover Default Folder", icon= 'FOLDER_REDIRECT').directory = "Storage"
        box = col.box()
        box.label(text= self.storage_path)
        col.separator(factor= 1.5)
        row = col.row().split(factor= 0.5)
        row.label(text= "Icon Storage Folder")
        row2 = row.row(align= True).split(factor= 0.65, align= True)
        row2.operator(icon_manager.AR_OT_add_custom_icon.bl_idname, text= "Add Custom Icon", icon= 'PLUS')
        row2.operator(icon_manager.AR_OT_delete_custom_icon.bl_idname, text= "Delete", icon= 'TRASH')
        row = col.row()
        row.operator(AR_OT_preferences_directory_selector.bl_idname, text= "Select Icon Storage Folder", icon= 'FILEBROWSER').directory = "Icons"
        row.operator(AR_OT_preferences_recover_directory.bl_idname, text= "Recover Default Folder", icon= 'FOLDER_REDIRECT').directory = "Icons"
        box = col.box()
        box.label(text= self.IconFilePath)
        col.separator(factor= 1.5)
        box = col.box()
        row = box.row()
        row.prop(self, "ShowKeymap", text= "", icon= 'TRIA_DOWN' if self.ShowKeymap else 'TRIA_RIGHT', emboss= False)
        row.label(text="Keymap")
        if self.ShowKeymap:
            wm = bpy.context.window_manager
            kc = wm.keyconfigs.user
            km = kc.keymaps['Screen']
            for (idname, key, event, ctrl, alt, shift, name) in AR_preferences.key_assign_list:
                kmi = km.keymap_items[idname]
                rna_keymap_ui.draw_kmi([], kc, km, kmi, box, 0)
classes.append(AR_preferences)
# endregion

# region Regestration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    AR_preferences.preview_collections['ar_custom'] = bpy.utils.previews.new()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    for pcoll in AR_preferences.preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    AR_preferences.preview_collections.clear()
# endregion