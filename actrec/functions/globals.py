# region Imports
# external modules
import json
import os

# blender modules
import bpy
from bpy.app.handlers import persistent

# relative imports
from ..log import logger
from .. import ui_functions, shared_data
from . import shared
# endregion

# region Functions
def global_runtime_save(AR, use_autosave: bool = True):
    """includes autosave"""
    shared_data.global_temp = shared.property_to_python(AR.global_actions)
    if use_autosave and AR.autosave:
        save(AR)

@persistent
def global_runtime_load(dummy = None):
    AR = bpy.context.preferences.addons[__package__].preferences
    AR.global_actions.clear()
    for action in shared_data.global_temp:
        shared.add_data_to_collection(AR.global_actions, action)

def save(AR):
    data = {}
    data['categories'] = shared.property_to_python(AR.categories, exclude= ["name", "actions.name", "areas.name", "areas.modes.name"])
    data['actions'] = shared.property_to_python(AR.global_actions, exclude= ["name", "selected", "macros.name", "macros.is_available"])
    with open(AR.storage_path, 'w', encoding= 'utf-8') as storage_file:
        json.dumps(data, storage_file, ensure_ascii= False, indent= 4)
    logger.info('saved global actions')

def load(AR) -> bool:
    """return Succeses"""
    if os.path.exist(AR.storage_path):
        with open(AR.storage_path, 'r', encoding= 'utf-8') as storage_file:
            data = json.load(storage_file)
        logger.info('load global actions')
        # cleanup
        for category in AR.categories:
            ui_functions.unregister_category(category)
        AR.categories.clear()
        AR.global_actions.clear()
        import_global_from_dict(AR, data)
        for category in AR.categories:
            ui_functions.register_category(AR, category)
        if len(AR.categories):
            AR.categories[0].selected = True
        if len(AR.global_actions):
            AR.global_actions[0].selected = True
        return True
    return False

def import_global_from_dict(AR, data: dict) -> None:
    shared.apply_data_to_item(AR.categories, data['categories'])
    shared.apply_data_to_item(AR.global_actions, data['actions'])

def get_global_action_id(AR, id, index):
    if AR.global_actions.find(id) == -1:
        if index >= 0 and len(AR.global_actions) > index:
            id = AR.global_actions[index].id
        else:
            return None
    else:
        return id

def get_global_action_ids(AR, id, index):
    id = get_global_action_id(AR, id, index)
    if id is None:
        return AR.get("global_actions.selected_ids", [])
    return [id]
# endregion