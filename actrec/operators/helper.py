# region Imports
# blender modules
import bpy
from bpy.types import Operator
# endregion

__module__ = __package__.split(".")[0]

# Why Helper Operator?
# Helper Operator are used to mimic Operator that are executed on an object or need specific user interaction to work

# region Operators


class AR_OT_helper_object_to_collection(Operator):
    bl_idname = "ar.helper_object_to_collection"
    bl_label = "Object to Collection"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    def execute(self, context):
        active_coll = context.collection
        for obj in context.objects:
            for coll in obj.users_collection:
                coll.ojects.unlink(obj)
            active_coll.ojects.link(obj)
        return {'FINISHED'}
# endregion


classes = [
    AR_OT_helper_object_to_collection
]

# region Registration


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion
