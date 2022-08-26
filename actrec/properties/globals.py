# region Imports
# blender modules
import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, StringProperty, CollectionProperty

# relative Imports
from . import shared
# endregion

__module__ = __package__.split(".")[0]

# region PropertyGroups


class AR_global_actions(shared.AR_action, PropertyGroup):
    def get_selected(self) -> bool:
        """
        default Blender property getter

        Returns:
            bool: selected state of action
        """
        return self.get("selected", False)

    def set_selected(self, value: bool):
        """
        set selected macro or if ctrl is pressed multiple macros can be selected
        if ctrl is not pressed all selected macros get deselected except the new selected.

        Args:
            value (bool): state of selection
        """
        AR = bpy.context.preferences.addons[__module__].preferences
        selected_ids = list(AR.get("global_actions.selected_ids", []))
        # implementation similar to a UIList (only one selection of all can be active),
        # with extra multi selection by pressing ctrl
        if len(selected_ids) > 1:
            value = True
        if value:
            # uses check_ctrl operator to check for ctrl event
            ctrl_value = bpy.ops.ar.check_ctrl('INVOKE_DEFAULT')
            # {'CANCELLED'} == ctrl is not pressed
            if selected_ids and ctrl_value == {'CANCELLED'}:
                AR["global_actions.selected_ids"] = []
                for selected_id in selected_ids:
                    action = AR.global_actions.get(selected_id, None)
                    if action:
                        action.selected = False
                selected_ids.clear()
            selected_ids.append(self.id)
            AR["global_actions.selected_ids"] = selected_ids
            self['selected'] = value
        elif not (self.id in selected_ids):
            self['selected'] = value

    selected: BoolProperty(
        default=False,
        set=set_selected,
        get=get_selected,
        description="Select this Action Button\nuse ctrl to select multiple",
        name='Select'
    )


class AR_global_import_action(PropertyGroup):
    def get_use(self) -> bool:
        """
        get state whether the action will be used to import
        with extra check if the category of this action is also selected for import

        Returns:
            bool: action import state
        """
        return self.get('use', True) and self.get('category.use', True)

    def set_use(self, value: bool):
        """
        set state whether the action will be used to import

        Args:
            value (bool): action import state
        """
        if self.get('category.use', True):
            self['use'] = value

    label: StringProperty()
    identifier: StringProperty()
    use: BoolProperty(default=True,
                      name="Import Action",
                      description="Decide whether to import the action",
                      get=get_use,
                      set=set_use
                      )


class AR_global_import_category(PropertyGroup):
    def get_use(self) -> bool:
        """
        get state whether the category will be used to import

        Returns:
            bool: category import state
        """
        return self.get("use", True)

    def set_use(self, value: bool):
        """
        set state whether the category will be used to import

        Args:
            value (bool): category import state
        """
        self['use'] = value
        # needed for the action to check if there category is imported
        for action in self.actions:
            action['category.use'] = value

    label: StringProperty()
    identifier: StringProperty()
    actions: CollectionProperty(type=AR_global_import_action)
    show: BoolProperty(default=True)
    use: BoolProperty(default=True, name="Import Category",
                      description="Decide whether to import the category", get=get_use, set=set_use)


class AR_global_export_action(shared.Id_based, PropertyGroup):
    def get_use(self) -> bool:
        """
        get state whether the action will be used to export
        with extra check if the category of this action is also selected for export or export_all is active

        Returns:
            bool: action export state
        """
        return self.get("use", True) and self.get('category.use', True) or self.get('export_all', False)

    def set_use(self, value: bool):
        """
        set state whether the action will be used to export

        Args:
            value (bool): action export state
        """
        if self.get('category.use', True) and not self.get('export_all', False):
            self['use'] = value

    label: StringProperty()
    use: BoolProperty(default=True, name="Import Action",
                      description="Decide whether to export the action", get=get_use, set=set_use)


class AR_global_export_categories(shared.Id_based, PropertyGroup):
    def get_use(self) -> bool:
        """
        get state whether the category will be used to export or export_all is active

        Returns:
            bool: category export state
        """
        return self.get("use", True) or self.get("export_all", False)

    def set_use(self, value: bool):
        """
        set state whether the category will be used to export

        Args:
            value (bool): category export state
        """
        if not self.get("export_all", False):
            self['use'] = value
            for action in self.actions:
                action['category.use'] = value

    label: StringProperty()
    actions: CollectionProperty(type=AR_global_export_action)
    show: BoolProperty(default=True)
    use: BoolProperty(default=True, name="Export Category",
                      description="Decide whether to export the category", get=get_use, set=set_use)
# endregion


classes = [
    AR_global_actions,
    AR_global_import_action,
    AR_global_import_category,
    AR_global_export_action,
    AR_global_export_categories
]

# region Registration


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion
