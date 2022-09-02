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


def compare_with_dict(obj, compare_dict):
    return all(getattr(obj, key) == value for key, value in compare_dict.items())
