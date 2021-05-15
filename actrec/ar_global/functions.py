# region Import
# 
# endregion


# region Functions
def SetEnumIndex(): #Set enum, if out of range to the first enum
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    scene = bpy.context.scene
    if len(AR_Var.ar_enum):
        enumIndex = AR_Var.Instance_Index * (AR_Var.Instance_Index < len(AR_Var.ar_enum))
        AR_Var.ar_enum[enumIndex].Value = True
        AR_Var.Instance_Index = enumIndex

# endregion
