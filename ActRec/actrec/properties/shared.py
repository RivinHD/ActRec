# region Imports
# external modules
import uuid

# blender modules
import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, IntProperty, CollectionProperty, BoolProperty

# relative imports
from .. import functions
from ..functions.shared import get_preferences
# endregion

# region PropertyGroups


class Id_based:
    def get_id(self) -> str:
        """
        get id as UUID,
        generates new UUID if id is not set

        Returns:
            str: UUID in hex format
        """
        self['name'] = self.get('name', uuid.uuid1().hex)
        return self['name']

    def set_id(self, value: str):
        """
        Create a UUID from a string of 32 hexadecimal digits

        Args:
            value (str): preferred UUID in hex format

        Raises:
            ValueError: unparsable value into UUID get raised
        """
        try:
            self['name'] = uuid.UUID(value).hex
        except ValueError as err:
            raise ValueError("%s with %s" % (err, value))

    # needed for easier access to the types of the category
    # id and name are the same, because CollectionProperty use property 'name' as key
    name: StringProperty(get=get_id)
    # create id by calling get-function of id
    id: StringProperty(get=get_id, set=set_id)


class Alert_system:
    def get_alert(self) -> bool:
        """
        default Blender property getter

        Returns:
            bool: alert state
        """
        return self.get('alert', False)

    def set_alert(self, value: bool):
        """
        automatically reset the alert after 1 second to false again,
        because alert is only shown temporarily in the UI

        Args:
            value (bool): change alert state
        """
        self['alert'] = value
        if value:
            def reset():
                self['alert'] = False
            bpy.app.timers.register(reset, first_interval=1, persistent=True)

    def update_alert(self, context: bpy.types.Context):
        """
        redraw the area to show the alert change in the UI

        Args:
            context (bpy.types.Context): active blender context
        """
        if hasattr(context, 'area') and context.area:
            context.area.tag_redraw()

    alert: BoolProperty(default=False, description="Internal use",
                        get=get_alert, set=set_alert, update=update_alert)


class AR_macro(Id_based, Alert_system, PropertyGroup):
    def get_active(self) -> bool:
        """
        default Blender property getter with extra check if the macro is available

        Returns:
            bool: state of macro, true if active, always false if macro is not available
        """
        return self.get('active', True) and self.is_available

    def set_active(self, value: bool):
        """
        set the active state if macro is available and macro recording is turned off
        if the value change it is written to the local scene data if autosave is active

        Args:
            value (bool): state of macro
        """
        if self.is_available:
            context = bpy.context
            ActRec_pref = get_preferences(context)
            if not ActRec_pref.local_record_macros:
                if self.get('active', True) != value:
                    functions.local_runtime_save(ActRec_pref, context.scene)
                self['active'] = value

    def get_command(self) -> str:
        """
        default Blender property getter

        Returns:
            str: command of macro
        """
        return self.get("command", "")

    def set_command(self, value: str):
        """
        sets the macro command and updates it with the running Blender version
        if the command isn't found in the running Blender it will be marked as not available

        Args:
            value (str): command to set to
        """
        res = functions.update_command(value)
        self['command'] = res if isinstance(res, str) else value
        self['is_available'] = res is not None

    def get_is_available(self) -> bool:
        """
        default Blender property getter

        Returns:
            bool: state if macro is available
        """
        return self.get('is_available', True)

    label: StringProperty()
    command: StringProperty(get=get_command, set=set_command)
    active: BoolProperty(
        default=True, description='Toggles Macro on and off.', get=get_active, set=set_active)
    # Icon NONE: Global: BLANK1 (101), Local: MESH_PLANE (286)
    icon: IntProperty(default=0)
    is_available: BoolProperty(default=True, get=get_is_available)
    ui_type: StringProperty(default="")


class AR_action(Id_based, Alert_system):
    label: StringProperty()
    macros: CollectionProperty(type=AR_macro)
    # Icon NONE: Global: BLANK1 (101), Local: MESH_PLANE (286)
    icon: IntProperty(default=0)


class AR_scene_data(PropertyGroup):  # as Scene PointerProperty
    local: StringProperty(
        name="Local",
        description='Scene Backup-Data of AddonPreference.local_actions (json format)',
        default='{}'
    )
    record_undo_end: BoolProperty(
        name="Undo End",
        description="Used to get the undo step before the record started to compare the undo steps (INTERNAL)",
        default=False
    )
# endregion


classes = [
    AR_macro,
    AR_scene_data,
    # AR_keymap
]

# region Registration


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion
