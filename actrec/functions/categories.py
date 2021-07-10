# region Imports
# external modules
import json
import os
from typing import Optional

# blender modules
import bpy

# relative imports
from . import globals, shared
from .. import shared_data
# endregion

# region functions
def get_storage_data(AR) -> dict:
    path = AR.storage_path
    if not os.path.exists(path):
        with open(path, 'w', encoding= 'utf-8') as file:
            file.write("{}")
    with open(path, 'r', encoding= 'utf-8') as file:
        data = json.loads(file.read())
    return data

def read_category_visbility(AR, category_id) -> Optional[list]:
    """return None on Fail, dict on Successes"""
    visibility = []
    data = get_storage_data(AR)
    for category in data['categories']:
        if category['id'] == category_id:
            for area in category['areas']:
                for mode in area['modes']:
                    visibility.append((area['type'], mode['type']))
                if len(area['modes']) == 0:
                    visibility.append((area['type'], None))
            return visibility

def category_runtime_save(AR, use_autosave: bool = True) -> None:
    """includes autosave"""
    shared_data.data_manager.categories_temp = shared.property_to_python(AR.categories)
    if use_autosave and AR.autosave:
        globals.save(AR)

def adjust_categories(categories, category, change: int) -> None:
    """adjust the 'start'-property of the categories after the 'category' by the 'change' value"""
    for adjust_categorie in categories:
        if adjust_categorie.start > category.start:
            adjust_categorie.start += change

def category_visible(category, context) -> bool:
    if not len(category.areas):
        return True
    for area in category.areas:
        if context.area.ui_type == area.type:
            if len(area.modes):
                mode_from_space = {
                    'IMAGE_EDITOR': 'ui_mode',
                    'NODE_EDITOR': 'texture_type',
                    'SEQUENCE_EDITOR': 'view_type',
                    'CLIP_EDITOR': 'mode',
                    'DOPESHEET_EDITOR': 'ui_mode',
                    'FILE_BROWSER': 'mode'
                }
                space = context.space_data
                space_mode = context.mode if space.type == 'VIEW_3D' else getattr(space, mode_from_space[space.type])
                return space_mode in [mode.type for mode in area.modes]
            else:
                return True
    return False
# endregion