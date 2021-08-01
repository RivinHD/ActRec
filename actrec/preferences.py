# region Imports
# external modules
import os

# blender modules
import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty, IntProperty
from bpy.types import AddonPreferences
import rna_keymap_ui

# relative imports
from . import properties
from . import config
from . import update
from .log import logger
# endregion

classes = []

# region Preferences
class AR_preferences(AddonPreferences):
    bl_idname = __package__
    addon_directory : StringProperty(name= "addon directory", default= os.path.dirname(os.path.dirname(__file__)), get= lambda self: self.bl_rna.properties['addon_directory'].default)  # get the base addon directory

    selected_icon : IntProperty(name="selected icon", description= "only internal usage", default= 101, min= 0, options= {'HIDDEN'}) # default icon value for BLANK1
    
    # update
    launch_update : BoolProperty()
    restart : BoolProperty()
    version : StringProperty()
    auto_update : BoolProperty(default= True, name= "Auto Update", description= "automatically search for a new Update")
    update_progress : IntProperty(name= "Update Progress", default= -1, min= -1, max= 100, soft_min= 0, soft_max= 100, subtype= 'PERCENTAGE') # use as slider

    # locals
    local_actions : CollectionProperty(type= properties.AR_local_actions)

    def get_selected_local_action_index(self):
        value = self.get('selected_local_action_index', 0)
        actions_length = len(self.local_actions)
        return value if value < actions_length else actions_length - 1
    def set_selected_local_action_index(self, value):
        actions_length = len(self.local_actions)
        self['selected_local_action_index'] = value if value < actions_length else actions_length - 1
    selected_local_action_index : IntProperty(min= 0, get= get_selected_local_action_index, set= set_selected_local_action_index)

    local_to_global_mode : EnumProperty(items=[("copy", "Copy", "Copy the Action over to Global"), ("move", "Move", "Move the Action over to Global and Delete it from Local")], name= "Mode")
    local_record_macros : BoolProperty(name= "Record Macros", default= False)
    def hide_show_local_in_texteditor(self, context):
        if self.hideLocal:
            for text in bpy.data.texts:
                if text.lines[0].body.strip().startswith("###AR###"):
                    bpy.data.texts.remove(text)
        else:
            for i in range(1, len(self.Record_Coll)):
                UpdateRecordText(i)
    hide_local_text : BoolProperty(name= "Hide Local Action in Texteditor", description= "Hide the Local Action in the Texteditor", update=hide_show_local_in_texteditor)

    # macros
    def get_selected_macro_index(self):
        value = self.get('selected_macro_index', 0)
        commands_length = len(self.local_actions[self.selected_local_action_index].macros)
        return value if value < commands_length else commands_length - 1
    def set_selected_macro_index(self, value):
        commands_length = len(self.local_actions[self.selected_local_action_index].macros)
        self['selected_macro_index'] = value if value < commands_length else commands_length - 1
    selected_macro_index : IntProperty(min= 0, get= get_selected_macro_index, set= set_selected_macro_index)

    # globals
    global_actions : CollectionProperty(type= properties.AR_global_actions)

    global_to_local_mode : EnumProperty(items=[("copy", "Copy", "Copy the Action over to Global"), ("move", "Move", "Move the Action over to Global and Delete it from Local")], name= "Mode")
    autosave : BoolProperty(default= True, name= "Autosave", description= "automatically saves all Global Buttons to the Storage")
    global_rename : StringProperty(name= "Rename", description= "Rename the selected Action")

    import_settings : CollectionProperty(type= properties.AR_global_import_category)
    import_extension : StringProperty()

    # categories
    def get_storage_path(self) -> str:
        origin_path = self.get('storage_path', 'Fallback')
        if os.path.exists(origin_path):
            return self['storage_path']
        else:
            path = os.path.join(self.addon_directory, "Storage.json")
            if origin_path != 'Fallback':
                logger.error("ActRec ERROR: Storage Path \"" + origin_path +"\" don't exist, fallback to " + path)
            self['storage_path'] = path
            return path
    def set_storage_path(self, origin_path: str) -> None:
        self['storage_path'] = origin_path
        if not(os.path.exists(origin_path)) and os.path.isfile(origin_path):
            with open(origin_path, 'w') as storage_file:
                storage_file.write('{}')
    storage_path : StringProperty(name= "Stroage Path", description= "The Path to the Storage for the saved Categories", default= os.path.join(os.path.dirname(os.path.dirname(__file__)), "Storage.json"), get=get_storage_path, set=set_storage_path)

    categories : CollectionProperty(type= properties.AR_categories)
    def get_selected_category(self):
        return self.get("categories.selected_id", '')
    selected_category : StringProperty(get= get_selected_category, default= '')
    show_all_categories : BoolProperty(name= "Show All Categories", default= False)


    # =================================================================================================================================
    Rename : StringProperty()
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
        AR = context.preferences.addons[__package__].preferences
        layout = self.layout
        col = layout.column()
        row = col.row()
        if AR.update:
            update.draw_update_button(row, AR)
            row.operator('ar.open_url', text= "Release Notes").url = config.release_notes_url
        else:
            row.operator('ar.update_check', text= "Check For Updates")
            if AR.restart:
                row.operator('ar.show_restart_menu', text= "Restart to Finsih")
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

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion