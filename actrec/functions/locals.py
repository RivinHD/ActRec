# region Imports
# external modules
import json

# blender modules
import bpy

# relative imports
from .. import shared_data
from . import shared
# endregion

# region Functions
def local_runtime_save(AR, scene: bpy.types.Scene, use_autosave: bool = True) -> None:
    """includes autosave to scene (depend on AddonPreference autosave)"""
    shared_data.local_temp = shared.property_to_python(AR.local_actions)
    if use_autosave and AR.autosave:
        scene.ar.local = json.dumps(shared_data.local_temp)

def save_local_to_scene(AR, scene):
    scene.ar.local = json.dumps(shared.property_to_python(AR.local_actions))

def get_local_action_index(AR, id, index):
    action = AR.local_actions.find(id)
    if action == -1:
        if len(AR.local_actions) > index and index >= 0: # fallback to input index
            action = index
        else:
            index = AR.selected_local_action_index # fallback to selection
    return action

def load_local_action(AR, data: list):
    actions = AR.local_actions
    actions.clear()
    for value in data:
        shared.add_data_to_collection(actions, value)

# endregion
