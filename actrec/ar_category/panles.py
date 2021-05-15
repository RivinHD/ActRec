# region Import
# blender module
from bpy.types import Panel

# relativ import
from ..preferences import AR_preferences

# endregion

# region Panels

def register_categories(): #Register all Categories
    for i in range(catlength[0]):
        register_unregister_category(i)

def register_category(index):
    register_unregister_category(index)

def unregister_category(index):
    register_unregister_category(index, False)

def register_unregister_category(index, register = True): #Register/Unregister one Category
    for spaceType in AR_preferences.space_types:
        class AR_PT_Category(Panel):
            bl_space_type = spaceType
            bl_region_type = 'UI'
            bl_category = 'Action Recorder'
            bl_label = ' '
            bl_idname = "AR_PT_Category_%s_%s" %(index, spaceType)
            bl_parent_id = "AR_PT_Global_%s" % spaceType
            bl_order = index + 1

            @classmethod
            def poll(self, context):
                AR_Var = context.preferences.addons[__package__].preferences
                index = int(self.bl_idname.split("_")[3])
                if len(AR_Var.Categories) <= index:
                    Load()
                category = AR_Var.Categories[index]
                return showCategory(category.pn_name, context)

            def draw_header(self, context):
                AR_Var = context.preferences.addons[__package__].preferences
                index = int(self.bl_idname.split("_")[3])
                category = AR_Var.Categories[index]
                layout = self.layout
                row = layout.row()
                row.prop(AR_Var.Selected_Category[index], 'selected', text= '', icon= 'LAYER_ACTIVE' if AR_Var.Selected_Category[index].selected else 'LAYER_USED', emboss= False)
                row.label(text= category.pn_name)

            def draw(self, context):
                AR_Var = context.preferences.addons[__package__].preferences
                scene = context.scene
                index = int(self.bl_idname.split("_")[3])
                category = AR_Var.Categories[index]
                layout = self.layout
                col = layout.column()
                for i in range(category.Instance_Start, category.Instance_Start + category.Instance_length):
                    row = col.row(align=True)
                    row.alert = Data.alert_index == i
                    row.prop(AR_Var.category_action_enum[i], 'Value' ,toggle = 1, icon= 'LAYER_ACTIVE' if AR_Var.category_action_enum[i].Value else 'LAYER_USED', text= "", event= True)
                    row.operator(AR_OT_Category_Cmd_Icon.bl_idname, text= "", icon_value= AR_Var.Instance_Coll[i].icon).index = i
                    row.operator(AR_OT_Category_Cmd.bl_idname , text= AR_Var.Instance_Coll[i].name).Index = i
        AR_PT_Category.__name__ = "AR_PT_Category_%s_%s" %(index, spaceType)
        if register:
            bpy.utils.register_class(AR_PT_Category)
            categoriesclasses.append(AR_PT_Category)
        else:
            try:
                panel = eval("bpy.types." + AR_PT_Category.__name__)
                bpy.utils.unregister_class(panel)
                categoriesclasses.remove(panel)
            except:
                pass
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    if register:
        new = AR_Var.Selected_Category.add()
        new.index = index
    else:
        AR_Var.Selected_Category.remove(len(AR_Var.Selected_Category) - 1)
    if get_selected_index(AR_Var.Selected_Category) is None and len(AR_Var.Selected_Category):
        AR_Var.Selected_Category[0].selected = True
# endregion
