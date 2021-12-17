﻿from . import actrec

bl_info = {
    "name" : "ActionRecorder",
    "author" : "InamuraJIN, Rivin",
    "version" : (4, 0, 4),
    "blender" : (2, 83, 12),
    "location" : "View 3D",
    "warning" : "",
    "docs_url" : 'https://github.com/InamuraJIN/ActionRecorder/blob/master/README.md', # Documentation
    "tracker_url" : 'https://inamurajin.wixsite.com/website/post/bug-report', # Report Bug
    "link" : 'https://twitter.com/Inamura_JIN',
    "category" : "System"
}

def register():
    actrec.register()

def unregister():
    actrec.unregister()