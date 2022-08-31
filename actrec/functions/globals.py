# region Imports
# external modules
import json
import os
from typing import Union

# blender modules
import bpy
from bpy.app.handlers import persistent

# relative imports
from ..log import logger
from .. import ui_functions, shared_data, keymap
from . import shared
# endregion

__module__ = __package__.split(".")[0]

# region Functions


def global_runtime_save(AR: bpy.types.AddonPreferences, use_autosave: bool = True):
    """
    save global actions to the local temp (dict) while Blender is running

    Args:
        AR (bpy.types.AddonPreferences): Blender preferences of this addon
        use_autosave (bool, optional):
            include autosave to storage file (depend on AddonPreference autosave).
            Defaults to True.
    """
    shared_data.global_temp = shared.property_to_python(AR.global_actions)
    if use_autosave and AR.autosave:
        save(AR)


@persistent
def global_runtime_load(dummy: bpy.types.Scene = None):
    """
    load global actions while Blender is running from the local temp (dict)

    Args:
        dummy (bpy.types.Scene, optional): unused. Defaults to None.
    """
    AR = bpy.context.preferences.addons[__module__].preferences
    AR.global_actions.clear()
    # needed otherwise all global actions get selected
    AR["global_actions.selected_ids"] = []
    # Writes data from global_temp (JSON format) to global_actions (Blender Property)
    for action in shared_data.global_temp:
        shared.add_data_to_collection(AR.global_actions, action)


def save(AR: bpy.types.AddonPreferences):
    """
    save the global actions and categories to the storage file

    Args:
        AR (bpy.types.AddonPreferences): Blender preferences of this addon
    """
    data = {}
    data['categories'] = shared.property_to_python(
        AR.categories,
        exclude=["name", "selected", "actions.name", "areas.name", "areas.modes.name"]
    )
    data['actions'] = shared.property_to_python(
        AR.global_actions,
        exclude=["name", "selected", "alert", "macros.name", "macros.is_available", "macros.alert"]
    )
    with open(AR.storage_path, 'w', encoding='utf-8') as storage_file:
        json.dump(data, storage_file, ensure_ascii=False, indent=2)
    logger.info('saved global actions')


def load(AR: bpy.types.AddonPreferences) -> bool:
    """
    load the global actions and categories from the storage file

    Args:
        AR (bpy.types.AddonPreferences): Blender preferences of this addon

    Returns:
        bool: success
    """
    if os.path.exists(AR.storage_path):
        with open(AR.storage_path, 'r', encoding='utf-8') as storage_file:
            text = storage_file.read()
            if not text:
                text = "{}"
            data = json.loads(text)
        logger.info('load global actions')
        # cleanup
        for i in range(len(AR.categories)):
            ui_functions.unregister_category(AR, i)
        AR.categories.clear()
        AR.global_actions.clear()
        # load data
        if data:
            import_global_from_dict(AR, data)
            return True
    return False


def import_global_from_dict(AR: bpy.types.AddonPreferences, data: dict):
    """
    import the global actions and categories from a dict

    Args:
        AR (bpy.types.AddonPreferences): Blender preferences of this addon
        data (dict): dict to use
    """
    value = data.get('categories', None)
    if value:
        shared.apply_data_to_item(AR.categories, value)
    value = data.get('actions', None)
    if value:
        shared.apply_data_to_item(AR.global_actions, value)

    for i in range(len(AR.categories)):
        ui_functions.register_category(AR, i)
    if len(AR.categories):
        AR.categories[0].selected = True
    if len(AR.global_actions):
        AR.global_actions[0].selected = True


def get_global_action_id(AR: bpy.types.AddonPreferences, id: str, index: int) -> Union[str, None]:
    """
    get global action id based on id (check for existence) or index

    Args:
        AR (bpy.types.AddonPreferences): Blender preferences of this addon
        id (str): id to check
        index (int): index of action

    Returns:
        Union[str, None]: str: action id; None: fail
    """
    if AR.global_actions.find(id) == -1:
        if index >= 0 and len(AR.global_actions) > index:
            return AR.global_actions[index].id
        else:
            return None
    else:
        return id


def get_global_action_ids(AR: bpy.types.AddonPreferences, id: str, index: int) -> list:
    """
    get global action is inside a list or selected global actions if not found

    Args:
        AR (bpy.types.AddonPreferences): Blender preferences of this addon
        id (str): id to check
        index (int): index of action

    Returns:
        list: list with ids of actions
    """
    id = get_global_action_id(AR, id, index)
    if id is None:
        return AR.get("global_actions.selected_ids", [])
    return [id]


def add_empty_action_keymap(id: str) -> bpy.types.KeyMapItem:
    """
    adds an empty keymap for a global action

    Args:
        id (str): id of the action

    Returns:
        bpy.types.KeyMapItem: created keymap or found keymap of action
    """
    logger.info("add empty action")
    kmi = get_action_keymap(id)
    if kmi is None:
        kmi = keymap.keymaps['default'].keymap_items.new("ar.global_execute_action", "NONE", "PRESS")
        kmi.properties.id = id
    return kmi


def is_action_keymap_empty(kmi: bpy.types.KeyMapItem) -> bool:
    """
    checks is the given keymapitem is empty

    Args:
        kmi (bpy.types.KeyMapItem): keymapitem to check

    Returns:
        bool: is empty
    """
    return kmi.type == "NONE"


def get_action_keymap(id: str) -> Union[bpy.types.KeyMapItem, None]:
    """
    get the keymap of the action with the given id

    Args:
        id (str): id of the action

    Returns:
        Union[bpy.types.KeyMapItem, None]: KeyMapItem on success; None on fail
    """
    items = keymap.keymaps['default'].keymap_items
    for kmi in items:
        if kmi.idname == "ar.global_execute_action" and kmi.properties.id == id:
            return kmi
    return None


def remove_action_keymap(id: str):
    """
    removes the keymapitem for the action with the given id

    Args:
        id (str): id of the action
    """
    kmi = get_action_keymap(id)
    items = keymap.keymaps['default'].keymap_items
    items.remove(kmi)
# endregion
