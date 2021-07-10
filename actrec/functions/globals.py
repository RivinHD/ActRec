# region Imports
# external modules
import json
import os

# relative imports
from ..log import logger
from .. import ui, shared_data
from . import shared
# endregion

# region Functions
def set_enum_index(AR): #Set enum, if out of range to the first enum
    if len(AR.global_actions_enum):
        global_actions_selections= AR.get("global_actions_enum.selected_indexes", [0])
        actions_selection = global_actions_selections[0] if 0 < len(global_actions_selections) else 0
        enum_index = actions_selection * (actions_selection < len(AR.global_actions_enum))
        AR.global_actions_enum[enum_index].selected = True

def add_global_actions_enum(AR):
    new = AR.global_actions_enum.add()
    new.index = len(AR.global_actions_enum) - 1

def extract_properties(properties :str):
    properties = properties.split(",")
    new_props = []
    prop_str = ''
    for prop in properties:
        prop = prop.split('=')
        if prop[0].strip().isidentifier() and len(prop) > 1:
            new_props.append(prop_str)
            prop_str = ''
            prop_str += "=".join(prop)
        else:
            prop_str += ",%s" %prop[0]
    new_props.append(prop_str)
    return new_props[1:]

def update_macro(macro: str):
    if macro.startswith("bpy.ops."):
        command, values = macro.split("(", 1)
        values = extract_properties(values[:-1])
        for i in range(len(values)):
            values[i] = values[i].strip().split("=")
        try:
            props = eval("%s.get_rna_type().properties[1:]" %command)
        except:
            return None
        inputs = []
        for prop in props:
            for value in values:
                if value[0] == prop.identifier:
                    inputs.append("%s=%s" %(value[0], value[1]))
                    values.remove(value)
                    break
        return "%s(%s)" %(command, ", ".join(inputs))
    else:
        return False

def global_runtime_save(AR, use_autosave: bool = True):
    """includes autosave"""
    shared_data.data_manager.global_temp = shared.property_to_python(AR.global_actions)
    shared_data.data_manager.global_enum_temp = shared.property_to_python(AR.global_actions_enum)
    if use_autosave and AR.autosave:
        save(AR)

def save(AR):
    data = {}
    categories_data = []
    for category in AR.categories:
        categories_data.append({
            'id': category.id,
            'label': category.label,
            'start': category.start,
            'length': category.length,
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
            'commands': [
                {
                    'id': command.id,
                    'label': command.label,
                    'macro': command.macro,
                    'active': command.active,
                    'icon': command.icon
                } for command in action.commands
            ],
            'icon': action.icon
        })
    data['actions'] = actions_data
    with open(AR.storage_path, 'w', encoding= 'utf-8') as storage_file:
        storage_file.write(data)
    logger.info('saved global actions')

def load(AR) -> bool:
    """return Succeses"""
    if os.path.exist(AR.storage_path):
        with open(AR.storage_path, 'r', encoding= 'utf-8') as storage_file:
            data = json.loads(storage_file.read())
        logger.info('load global actions')
        # cleanup
        for category in AR.categories:
            ui.unregister_category(category)
        AR.categories.clear()
        AR.global_actions.clear()
        AR.global_actions_enum.clear()
        import_global_from_dict(AR, data)
        if len(AR.categories):
            AR.categories[0].selected = True
        if len(AR.global_actions_enum):
            AR.global_actions_enum[0].selected = True
        return True
    return False

def import_global_from_dict(AR, data: dict) -> None:
    # load categories
    for i, category in enumerate(data['categories'], len(AR.categories)):
        new_category = AR.categories.add()
        new_category.id = category['id']
        new_category.label = category['label']
        new_category.start = i + category['start']
        new_category.length = category['length']
        for area in category['areas']:
            new_area = new_category.areas.add()
            new_area.type = area['type']
            for mode in area['modes']:
                new_mode = new_area.modes.add()
                new_mode.type = mode
    # load global actions
    for i, action in enumerate(data['actions'], len(AR.global_actions_enum)):
        new_action = AR.global_actions.add()
        new_action.id = action['id']
        new_action.label = action['label']
        for commmand in action['commands']:
            result = update_macro(commmand['macro'])
            new_command = new_action.commands.add()
            new_command.id = commmand['id']
            new_command.label = commmand['label']
            new_command.macro = result if isinstance(result, str) else commmand['macro']
            new_command.active = commmand['active']
            new_command.icon = commmand['icon']
            new_command.is_available = result is not None
        new_action.icon = action['icon']
        new_enum = AR.global_actions_enum.add()
        new_enum.index = i
# endregion