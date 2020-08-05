import bpy
from . import ActionRecorder as ActionRecorder

bl_info = {
    "name" : "ActionRecorder",
    "author" : "BuuGraphic, Rivin",
    "version": (0, 99, 5),
    "blender": (2, 83, 0),
    "location" : "View 3D",
    "warning" : "",
    "wiki_url" : "https://github.com/InamuraJIN/CommandRecorder/blob/master/README.md",# Documentation
    "tracker_url" : "https://twitter.com/Inamura_JIN",# Report Bug
    'link': 'https://twitter.com/Inamura_JIN',
    "category" : "System"
}

def register():
    for cl in ActionRecorder.classes:
        bpy.utils.register_class(cl)
    ActionRecorder.Initialize_Props()
    print("Register")

def unregister():
    for cl in ActionRecorder.classes:
        bpy.utils.unregister_class(cl)
    for cl in ActionRecorder.categoriesclasses:
        bpy.utils.unregister_class(cl)
    ActionRecorder.Clear_Props()
    print("UnRegister")
