from .. import operators

# region UI functions
def draw_actions(layout, AR, index: int) -> None:
    row = layout.row(align=True)
    row.alert = Data.alert_index == index
    row.prop(AR.category_action_enum[index], 'selected' ,toggle = 1, icon= 'LAYER_ACTIVE' if AR.category_action_enum[index].selected else 'LAYER_USED', text= "", event= True)
    row.operator(operators.AR_OT_Category_Cmd_Icon.bl_idname, text= "", icon_value= AR.global_actions[index].icon).index = index
    row.operator(operators.AR_OT_Category_Cmd.bl_idname , text= AR.global_actions[index].name).index = index
# endregion