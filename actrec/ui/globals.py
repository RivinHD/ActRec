# region UI functions
def draw_actions(layout, AR, id: str) -> None:
    index = AR.global_actions.find(id)
    row = layout.row(align=True)
    row.alert = Data.alert_index == index
    row.prop(AR.global_actions[index], 'selected' ,toggle = 1, icon= 'LAYER_ACTIVE' if AR.global_actions[index].selected else 'LAYER_USED', text= "", event= True)
    op = row.operator(operators.AR_OT_Category_Cmd_Icon.bl_idname, text= "", icon_value= AR.global_actions[index].icon)
    op.id = id
    op.index = index
    op = row.operator(operators.AR_OT_Category_Cmd.bl_idname , text= AR.global_actions[index].name)
    op.id = id
    op.index = index
# endregion