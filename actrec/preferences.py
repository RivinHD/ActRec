# region Imports
# external modules
import Category_Visibility
import bpy
import os

# blender modules
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty, IntProperty
from bpy.types import PropertyGroup
import rna_keymap_ui

# relative imports
from . import log
from . import ar_category
# endregion

classes = []

# region PropertGroups
class AR_macro(PropertyGroup):
    name : StringProperty()
    macro : StringProperty()
classes.append(AR_macro)

class AR_action(PropertyGroup):
    name: StringProperty()
    command: CollectionProperty(type= AR_macro)
    icon : IntProperty(default= 101) #Icon BLANK1
classes.append(AR_action)

# region Preferences
class AR_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    addon_directory = os.path.dirname(os.path.dirname(__file__)) # get the base addon directory
    space_types = [space.identifier for space in bpy.types.Panel.bl_rna.properties['bl_space_type'].enum_items] # get all registered Space Types of Blender
    
    ar_category.preferences.register_preferences()

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
    Update : BoolProperty()
    Version : StringProperty()
    Restart : BoolProperty()
    AutoUpdate : BoolProperty(default= True, name= "Auto Update", description= "automatically search for a new Update")
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
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        layout = self.layout
        col = layout.column()
        row = col.row()
        if AR_Var.Update:
            row.operator(AR_OT_Update.bl_idname, text= "Update")
            row.operator(AR_OT_ReleaseNotes.bl_idname, text= "Release Notes")
        else:
            row.operator(AR_OT_CheckUpdate.bl_idname, text= "Check For Updates")
            if AR_Var.Restart:
                row.operator(AR_OT_Restart.bl_idname, text= "Restart to Finsih")
        if AR_Var.Version != '':
            if AR_Var.Update:
                col.label(text= "A new Version is available (" + AR_Var.Version + ")")
            else:
                col.label(text= "You are using the latest Vesion (" + AR_Var.Version + ")")
        col.separator(factor= 1.5)
        col.label(text= 'Action Storage Folder')
        row = col.row()
        row.operator(AR_OT_Preferences_DirectorySelector.bl_idname, text= "Select Action Button’s Storage Folder", icon= 'FILEBROWSER').directory = "Storage"
        row.operator(AR_OT_Preferences_RecoverDirectory.bl_idname, text= "Recover Default Folder", icon= 'FOLDER_REDIRECT').directory = "Storage"
        box = col.box()
        box.label(text= self.storage_path)
        col.separator(factor= 1.5)
        row = col.row().split(factor= 0.5)
        row.label(text= "Icon Storage Folder")
        row2 = row.row(align= True).split(factor= 0.65, align= True)
        row2.operator(AR_OT_AddCustomIcon.bl_idname, text= "Add Custom Icon", icon= 'PLUS')
        row2.operator(AR_OT_DeleteCustomIcon.bl_idname, text= "Delete", icon= 'TRASH')
        row = col.row()
        row.operator(AR_OT_Preferences_DirectorySelector.bl_idname, text= "Select Icon Storage Folder", icon= 'FILEBROWSER').directory = "Icons"
        row.operator(AR_OT_Preferences_RecoverDirectory.bl_idname, text= "Recover Default Folder", icon= 'FOLDER_REDIRECT').directory = "Icons"
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
            for (idname, key, event, ctrl, alt, shift, name) in AR_Prop.key_assign_list:
                kmi = km.keymap_items[idname]
                rna_keymap_ui.draw_kmi([], kc, km, kmi, box, 0)
# endregion

# region Regestration
def register():
    bpy.utils.register_class(AR_preferences)

def unregister():
    bpy.utils.unregister_class(AR_preferences)
# endregion