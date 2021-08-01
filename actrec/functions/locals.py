# region Imports
# external modules
import json
from typing import Optional

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

def get_report_text(self, context) -> str:
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

def append_operators(self, action, operators):
    for operator in operators:
        macro = action.macros.add()
        label = shared.get_name_of_command(operator)
        command = shared.update_command(operator)
        macro.id
        macro.label = label if label else operator
        macro.command = command if command else operator
        macro.is_available = bool(command)
    operators.clear()

def add_report_as_macro(action, report: str, operators: list, compare_operators: bool, error_reports: list) -> Optional[str]:
    if report.startswith('bpy.ops.'):
        report_split = report.split("(")
        if operators:
            if operators[-1].split("(")[0] != report_split[0]:
                append_operators(action, operators)
            if compare_operators:
                last_ops = operators[-1]
                if last_ops.count(compare_operators) > report.count(compare_operators):
                    report = last_ops
                operators.clear()
                compare_operators = False
        operators.append(report)
    elif report.startswith('bpy.data.window_managers["WinMan"].(null)'):
        return report.split(' = ')[1]
    elif report.startswith('bpy.context.'):
        append_operators(action, operators)
        macro = action.macros.add()
        label = shared.get_name_of_command(report)
        macro.id
        macro.label = label if label else report
        macro.command = report
    else:
        error_reports.append(report)
# endregion
