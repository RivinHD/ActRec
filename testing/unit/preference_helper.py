import bpy
from ActRec.actrec.functions.shared import get_preferences


class preferences():
    addon_directory: str
    preference_tab: str
    icon_path: str
    selected_icon: int
    update: bool
    restart: bool
    version: str
    auto_update: bool
    update_progress: int
    local_actions: list
    active_local_action_index: int
    local_to_global_mode: str
    local_record_macros: bool
    hide_local_text: bool
    local_create_empty: bool
    last_macro_label: str
    last_macro_command: str
    operators_list_length: int
    global_actions: list
    global_to_local_mode: str
    autosave: bool
    global_rename: str
    global_hide_menu: bool
    import_settings: list
    import_extension: str
    storage_path: str
    categories: list
    selected_category: str
    show_all_categories: bool


def get_pref():
    register()
    bpy.ops.test.test_pref("INVOKE_DEFAULT")
    pref = TEST_OT_test_pref.pref[0]
    unregister()
    return pref


class TEST_OT_test_pref(bpy.types.Operator):
    bl_idname = "test.test_pref"
    bl_label = "Test PRef"
    bl_options = {'INTERNAL'}

    pref = ["pref"]

    def execute(self, context):
        TEST_OT_test_pref.pref[0] = get_preferences(context)
        return {"FINISHED"}


def register():
    bpy.utils.register_class(get_Pref)


def unregister():
    bpy.utils.unregister_class(get_Pref)
