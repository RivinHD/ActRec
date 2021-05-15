from . import actrec

bl_info = {
    "name" : "ActionRecorder",
    "author" : "InamuraJIN, Rivin",
    "version": (3, 6, 5),
    "blender": (2, 83, 12),
    "location" : "View 3D",
    "warning" : "",
    "wiki_url" : "https://github.com/InamuraJIN/CommandRecorder/blob/master/README.md",# Documentation
    "tracker_url" : "https://twitter.com/Inamura_JIN",# Report Bug
    'link': 'https://twitter.com/Inamura_JIN',
    "category" : "System"
}

def register():
    actrec.register()

def unregister():
    actrec.unregister()