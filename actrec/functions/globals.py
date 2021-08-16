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
    categories_data = []
    for category in AR.categories:
        categories_data.append({
            'id': category.id,
            'label': category.label,
            'actions': [
                {
                    "id": id_action.id
                } for id_action in category.actions
            ],
            'areas': [
                {
                    'type': area.type,
                    'modes': [
                        {
                            'type': mode.type
                        } for mode in area.modes
                    ]
                } for area in category.areas
            ]
        })
    data['categories'] = categories_data
    actions_data = []
    for action in AR.global_actions:
        actions_data.append({
            'id': action.id,
            'label': action.label,
            'macros': [
                {
                    'id': macro.id,
                    'label': macro.label,
                    'macro': macro.macro,
                    'active': macro.active,
                    'icon': macro.icon
                } for macro in action.macros
            ],
            'icon': action.icon
        })
    data['actions'] = actions_data
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
    # load categories
    for category in data['categories']:
        new_category = AR.categories.add()
        new_category.id = category['id']
        new_category.label = category['label']
        for action in category['actions']:
            new_action = new_category.actions.add()
            new_action.id = action['id']
        for area in category['areas']:
            new_area = new_category.areas.add()
            new_area.type = area['type']
            for mode in area['modes']:
                new_mode = new_area.modes.add()
                new_mode.type = mode
    # load global actions
    for action in data['actions']:
        new_action = AR.global_actions.add()
        new_action.id = action['id']
        new_action.label = action['label']
        for macro in action['macros']:
            result = shared.update_command(macro['command'])
            new_macro = new_action.macros.add()
            new_macro.id = macro['id']
            new_macro.label = macro['label']
            new_macro.command = result if isinstance(result, str) else macro['command']
            new_macro.active = macro['active']
            new_macro.icon = macro['icon']
            new_macro.is_available = result is not None
        new_action.icon = action['icon']

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