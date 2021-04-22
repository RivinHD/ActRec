import bpy
from . import ActionRecorder as ActionRecorder
import logging
import logging.handlers
import os
import sys

bl_info = {
    "name" : "ActionRecorder",
    "author" : "InamuraJIN, Rivin",
    "version": (3, 6, 2),
    "blender": (2, 83, 12),
    "location" : "View 3D",
    "warning" : "",
    "wiki_url" : "https://github.com/InamuraJIN/CommandRecorder/blob/master/README.md",# Documentation
    "tracker_url" : "https://twitter.com/Inamura_JIN",# Report Bug
    'link': 'https://twitter.com/Inamura_JIN',
    "category" : "System"
}

#Logging System
class Logger:
    def __init__(self, count: int):
        dirc = os.path.join(os.path.dirname(__file__), "logs")
        if not os.path.exists(dirc):
            os.mkdir(dirc)
        path = os.path.join(dirc, "ActRec.log")
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        file_formatter = logging.Formatter("%(levelname)s - %(relativeCreated)d - %(funcName)s - %(message)s")
        file_handler = logging.handlers.RotatingFileHandler(path, mode='a', backupCount= count, encoding= 'utf-8', delay= True)
        file_handler.doRollover() # Save last Session as Backup and start with clean file
        file_handler.setLevel(logger.level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        logger.info("ActRec Logger started with %i Backups" %count)
        self.logger = logger

        sys.excepthook = self.exception_handler
    
    def exception_handler(self, type, value, tb):
        self.logger.exception(str(type) + ": " + str(value))
        self.logger.error(tb)
logger = Logger(5).logger

def register():
    for cls in ActionRecorder.classes:
        bpy.utils.register_class(cls)
    for cls in ActionRecorder.classespanel:
        bpy.utils.register_class(cls)
    for cls in ActionRecorder.blendclasses:
        try:
            bpy.utils.register_class(cls)
        except:
            continue
    ActionRecorder.Initialize_Props()
    logger.info("Registered Action Recorder")

def unregister():
    for cls in ActionRecorder.classes:
        bpy.utils.unregister_class(cls)
    for cls in ActionRecorder.categoriesclasses:
        try:
            bpy.utils.unregister_class(cls)
        except:
            continue
    for cls in ActionRecorder.classespanel:
        bpy.utils.unregister_class(cls)
    for cls in ActionRecorder.blendclasses:
        try:
            bpy.utils.unregister_class(cls)
        except:
            continue
    ActionRecorder.Clear_Props()
    logger.info("Unregistered Action Recorder")
