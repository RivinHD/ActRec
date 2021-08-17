# region Imports
# external modules
import json
from typing import Optional, Tuple, Union

# blender modules
import bpy
from bpy.app.handlers import persistent

# relative imports
from .. import shared_data
from . import shared
# endregion

# region Functions
def local_runtime_save(AR, scene: bpy.types.Scene, use_autosave: bool = True) -> None:
    """includes autosave to scene (depend on AddonPreference autosave)"""
    shared_data.local_temp = shared.property_to_python(AR.local_actions)
    if use_autosave and AR.autosave and scene:
        scene.ar.local = json.dumps(shared_data.local_temp)

@persistent
def local_runtime_load(dummy = None):
    AR = bpy.context.preferences.addons[__package__].preferences
    AR.local_actions.clear()
    for action in shared_data.global_temp:
        shared.add_data_to_collection(AR.local_actions, action)

def save_local_to_scene(AR, scene):
    scene.ar.local = json.dumps(shared.property_to_python(AR.local_actions))

def get_local_action_index(AR, id, index):
    action = AR.local_actions.find(id)
    if action == -1:
        if index >= 0 and len(AR.local_actions) > index: # fallback to input index
            action = index
        else:
            action = AR.selected_local_action_index # fallback to selection
    return action

def load_local_action(AR, data: list):
    actions = AR.local_actions
    actions.clear()
    for value in data:
        shared.add_data_to_collection(actions, value)

def local_action_to_text(action, text_name = None):
    if text_name is None:
        text_name = action.label
    texts = bpy.data.texts
    if texts.find(text_name) == -1:
        texts.new(text_name)
    text = texts[text_name]
    text.clear()
    text.write("###AR### id: %s, icon: %i\n%s" %(action.id, action.icon, 
        "\n".join(["%s # id: %s, label: %s, icon: %i, active: %b, is_available: %b"
        %(macro.command, macro.id, macro.label, macro.icon, macro.active, macro.is_available) for macro in action.macros])
        )
    )

def get_report_text(context) -> str:
    override = context.copy()
    area_type = override['area'].type
    clipboard_data = override['window_manager'].clipboard
    override['area'].type = 'INFO'
    bpy.ops.info.select_all(override, action= 'SELECT')
    bpy.ops.info.report_copy(override)
    bpy.ops.info.select_all(override, action= 'DESELECT')
    report_text = override['window_manager'].clipboard
    override['area'].type = area_type
    override['window_manager'].clipboard = clipboard_data
    return report_text

def split_context_report(report) -> Tuple[list, str, str]:
    base, value = report.split(" = ")
    split = base.replace("bpy.context.", "").split(".")
    return split[:-1], split[-1], value # source_path, attribute, value

def get_id_object(context, source_path, attribute):
    if source_path[0] == 'area':
        for area in context.screen.areas:
            if hasattr(area, attribute):
                return area
    elif source_path[0] == 'space_data':
        for area in context.screen.areas:
            for space in area.spaces:
                if hasattr(space, attribute):
                    return space
    id_object = context
    for x in source_path:
        id_object = getattr(id_object, x)
    return id_object

def get_copy_of_object(data, obj, attribute, depth= 5):
    if hasattr(obj, attribute):
        return getattr(obj, attribute)
    for prop in obj.bl_rna.properties[1: ]:
        if prop.type == 'COLLECTION' or prop.type == 'POINTER':
            res = get_copy_of_object({}, getattr(obj, prop.identifier), attribute, depth - 1)
            if res:
                data[prop.identifier] = res
    return data

def create_object_copy(context, source_path: list, attribute: str) -> dict:
    data = {}
    id_object = get_id_object(context, source_path, attribute)
    res = get_copy_of_object(data, id_object, attribute)
    if res and not isinstance(res, dict):
        data[attribute] = res
    return data

def check_object_report(object, copy_dict, source_path, attribute, value):
    if hasattr(object, attribute) and getattr(object, attribute) != copy_dict[attribute]:
        return object.__class__.__name__, ".".join(source_path), attribute, value
    for key in copy_dict:
        if hasattr(object, key):
            res = check_object_report(getattr(object, key), copy_dict[key], [*source_path, key],  attribute, value)
            if res:
                return res

def improve_context_report(context, copy_dict: dict, source_path: list, attribute: str, value: str) -> Optional[str]:
    id_object = get_id_object(context, source_path, attribute)
    if hasattr(id_object, attribute):
        object_class = id_object.__class__.__name__
        res = [".".join(source_path), attribute, value]
    else:
        object_class, *res = check_object_report(id_object, copy_dict, source_path, attribute, value)
    for attr in context.__dir__():
        if object_class == getattr(bpy.context, attr).__class__.__name__:
            res[0] = attr
    return "bpy.context.%s.%s = %s" %res

def split_operator_report(operator_str: str) -> Tuple[str, str, dict]:
    ops_type, ops_name = operator_str.replace("bpy.ops.", "").split("(")[0].split(".")
    ops_values = {}
    key = ""
    for x in "(".join(operator_str.split("(")[1:])[:-1].split(","):
        split = x.split("=")
        if split[0].strip().isidentifier() and len(split) > 1:
            key = split[0]
            ops_values[key] = split[1]
        else:
            ops_values[key] += ",%s"%(split[0])
    return ops_type, ops_name, ops_values

def get_collection_data(collection) -> dict:
    data = {'name': collection.name}
    data['children'] = [get_collection_data(child) for child in collection.children]
    data['objects'] = set(obj.name for obj in collection.objects)
    return data

def create_operator_based_copy(context, ops_type: str, ops_name: str, ops_values: dict) -> Union[dict, False, None]:
    if ops_type == "outliner":
        if ops_name in set("item_activate", "item_rename"):
            return False
        elif ops_name == "collection_drop":
            master = context.scene.collection
            return get_collection_data(master)

def imporve_operator_report(context, operator_str: str):
    pass
# endregion
