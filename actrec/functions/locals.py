# region Imports
# external modules
import json

# blender modules
import bpy
from bpy.app.handlers import persistent

# relative imports
from .. import shared_data
from . import shared
# endregion

__module__ = __package__.split(".")[0]

# region Functions


def local_runtime_save(AR: bpy.types.AddonPreferences, scene: bpy.types.Scene, use_autosave: bool = True):
    """
    save local action to the local temp (dict) while Blender is running

    Args:
        AR (bpy.types.AddonPreferences): Blender preferences of this addon
        scene (bpy.types.Scene): Blender scene to write to
        use_autosave (bool, optional): include autosave to scene (depend on AddonPreference autosave). Defaults to True.
    """
    shared_data.local_temp = shared.property_to_python(AR.local_actions)
    if use_autosave and AR.autosave and scene:
        scene.ar.local = json.dumps(shared_data.local_temp)


@persistent
def local_runtime_load(dummy: bpy.types.Scene = None):
    """
    loads local actions from the local temp (dict) while Blender is running

    Args:
        dummy (bpy.types.Scene, optional): unused. Defaults to None.
    """
    AR = bpy.context.preferences.addons[__module__].preferences
    AR.local_actions.clear()
    for action in shared_data.local_temp:
        shared.add_data_to_collection(AR.local_actions, action)


def save_local_to_scene(AR: bpy.types.AddonPreferences, scene: bpy.types.Scene):
    """
    saves all local actions to the given scene

    Args:
        AR (bpy.types.AddonPreferences): Blender preferences of this addon
        scene (bpy.types.Scene): Blender scene to write to
    """
    scene.ar.local = json.dumps(shared.property_to_python(AR.local_actions))


def get_local_action_index(AR: bpy.types.AddonPreferences, id: str, index: int) -> int:
    """
    get local action index based on the given id or index (checks if index is in range)

    Args:
        AR (bpy.types.AddonPreferences): Blender preferences of this addon
        id (str): id to get index from
        index (int): index for fallback

    Returns:
        int: valid index of a local actions or active local action index on fallback
    """
    action = AR.local_actions.find(id)
    if action == -1:
        if index >= 0 and len(AR.local_actions) > index:  # fallback to input index
            action = index
        else:
            action = AR.active_local_action_index  # fallback to selection
    return action


def load_local_action(AR: bpy.types.AddonPreferences, data: list):
    """
    load the given data to the local actions

    Args:
        AR (bpy.types.AddonPreferences): Blender preferences of this addon
        data (list): data to apply
    """
    actions = AR.local_actions
    actions.clear()
    for value in data:
        shared.add_data_to_collection(actions, value)


def local_action_to_text(action: 'AR_local_actions', text_name: str = None):
    """
    write the local action and it's macro the the TextEditor

    Args:
        action (AR_local_actions): action to write
        text_name (str, optional): name of the written text. Defaults to None.
    """
    if text_name is None:
        text_name = action.label
    texts = bpy.data.texts
    if texts.find(text_name) == -1:
        texts.new(text_name)
    text = texts[text_name]
    text.clear()
    text.write(
        "###AR### id: '%s', icon: %i\n%s" % (
            action.id, action.icon, "\n".join(
                ["%s # id: '%s', label: '%s', icon: %i, active: %s, is_available: %s" % (
                    macro.command, macro.id, macro.label, macro.icon, macro.active, macro.is_available
                ) for macro in action.macros]
            )
        )
    )
# endregion
