# region Imports
# external modules
from typing import Optional

# relative imports
from . import shared
# endregion

# region Functions
def get_local_macro_index(action, id, index):
    macro = action.macros.find(id)
    if macro == -1:
        if len(action.macros) > index and index >= 0: # fallback to input index
            macro = index
        else:
            macro = action.selected_macro_index # fallback to selection
    return macro

def append_operators(AR, action, operators):
    for operator in operators:
        macro = action.macros.add()
        label = shared.get_name_of_command(operator)
        command = shared.update_command(operator)
        macro.id
        macro.label = AR.last_macro_label = label if label else operator
        macro.command = AR.last_macro_command = command if command else operator
        macro.is_available = bool(command)
    operators.clear()

def add_report_as_macro(AR, action, report: str, operators: list, compare_operators: Optional[str], error_reports: list) -> Optional[str]:
    if report.startswith('bpy.ops.'):
        report_split = report.split("(")
        if operators:
            if operators[-1].split("(")[0] != report_split[0]:
                append_operators(AR, action, operators)
            if compare_operators:
                last_ops = operators[-1]
                if last_ops.count(compare_operators) > report.count(compare_operators):
                    report = last_ops
                operators.clear()
                compare_operators = None
        operators.append(report)
    elif report.startswith('bpy.data.window_managers["WinMan"].(null)'):
        return report.split(' = ')[1]
    elif report.startswith('bpy.context.'):
        append_operators(AR, action, operators)
        macro = action.macros.add()
        label = shared.get_name_of_command(report)
        macro.id
        macro.label = AR.last_macro_label = label if label else report
        macro.command = AR.last_macro_command = report
    else:
        error_reports.append(report)
# endregion