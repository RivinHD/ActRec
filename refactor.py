﻿# region Imports
from typing import Optional
import bpy
from bpy.app.handlers import persistent
import os
import shutil
import json
from json.decoder import JSONDecodeError
import zipfile
import time
import webbrowser
from addon_utils import check, paths, enable
from .config import config
import atexit
from urllib import request
from io import BytesIO
from . import __init__ as init
import base64
import random
import math
import inspect
import functools
import numpy as np
import copy
import importlib
from importlib import reload
from .Category import Category as CatVisibility
import queue
import subprocess
import ensurepip
import sys
import re
import logging

from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, EnumProperty, PointerProperty, CollectionProperty
from bpy.types import Panel, UIList, Operator, PropertyGroup, AddonPreferences, Menu
from bpy_extras.io_utils import ImportHelper, ExportHelper
import bpy.utils.previews
# endregion

# region Variables
classes = []
classespanel = []
categoriesclasses = []
blendclasses = []
catlength = [0]
ontempload = [False]
multiselection_buttons = [False, True]
oninit = [False]
catVisPath = os.path.join(os.path.dirname(__file__), "Category.py")
execution_queue = queue.Queue()
logger = logging.getLogger(__package__)

class Data:
    Edit_Command = None
    Record_Edit_Index = None
    Commands_RenderComplete = []
    Commands_RenderInit = []
    CatVisis = []
    alert_index = None
    activeareas = []
    ActiveTimers = 0
# endregion

# region UIList
class AR_UL_Selector(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        self.use_filter_show = False
        self.use_filter_sort_lock = True
        row = layout.row(align= True)
        row.alert = item.alert
        row.operator(AR_OT_Record_Icon.bl_idname, text= "", icon_value= AR_Var.Record_Coll[0].Command[index].icon, emboss= False).index = index
        col = row.column()
        col.ui_units_x = 0.5
        row.prop(item, 'cname', text= '', emboss= False)
classes.append(AR_UL_Selector)
class AR_UL_Command(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        self.use_filter_show = False
        self.use_filter_sort_lock = True
        row = layout.row(align= True)
        row.alert = item.alert
        row.prop(item, 'active', text= "")
        row.operator(AR_OT_Command_Edit.bl_idname, text= item.macro, emboss= False).index = index
classes.append(AR_UL_Command)

# endregion

# region Functions
def CheckCommand(num): #Add a new Collection if necessary
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    while len(AR_Var.Record_Coll) <= num:
        AR_Var.Record_Coll.add()
    return num

def Get_Recent(Return_Bool):
    #remove other Recent Reports
    reports = \
    [
    bpy.data.texts.remove(t)
    for t in bpy.data.texts
        if t.name.startswith('Recent Reports')
    ]
    # make a report
    win = bpy.context.window_manager.windows[0]
    area = win.screen.areas[0]
    area_type = area.type
    area.type = 'INFO'
    override = bpy.context.copy()
    override['window'] = win
    override['screen'] = win.screen
    override['area'] = win.screen.areas[0]
    bpy.ops.info.select_all(override, action='SELECT')
    bpy.ops.info.report_copy(override)
    area.type = area_type
    clipboard = bpy.context.window_manager.clipboard
    bpy.data.texts.new('Recent Reports')
    bpy.data.texts['Recent Reports'].write(clipboard)
    # print the report
    if Return_Bool == 'Reports_All':
        return bpy.data.texts['Recent Reports'].lines
    elif Return_Bool == 'Reports_Length':
        return len(bpy.data.texts['Recent Reports'].lines)

def GetMacro(name):
    if name.startswith("bpy.ops"):
        try:
            return eval(name.split("(")[0] + ".get_rna_type().name")
        except:
            return name
    elif name.startswith('bpy.data.window_managers["WinMan"].(null)'):
        return True
    elif name.startswith('bpy.context'):
        split = name.split('=')
        if len(split) > 1:
            return split[0].split('.')[-1] + " = " + split[1]
        else:
            return ".".join(split[0].split('.')[-2:])
    else:
        return None

def Record(Num, Mode):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    Recent = Get_Recent('Reports_All')
    if Mode == 'Start':
        AR_preferences.Record = True
        AR_preferences.Temp_Num = len(Recent)
        bpy.data.texts.remove(bpy.data.texts['Recent Reports'])
    else:
        AR_preferences.Record = False
        notadded = []
        startCommand = ""
        lastCommand = ""
        for i in range(AR_preferences.Temp_Num, len(Recent)):
            TempText = Recent[i - 1].body
            if TempText.count('bpy'):
                name = TempText[TempText.find('bpy'):]
                if lastCommand.split("(", 1)[0] == name.split("(", 1)[0] and startCommand != name:
                    lastCommand = name
                    continue
                macro = GetMacro(name)
                if macro is True:
                    continue
                if startCommand != lastCommand:
                    lastMacro = GetMacro(lastCommand)
                    if lastMacro is None:
                        notadded.append(name)
                        if AR_Var.CreateEmpty:
                            Item = AR_Var.Record_Coll[CheckCommand(Num)].Command[-1]
                            Item.macro = "<Empty>"
                            Item.cname = ""
                    else:
                        Item = AR_Var.Record_Coll[CheckCommand(Num)].Command[-1]
                        Item.macro = lastMacro
                        Item.cname = lastCommand
                lastCommand = name
                startCommand = name
                if macro is None:
                    notadded.append(name)
                    if AR_Var.CreateEmpty:
                        Item = AR_Var.Record_Coll[CheckCommand(Num)].Command.add()
                        Item.macro = "<Empty>"
                        Item.cname = ""
                else:
                    Item = AR_Var.Record_Coll[CheckCommand(Num)].Command.add()
                    Item.macro = macro
                    Item.cname = name
        if startCommand != lastCommand:
            lastMacro = GetMacro(lastCommand)
            if lastMacro is None:
                notadded.append(name)
                if AR_Var.CreateEmpty:
                    Item = AR_Var.Record_Coll[CheckCommand(Num)].Command[-1]
                    Item.macro = "<Empty>"
                    Item.cname = ""
            else:
                Item = AR_Var.Record_Coll[CheckCommand(Num)].Command[-1]
                Item.macro = lastMacro
                Item.cname = lastCommand
        UpdateRecordText(Num)
        bpy.data.texts.remove(bpy.data.texts['Recent Reports'])
        return notadded

def CreateTempFile():
    tpath = bpy.app.tempdir + "temp.json"
    if not os.path.exists(tpath):
        logger.info(tpath)
        with open(tpath, 'w', encoding='utf8') as tempfile:
            json.dump({"0":[]}, tempfile)
    return tpath

def TempSave(Num):  # write new record to temp.json file
    tpath = CreateTempFile()
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    with open(tpath, 'r+', encoding='utf8') as tempfile:   
        data = json.load(tempfile)
        data.update({str(Num):[]})
        data["0"] = [{"name": i.cname, "macro": i.macro, "icon": i.icon, "active": i.active} for i in AR_Var.Record_Coll[CheckCommand(0)].Command]
        tempfile.truncate(0)
        tempfile.seek(0)
        json.dump(data, tempfile)

def TempUpdate(): # update all records in temp.json file
    tpath = CreateTempFile()
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    with open(tpath, 'r+', encoding='utf8') as tempfile:
        tempfile.truncate(0)    
        tempfile.seek(0)
        data = {}
        for cmd in range(len(AR_Var.Record_Coll[CheckCommand(0)].Command) + 1):
            data.update({str(cmd):[{"name": i.cname, "macro": i.macro, "icon": i.icon, "active": i.active} for i in AR_Var.Record_Coll[CheckCommand(cmd)].Command]})
        json.dump(data, tempfile)

def TempUpdateCommand(Key): # update one record in temp.json file
    tpath = CreateTempFile()
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    with open(tpath, 'r+', encoding='utf8') as tempfile:
        data = json.load(tempfile)
        data[str(Key)] = [{"name": i.cname, "macro": i.macro, "icon": i.icon, "active": i.active} for i in AR_Var.Record_Coll[CheckCommand(int(Key))].Command]
        tempfile.truncate(0)
        tempfile.seek(0)
        json.dump(data, tempfile)

@persistent
def TempLoad(dummy): # load records after undo
    tpath = bpy.app.tempdir + "temp.json"
    ontempload[0] = True
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    if os.path.exists(tpath):
        with open(tpath, 'r', encoding='utf8') as tempfile:
            data = json.load(tempfile)
        command = AR_Var.Record_Coll[CheckCommand(0)].Command
        command.clear()
        keys = list(data.keys())
        for i in range(1, len(data)):
            Item = command.add()
            Item.macro = data["0"][i - 1]["macro"]
            Item.cname = data["0"][i - 1]["name"]
            Item.icon = data["0"][i - 1]["icon"]
            record = AR_Var.Record_Coll[CheckCommand(i)].Command
            record.clear()
            for j in range(len(data[keys[i]])):
                Item = record.add()
                Item.macro = data[keys[i]][j]["macro"]
                Item.cname = data[keys[i]][j]["name"]
                Item.icon = data[keys[i]][j]["icon"]
                Item.active = data[keys[i]][j]["active"]
    ontempload[0] = False

def getlastoperation(data, i=-1):
    if len(data) < 1:
        return ("", i)
    if data[i].body.startswith("bpy."):
        return (data[i].body, i)
    else:
        return getlastoperation(data, i-1)

def CheckAddCommand(data, line = 0):
    name, index = getlastoperation(data)
    macro = GetMacro(name)
    if macro is True:
        return CheckAddCommand(data[ :index], line + 1)
    else:
        return (name, macro, len(data) + line - 1)

def Add(Num, command = None, macro = None):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    if Num:
        try: #Add Macro
            if command is None:
                Recent = Get_Recent('Reports_All')
                name, macro, line = CheckAddCommand(Recent)
                bpy.data.texts.remove(bpy.data.texts['Recent Reports'])
            else:
                name = command
                if macro is None:
                    macro = GetMacro(command)
                else:
                    macro = macro
                line = -1
            notadded = False
            if macro is None or macro is True:
                notadded = name
                if macro is None and AR_Var.CreateEmpty:
                    Item = AR_Var.Record_Coll[CheckCommand(Num)].Command.add()
                    Item.macro = "<Empty>"
                    Item.cname = ""
            elif AR_Var.LastLineIndex == line and AR_Var.LastLineCmd == name:
                notadded = "<Empty>"
                Item = AR_Var.Record_Coll[CheckCommand(Num)].Command.add()
                Item.macro = "<Empty>"
                Item.cname = ""
            else:
                Item = AR_Var.Record_Coll[CheckCommand(Num)].Command.add()
                Item.macro = macro
                Item.cname = name
                if line != -1:
                    AR_Var.LastLine = macro
                    AR_Var.LastLineIndex = line
                    AR_Var.LastLineCmd = name
            if not AR_Var.hideLocal:
                UpdateRecordText(Num)
            return notadded
        except Exception as err:
            if AR_Var.CreateEmpty:
                Item = AR_Var.Record_Coll[CheckCommand(Num)].Command.add()
                Item.macro = "<Empty>"
                Item.cname = ""
            logger.error("Action Adding Failure: " + str(err))
            return True
    else: # Add Record
        Item = AR_Var.Record_Coll[CheckCommand(Num)].Command.add()
        if command == None:
            Item.cname = CheckForDublicates([cmd.cname for cmd in AR_Var.Record_Coll[CheckCommand(0)].Command], 'Untitled.001')
        else:
            Item.cname = CheckForDublicates([cmd.cname for cmd in AR_Var.Record_Coll[CheckCommand(0)].Command], command)
    AR_Var.Record_Coll[CheckCommand(Num)].Index = len(AR_Var.Record_Coll[CheckCommand(Num)].Command) - 1
    if not AR_Var.hideLocal:
        bpy.data.texts.new(Item.cname)

def UpdateRecordText(Num):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    RecName = AR_Var.Record_Coll[CheckCommand(0)].Command[Num - 1].cname
    if bpy.data.texts.find(RecName) == -1:
        bpy.data.texts.new(RecName)
    bpy.data.texts[RecName].clear()
    bpy.data.texts[RecName].write("".join([cmd.cname + "#" + cmd.macro +"\n" for cmd in AR_Var.Record_Coll[CheckCommand(Num)].Command]))

def Remove(Num): # Remove Record or Macro
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    index = AR_Var.Record_Coll[CheckCommand(Num)].Index
    if Num:
        UpdateRecordText(Num)
    else:
        txtname = AR_Var.Record_Coll[CheckCommand(Num)].Command[index].cname
        if bpy.data.texts.find(txtname) != -1:
            bpy.data.texts.remove(bpy.data.texts[txtname])
    AR_Var.Record_Coll[Num].Command.remove(index)
    if not Num:
        AR_Var.Record_Coll.remove(index + 1)
    AR_Var.Record_Coll[Num].Index = (index - 1) * (index - 1 > 0)

def Move(Num , Mode) :# Move Record or Macro
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    index1 = AR_Var.Record_Coll[CheckCommand(Num)].Index
    if Mode == 'Up' :
        index2 = AR_Var.Record_Coll[CheckCommand(Num)].Index - 1
    else :
        index2 = AR_Var.Record_Coll[CheckCommand(Num)].Index + 1
    LengthTemp = len(AR_Var.Record_Coll[CheckCommand(Num)].Command)
    if (2 <= LengthTemp) and (0 <= index1 < LengthTemp) and (0 <= index2 < LengthTemp):
        AR_Var.Record_Coll[CheckCommand(Num)].Command.move(index1, index2)
        AR_Var.Record_Coll[CheckCommand(Num)].Index = index2
        if not Num:
            AR_Var.Record_Coll.move(index1 + 1, index2 + 1)

def Select_Command(Mode): # Select the upper/lower Record
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    currentIndex = AR_Var.Record_Coll[CheckCommand(0)].Index
    listlen = len(AR_Var.Record_Coll[CheckCommand(0)].Command) - 1
    if Mode == 'Up':
        if currentIndex == 0:
            AR_Var.Record_Coll[CheckCommand(0)].Index = listlen
        else:
            AR_Var.Record_Coll[CheckCommand(0)].Index = currentIndex - 1
    else:
        if currentIndex == listlen:
            AR_Var.Record_Coll[CheckCommand(0)].Index = 0
        else:
            AR_Var.Record_Coll[CheckCommand(0)].Index = currentIndex + 1

def RespAlert(Command, index, CommandIndex):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    if CommandIndex == AR_Var.Record_Coll[CheckCommand(index + 1)].Index:
        if AR_Var.Record_Coll[CheckCommand(index + 1)].Index == 0:
            if len(AR_Var.Record_Coll[CheckCommand(index + 1)].Command) > 1:
                AR_Var.Record_Coll[CheckCommand(index + 1)].Index = 1
                bpy.context.area.tag_redraw()
        else:
            AR_Var.Record_Coll[CheckCommand(index + 1)].Index = 0
            bpy.context.area.tag_redraw()
        bpy.app.timers.register(functools.partial(Alert, Command, index, CommandIndex), first_interval= 0.01)
    else:
        Alert(Command, index, CommandIndex)
    return True

def Alert(Command, index, CommandIndex):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    Command.alert = True
    AR_Var.Record_Coll[CheckCommand(index + 1)].Index = CommandIndex
    AR_Var.Record_Coll[CheckCommand(0)].Command[index].alert = True
    bpy.app.timers.register(functools.partial(AlertTimerPlay, index), first_interval = 1)
    try:
        bpy.context.area.tag_redraw()
    except:
        redrawLocalANDMacroPanels()

def Play(Commands, index, AllLoops = None, extension = 0, offset = 0): #Execute the Macro
    if AllLoops is None:
        AllLoops = getAllLoops(Commands)
    first_event = len(Commands)
    for i, Command in enumerate(Commands):
        if Command.active:
            split = Command.cname.split(":")
            if split[0] == 'ar.event': # non-realtime events
                data = json.loads(":".join(split[1:]))
                if data['Type'] == 'Render Complet':
                    Data.Commands_RenderComplete.append((index, Commands[i + 1:], i + 1))
                    first_event = i
                    break
                elif data['Type'] == 'Render Init':
                    Data.Commands_RenderInit.append((index, Commands[i + 1:], i + 1))
                    first_event = i
                    break
                else:
                    return RespAlert(Command, index, i + offset)
    for i, Command in enumerate(Commands[:first_event]):
        if Command.active:
            split = Command.cname.split(":")
            if split[0] == 'ar.event': # realtime events
                data = json.loads(":".join(split[1:]))
                if data['Type'] == 'Timer':
                    bpy.app.timers.register(functools.partial(TimerCommads, Commands[i + 1:], index, i + 1), first_interval = data['Time'])
                    Data.ActiveTimers += 1
                    bpy.ops.ar.command_run_queued('INVOKE_DEFAULT')
                    return
                elif data['Type'] == 'Loop' :
                    loopi = getIndexInLoop(i + extension, AllLoops, 'Loop')
                    if loopi == None:
                        continue
                    else:
                        AllLoops[loopi].pop('Loop', None)
                    if data['StatementType'] == 'python':
                        try:
                            while eval(data["PyStatement"]):
                                BackLoops = Play(Commands[int(i) + 1:], index, copy.deepcopy(AllLoops), extension + 2)
                                if BackLoops == True:
                                    return True
                            else:
                                AllLoops = BackLoops
                            continue
                        except:
                            return RespAlert(Command, index, i + offset)
                    else:
                        for k in np.arange(data["Startnumber"], data["Endnumber"], data["Stepnumber"]):
                            BackLoops = Play(Commands[int(i) + 1:], index, copy.deepcopy(AllLoops), extension + 2)
                            if BackLoops == True:
                                return True
                        else:
                            AllLoops = BackLoops    
                        AllLoops[loopi].pop('End', None)
                        continue
                elif data['Type'] == 'EndLoop':
                    loopi = getIndexInLoop(i + extension, AllLoops, 'End')
                    if loopi == None:
                        continue
                    else:
                        if 'Loop' not in AllLoops[loopi]:
                            return AllLoops
                elif data['Type'] == 'Select Object':
                    obj = bpy.data.objects[data['Object']]
                    objs = bpy.context.view_layer.objects
                    if obj in [o for o in objs]:
                        objs.active = obj
                    else:
                        return RespAlert(Command, index, i + offset)
                    continue
                elif data['Type'] == 'Select Vertices':
                    obj = bpy.context.object
                    mode = bpy.context.active_object.mode
                    bpy.ops.object.mode_set(mode = 'EDIT') 
                    bpy.ops.mesh.select_mode(type="VERT")
                    bpy.ops.mesh.select_all(action = 'DESELECT')
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    mesh = bpy.context.object.data
                    objverts = mesh.vertices
                    verts = data['Verts']
                    if max(verts) < len(objverts):
                        for vert in objverts:
                            vert.select = False
                        for i in verts:
                            objverts[i].select = True
                        mesh.update()
                    else:
                        bpy.ops.object.mode_set(mode=mode)
                        return RespAlert(Command, index, i + offset)
                    bpy.ops.object.mode_set(mode=mode)
                    continue
                else:
                    return RespAlert(Command, index, i + offset)
            try:
                exec(Command.cname)
            except Exception as err:
                logger.error(err)
                return RespAlert(Command, index, i + offset)

def Clear(Num) : # Clear all Macros
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    AR_Var.Record_Coll[CheckCommand(Num)].Command.clear()
    UpdateRecordText(Num)

def Save(): #Save Buttons to Storage
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    path = AR_Var.exact_storage_path
    for savedfolder in os.listdir(path):
        folderpath = os.path.join(path, savedfolder)
        if os.path.exists(folderpath):
            for savedfile in os.listdir(folderpath):
                os.remove(os.path.join(folderpath, savedfile))
            os.rmdir(folderpath)
    for cat in AR_Var.Categories:
        panelpath = os.path.join(path, f"{ar_category.functions.get_panel_index(cat)}~" + cat.pn_name)
        if not os.path.exists(panelpath):
            os.mkdir(panelpath)
        start = cat.Instance_Start
        for cmd_i in range(start, start + cat.Instance_length):
            with open(os.path.join(panelpath, f"{cmd_i - start}~" + AR_Var.Instance_Coll[cmd_i].name + "~" + f"{AR_Var.Instance_Coll[cmd_i].icon}" + ".py"), 'w', encoding='utf8') as cmd_file:
                for cmd in AR_Var.Instance_Coll[cmd_i].command:
                    cmd_file.write(cmd.name + "#" + cmd.macro +"\n")

def Load():#Load Buttons from Storage
    logger.info('Load')
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    for cat in AR_Var.Categories:
        RegisterUnregister_Category(ar_category.functions.get_panel_index(cat), False)
    AR_Var.Categories.clear()
    AR_Var.ar_enum.clear()
    AR_Var.Instance_Coll.clear()
    AR_Var.Instance_Index = 0
    path = AR_Var.exact_storage_path
    for folder in sorted(os.listdir(path)):
        folderpath = os.path.join(path, folder)
        if os.path.isdir(folderpath):
            textfiles = os.listdir(folderpath)
            new = AR_Var.Categories.add()
            name = "".join(folder.split('~')[1:])
            new.name = name
            new.pn_name = name
            new.Instance_Start = len(AR_Var.Instance_Coll)
            new.Instance_length = len(textfiles)
            sortedtxt = [None] * len(textfiles)
            RegisterUnregister_Category(ar_category.functions.get_panel_index(new))
            for i in textfiles:
                new_e = AR_Var.ar_enum.add()
                e_index = len(AR_Var.ar_enum) - 1
                new_e.name = str(e_index)
                new_e.Index = e_index
                new_e.Value = False
            for txt in textfiles:
                sortedtxt[int(txt.split('~')[0])] = txt #get the index 
            for i in range(len(sortedtxt)):
                txt = sortedtxt[i]
                inst = AR_Var.Instance_Coll.add()
                inst.name = "".join(txt.split('~')[1:-1])
                icon = os.path.splitext(txt)[0].split('~')[-1]
                if icon.isnumeric():
                    icon = int(icon)
                else:
                    iconlist = get_icons()
                    if icon in iconlist:
                        icon = get_icons_values()[iconlist.index(icon)]
                    else:
                        icon = 101 # Icon: BLANK1
                inst.icon = icon
                CmdList = []
                with open(os.path.join(folderpath, txt), 'r', encoding='utf8') as text:
                    for line in text.readlines():
                        cmd = inst.command.add()
                        line_split = line.strip().split('#')
                        updated_cmd = update_macro(line_split[0])
                        if updated_cmd is None:
                            cmd.macro = "ERROR N/A"
                            cmd.name = "The command <%s> no longer exists in this version of Blender" %line_split[0]
                        else:
                            if updated_cmd is False:
                                cmd.name = line_split[0]
                            else:
                                cmd.name = updated_cmd
                            if len(line_split) > 1:
                                cmd.macro = "#".join(line_split[1:])
    for iconpath in os.listdir(AR_Var.IconFilePath): # Load Icons
        filepath = os.path.join(AR_Var.IconFilePath, iconpath)
        if os.path.isfile(filepath):
            load_icons(filepath, True)
    set_enum_index()()

@persistent
def LoadLocalActions(dummy):
    logger.info('Load Local Actions')
    scene = bpy.context.scene
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    AR_Var.Record_Coll.clear()
    local = json.loads(scene.ar_local)
    for ele in local:
        loc = AR_Var.Record_Coll.add()
        loc.name = ele['name']
        loc.Index = ele['Index']
        loc.Command.clear()
        for cmd in ele['Command']:
            locmd = loc.Command.add()
            locmd.cname = cmd['cname']
            locmd.macro = cmd['macro']
            locmd.active = cmd['active']
            locmd.alert = cmd['alert']
            locmd.icon = cmd['icon']
    # Check Command
    i = 0
    while i < len(local):
        ele = local[i]
        loc = AR_Var.Record_Coll[i]
        if  loc.name == ele['name'] and loc.Index == ele['Index'] and len(ele['Command']) == len(loc.Command):
            i += 1
        else:
            AR_Var.Record_Coll.remove(i)
    SaveToDataHandler(None)

def Recorder_to_Instance(panel): #Convert Record to Button
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    i = panel.Instance_Start + panel.Instance_length
    rec_commands = []
    rec_macros = []
    for Command in AR_Var.Record_Coll[CheckCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)].Command:
        rec_commands.append(Command.cname)
        rec_macros.append(Command.macro)
    data = {"name":CheckForDublicates([AR_Var.Instance_Coll[j].name for j in range(panel.Instance_Start, i)], AR_Var.Record_Coll[CheckCommand(0)].Command[AR_Var.Record_Coll[CheckCommand(0)].Index].cname),
            "command": rec_commands,
            "macro" : rec_macros,
            "icon": AR_Var.Record_Coll[CheckCommand(0)].Command[AR_Var.Record_Coll[CheckCommand(0)].Index].icon}
    Inst_Coll_Insert(i, data , AR_Var.Instance_Coll)
    panel.Instance_length += 1
    new_e = AR_Var.ar_enum.add()
    e_index = len(AR_Var.ar_enum) - 1
    new_e.name = str(e_index)
    new_e.Index = e_index
    categories = AR_Var.Categories
    for cat in categories:
        if cat.Instance_Start > panel.Instance_Start:
            cat.Instance_Start -= 1

def Instance_to_Recorder():#Convert Button to Record
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    l = []
    if multiselection_buttons[0]:
        for i in range(len(AR_Var.ar_enum)):
            if AR_Var.ar_enum[i].Value:
                l.append(i)
    else:
        l.append(AR_Var.Instance_Index)
    for Index in l:
        Item = AR_Var.Record_Coll[CheckCommand(0)].Command.add()
        Item.cname = CheckForDublicates([cmd.cname for cmd in AR_Var.Record_Coll[CheckCommand(0)].Command], AR_Var.Instance_Coll[Index].name)
        Item.icon = AR_Var.Instance_Coll[Index].icon
        for Command in AR_Var.Instance_Coll[Index].command:
            Item = AR_Var.Record_Coll[CheckCommand(len(AR_Var.Record_Coll[CheckCommand(0)].Command))].Command.add()
            if Command.macro == '':
                macro = GetMacro(Command.name)
            else:
                macro = Command.macro
            if macro == None:
                split = Command.name.split(":")
                if split[0] == "ar.event":
                    data = json.loads(":".join(split[1:]))
                    Item.macro = "Event: " + data['Type']
                else:
                    Item.macro = Command.name
            else: 
                Item.macro = macro   
            Item.cname = Command.name
        AR_Var.Record_Coll[CheckCommand(0)].Index = len(AR_Var.Record_Coll[CheckCommand(0)].Command) - 1
        UpdateRecordText(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)

def Execute_Instance(Num): #Execute a Button
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    for cmd in AR_Var.Instance_Coll[Num].command:
        try:
            exec(cmd.name)
        except:
            return True # Alert

def Rename_Instance(): #Rename a Button
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    AR_Var.Instance_Coll[AR_Var.Instance_Index].name = AR_Var.Rename

def I_Remove(): # Remove a Button
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    scene = bpy.context.scene
    l = []
    if multiselection_buttons[0]:
        for i in range(len(AR_Var.ar_enum)):
            if AR_Var.ar_enum[i].Value:
                l.append(i)
    else:
        l.append(AR_Var.Instance_Index)
    offset = 0
    for Index in l:
        if len(AR_Var.Instance_Coll) :
            Index = Index - offset
            AR_Var.Instance_Coll.remove(Index)
            AR_Var.ar_enum.remove(len(AR_Var.ar_enum) - 1)
            categories = AR_Var.Categories
            for cat in categories:
                if Index >= cat.Instance_Start and Index < cat.Instance_Start + cat.Instance_length:
                    cat.Instance_length -= 1
                    for cat2 in categories:
                        if cat2.Instance_Start > cat.Instance_Start:
                            cat2.Instance_Start -= 1
                    break
            if len(AR_Var.Instance_Coll) and len(AR_Var.Instance_Coll)-1 < Index :
                AR_Var.Instance_Index = len(AR_Var.Instance_Coll)-1
            offset += 1
    set_enum_index()()

def I_Move(Mode): # Move a Button to the upper/lower
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    scene = bpy.context.scene
    l = []
    if multiselection_buttons[0]:
        multiselection_buttons[1] = False
        for i in range(len(AR_Var.ar_enum)):
            if AR_Var.ar_enum[i].Value:
                l.append(i)
    else:
        l.append(AR_Var.Instance_Index)
    if Mode == 'Down':
        l.reverse()
    for index1 in l:
        if Mode == 'Up' :
            index2 = index1 - 1
        else :
            index2 = index1 + 1
        LengthTemp = len(AR_Var.Instance_Coll)
        if (2 <= LengthTemp) and (0 <= index1 < LengthTemp) and (0 <= index2 < LengthTemp):
            AR_Var.Instance_Coll[index1].name , AR_Var.Instance_Coll[index2].name = AR_Var.Instance_Coll[index2].name , AR_Var.Instance_Coll[index1].name
            AR_Var.Instance_Coll[index1].icon , AR_Var.Instance_Coll[index2].icon = AR_Var.Instance_Coll[index2].icon , AR_Var.Instance_Coll[index1].icon
            index1cmd = [cmd.name for cmd in AR_Var.Instance_Coll[index1].command]
            index2cmd = [cmd.name for cmd in AR_Var.Instance_Coll[index2].command]
            AR_Var.Instance_Coll[index1].command.clear()
            AR_Var.Instance_Coll[index2].command.clear()
            for cmd in index2cmd:
                new = AR_Var.Instance_Coll[index1].command.add()
                new.name = cmd
            for cmd in index1cmd:
                new = AR_Var.Instance_Coll[index2].command.add()
                new.name = cmd
            AR_Var.ar_enum[index1].Value = False
            AR_Var.ar_enum[index2].Value = True
        else:
            break
    if multiselection_buttons[0]:
        multiselection_buttons[1] = True

#Initalize Standert Button List
@persistent
def InitSavedPanel(dummy = None):
    try:
        bpy.app.timers.unregister(TimerInitSavedPanel)
    except:
        if bpy.data.filepath == '':
            return
    try:
        bpy.app.handlers.depsgraph_update_pre.remove(InitSavedPanel)
    except:
        return
    oninit[0] = True
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    if bpy.data.filepath == '':
        AR_Var.Record_Coll.clear()
    LoadLocalActions(None)
    AR_Var.Update = False
    AR_Var.Version = ''
    AR_Var.Restart = False
    if AR_Var.AutoUpdate:
        bpy.ops.ar.update_check('EXEC_DEFAULT')
    AR_Var.storage_path = AR_Var.storage_path #Update storage_path
    path = AR_Var.exact_storage_path
    if not os.path.exists(path):
        os.mkdir(path)
    if not os.path.exists(AR_Var.IconFilePath):
        os.mkdir(AR_Var.IconFilePath)
    AR_Var.Selected_Category.clear()
    Load()
    catlength[0] = len(AR_Var.Categories)
    TempSaveCats()
    TempUpdate()
    multiselection_buttons[0] = False
    oninit[0] = False

def TimerInitSavedPanel():
    InitSavedPanel()




def CreateTempCats(): #Creat temp file to save categories for ignoring Undo
    tcatpath = bpy.app.tempdir + "tempcats.json"
    if not os.path.exists(tcatpath):
        with open(tcatpath, 'x', encoding='utf8') as tempfile:
            logger.info(tcatpath)
    return tcatpath

def TempSaveCats(): # save to the create Tempfile
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    tcatpath = CreateTempCats()
    with open(tcatpath, 'r+', encoding='utf8') as tempfile:
        tempfile.truncate(0)
        tempfile.seek(0)
        cats = []
        for cat in AR_Var.Categories:
            cats.append({
                "name": cat.name,
                "pn_name": cat.pn_name,
                "pn_show": cat.pn_show,
                "Instance_Start": cat.Instance_Start,
                "Instance_length": cat.Instance_length
            })
        insts = []
        for inst in AR_Var.Instance_Coll:
            insts.append({
                "name": inst.name,
                "icon": inst.icon,
                "command": [cmd.name for cmd in inst.command],
                "macro" : [cmd.macro for cmd in inst.command]
            })
        data = {
            "Instance_Index": AR_Var.Instance_Index,
            "Categories": cats,
            "Instance_Coll": insts
        }
        json.dump(data, tempfile)

@persistent
def TempLoadCats(dummy): #Load the Created tempfile
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    tcatpath = bpy.app.tempdir + "tempcats.json"
    AR_Var.ar_enum.clear()
    reg = bpy.ops.screen.redo_last.poll()
    if reg:
        for cat in AR_Var.Categories:
            RegisterUnregister_Category(ar_category.functions.get_panel_index(cat), False)
    AR_Var.Categories.clear()
    AR_Var.Instance_Coll.clear()
    with open(tcatpath, 'r', encoding='utf8') as tempfile:
        data = json.load(tempfile)
        inst_coll = data["Instance_Coll"]
        for i in range(len(inst_coll)):
            inst = AR_Var.Instance_Coll.add()
            inst.name = inst_coll[i]["name"]
            inst.icon = inst_coll[i]["icon"]
            for y in range(len(inst_coll[i]["command"])):
                cmd = inst.command.add()
                cmd.name = inst_coll[i]["command"][y]
                cmd.maro = inst_coll[i]["macro"][y]
        index = data["Instance_Index"]
        AR_Var.Instance_Index = index
        for i in range(len(AR_Var.Instance_Coll)):
            new_e = AR_Var.ar_enum.add()
            new_e.name = str(i)
            new_e.Index = i
        if len(AR_Var.ar_enum):
            AR_Var.ar_enum[index].Value = True
        for cat in data["Categories"]:
            new = AR_Var.Categories.add()
            new.name = cat["name"]
            new.pn_name = cat["pn_name"]
            new.pn_show = cat["pn_show"]
            new.Instance_Start = cat["Instance_Start"]
            new.Instance_length = cat["Instance_length"]
            if reg:
                RegisterUnregister_Category(ar_category.functions.get_panel_index(new))



def AlertTimerPlay(recindex): #Remove alert after time passed for Recored
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    AR_Var.Record_Coll[CheckCommand(0)].Command[recindex].alert = False
    for ele in AR_Var.Record_Coll[CheckCommand(recindex + 1)].Command:
        ele.alert = False
    redrawLocalANDMacroPanels()

def AlertTimerCmd(): #Remove alert after time passed for Buttons
    Data.alert_index = None

def Inst_Coll_Insert(index, data, collection): # Insert in "Inst_Coll" Collection
    collection.add()
    for x in range(len(collection) - 1, index, -1):# go the array backwards
        collection[x].name = collection[x - 1].name
        collection[x].icon = collection[x - 1].icon
        collection[x].command.clear()
        for command in collection[x - 1].command:
            cmd = collection[x].command.add()
            cmd.name = command.name
    collection[index].name = data["name"]
    collection[index].icon = check_icon(data["icon"])
    collection[index].command.clear()
    commands = data["command"]
    macros = data["macro"]
    for i in range(len(commands)):
        cmd = collection[index].command.add()
        cmd.name = commands[i]
        cmd.macro = macros[i]

def ImportSortedZip(filepath):
    with zipfile.ZipFile(filepath, 'r') as zip_out:
        filepaths = sorted(zip_out.namelist())
        dirlist = []
        tempdirfiles = []
        dirfileslist = []
        for btn_file in filepaths:
            btn_dirc = btn_file.split("/")[0]
            if btn_dirc not in dirlist:
                if len(tempdirfiles):
                    dirfileslist.append(tempdirfiles[:])
                dirlist.append(btn_dirc)
                tempdirfiles.clear()
            tempdirfiles.append(btn_file)
        else:
            if len(tempdirfiles):
                dirfileslist.append(tempdirfiles)

        sorteddirlist = [None] * len(dirlist)
        for i in range(len(dirlist)):
            if "~" in dirlist[i]:
                new_i = int(dirlist[i].split("~")[0])
                sorteddirlist[new_i] = dirlist[i]
                dirfileslist[new_i], dirfileslist[i] = dirfileslist[i], dirfileslist[new_i]
                sortedfilelist = [None] * len(dirfileslist[new_i])
                for fil in dirfileslist[new_i]:
                    if fil.count("~") == 3 and fil.endswith('.py'):
                        sortedfilelist[int(os.path.basename(fil).split("~")[0])] = fil
                    else:
                        return (None, None)
                dirfileslist[new_i] = sortedfilelist
            else:
                return (None, None)
        return (dirfileslist, sorteddirlist)

def CreateNewProp(prop):
    name = "Edit_Command_%s" % prop.identifier
    exec("bpy.types.Scene.%s = prop" % name)
    return "bpy.context.scene.%s" % name

def DeleteProps(address):
    exec("del %s" % address)


def TimerCommads(Commands, index, offset):
    execution_queue.put(functools.partial(Play, Commands, index, offset=offset))

def getAllLoops(Commands):
    datal = []
    for i, Command in enumerate(Commands):
        if Command.active:
            split = Command.cname.split(":")
            if split[0] == 'ar.event':
                data = json.loads(":".join(split[1:]))
                if data['Type'] == 'Loop':
                    datal.append({'Loop': i})
                elif data['Type'] == 'EndLoop':
                    index = CheckForLoopEnd(datal)
                    if index != -1:
                        datal[index]['End'] = i
    return [obj for obj in datal if 'End' in obj]

def CheckForLoopEnd(data):
    if len(data) < 1:
        return -1
    if 'End' in data[-1]:
        return CheckForLoopEnd(data[:-1])
    else:
        return len(data) - 1 

def getIndexInLoop(i, AllLoops, identifier):
    for li in range(len(AllLoops)):
        if identifier in AllLoops[li] and i == AllLoops[li][identifier]:
            return li

@persistent
def runRenderComplete(dummy):
    for index, Commands, offset in Data.Commands_RenderComplete:
        Play(Commands, index, offset=offset)
    Data.Commands_RenderComplete.clear()

@persistent
def runRenderInit(dummy):
    for index, Commands, offset in Data.Commands_RenderInit:
        Play(Commands, index, offset=offset)
    Data.Commands_RenderInit.clear()

@persistent
def SaveToDataHandler(dummy):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    local = []
    for ele in AR_Var.Record_Coll:
        loc = {}
        loc['name'] = ele.name
        loc['Index'] = ele.Index
        loc['Command'] = []
        for cmd in ele.Command:
            locmd = {}
            locmd['cname'] = cmd.cname
            locmd['macro'] = cmd.macro
            locmd['active'] = cmd.active
            locmd['alert'] = cmd.alert
            locmd['icon'] = cmd.icon
            loc['Command'].append(locmd)
        local.append(loc)
    bpy.context.scene.ar_local = json.dumps(local)

def getCatInAreas(cat, data):
    l = []
    for i in data['Area'].items():
        if cat == i[1]:
            l.append(i[0])
    return l

def redrawLocalANDMacroPanels():
    for i in classespanel:
        if i.__name__.startswith("AR_PT_Local_") or i.__name__.startswith("AR_PT_MacroEditer_"):
            bpy.utils.unregister_class(i)
            bpy.utils.register_class(i)


def LoadActionFromTexteditor(texts, replace = True):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    if replace:
        AR_Var.Record_Coll.clear()
    for text in texts:
        if bpy.data.texts.find(text) == -1:
            continue
        text = bpy.data.texts[text]
        lines = [line.body for line in text.lines]
        Add(0, text.name)
        for line in lines:
            if line != '':
                AR_Var = bpy.context.preferences.addons[__package__].preferences
                splitlines = line.split("#")
                Add(len(AR_Var.Record_Coll[0].Command), "#".join(splitlines[:-1]), splitlines[-1])

def showCategory(name, context):
    AR_Var = context.preferences.addons[__package__].preferences
    if AR_Var.ShowAllCategories:
        return True
    res = CatVisibility["Area"].get(context.space_data.type, None)
    if res is None:
        CatVisibility["Area"][context.space_data.type] = []
    if name in CatVisibility["Area"][context.space_data.type]:
        return True
    if context.space_data.type == "VIEW_3D":
        res = CatVisibility["Mode"].get(context.mode, None)
        if res is None:
            CatVisibility["Mode"][context.mode] = []
        if name in CatVisibility["Mode"][context.mode]:    
            return True
    l = []
    for ele in CatVisibility["Area"].values():
        for item in ele:
            l.append(item)
    for ele in CatVisibility["Mode"].values():
        for item in ele:
            l.append(item)
    return not (name in l)

def getCollectionBorderOfButtonIndex(index, AR_Var):
    for cat in AR_Var.Categories:
        if index < cat.Instance_Start + cat.Instance_length and index >= cat.Instance_Start:
            return (cat.Instance_Start, cat.Instance_Start + cat.Instance_length - 1)

def TextToLines(text, font_text, limit, endcharacter = " ,"):
    if text == '' or not font_text.use_dynamic_text:
        return [text]
    characters_width = font_text.getWidthOfText(text)
    possible_breaks = split_and_keep(endcharacter, text)
    lines = [""]
    start = 0
    for psb in possible_breaks:
        line_length = len(lines[-1])
        total_line_length = start + line_length
        total_length = total_line_length + len(psb)
        width = sum(characters_width[start : total_length])
        if width <= limit:
            lines[-1] += psb
        else:
            if sum(characters_width[total_line_length : total_length]) > limit:
                start += line_length
                while psb != "":
                    i = clamp(int(limit / width * len(psb)), 0, len(psb))
                    if len(psb) != i:
                        if sum(characters_width[start : start + i]) <= limit:
                            while sum(characters_width[start : start + i]) <= limit:
                                i += 1
                            i -= 1
                        else:
                            while sum(characters_width[start : start + i]) >= limit:
                                i -= 1
                            i += 1
                    lines.append(psb[:i])
                    psb = psb[i:]
                    start += i
                    width = sum(characters_width[start : total_length])
            else:
                lines.append(psb)
                start += line_length + len(psb)
    if(lines[0] == ""):
        lines.pop(0)
    return lines

def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)

def split_and_keep(sep, text):
    p=chr(ord(max(text))+1)
    for s in sep:
        text = text.replace(s, s+p)
    return text.split(p)

def getFontPath():
    if bpy.context.preferences.view.font_path_ui == '':
        dirc = "\\".join(bpy.app.binary_path_python.split("\\")[:-3])
        return os.path.join(dirc, "datafiles", "fonts", "droidsans.ttf")
    else:
        return bpy.context.preferences.view.font_path_ui

def update_macro(macro: str):
    if macro.startswith("bpy.ops."):
        command, values = macro.split("(", 1)
        values = extract_properties(values[:-1])
        for i in range(len(values)):
            values[i] = values[i].strip().split("=")
        try:
            props = eval(command + ".get_rna_type().properties[1:]")
        except:
            return None
        inputs = []
        for prop in props:
            for value in values:
                if value[0] == prop.identifier:
                    inputs.append(value[0] + "=" + value[1])
                    values.remove(value)
                    break
        return command + "(" + ", ".join(inputs) + ")"
    else:
        return False

def extract_properties(properties :str):
    properties = properties.split(",")
    new_props = []
    prop_str = ''
    for prop in properties:
        prop = prop.split('=')
        if prop[0].strip().isidentifier() and len(prop) > 1:
            new_props.append(prop_str)
            prop_str = ''
            prop_str += "=".join(prop)
        else:
            prop_str += "," + prop[0]
    new_props.append(prop_str)
    return new_props[1:]
# endregion

# region Panels
def panelFactory(spaceType): #Create Panels for every spacetype with UI

    class AR_PT_Local(Panel):
        bl_space_type = spaceType
        bl_region_type = 'UI'
        bl_category = 'Action Recorder'
        bl_label = 'Local Actions'
        bl_idname = "AR_PT_Local_%s" % spaceType
        bl_order = 0

        '''def draw_header(self, context):
            self.layout.label(text = '', icon = 'REC')'''

        def draw(self, context):
            AR_Var = context.preferences.addons[__package__].preferences
            scene = bpy.context.scene
            layout = self.layout
            if AR_Var.AutoUpdate and AR_Var.Update:
                box = layout.box()
                box.label(text= "A new Version is available (" + AR_Var.Version + ")")
                box.operator(AR_OT_update.bl_idname, text= "Update")
            box = layout.box()
            box_row = box.row()
            col = box_row.column()
            col.template_list('AR_UL_Selector' , '' , AR_Var.Record_Coll[CheckCommand(0)] , 'Command' , AR_Var.Record_Coll[CheckCommand(0)] , 'Index', rows=4, sort_lock= True)
            col = box_row.column()
            col2 = col.column(align= True)
            col2.operator(AR_OT_Record_Add.bl_idname , text='' , icon='ADD' )
            col2.operator(AR_OT_Record_Remove.bl_idname , text='' , icon='REMOVE' )
            col2 = col.column(align= True)
            col2.operator(AR_OT_Record_MoveUp.bl_idname , text='' , icon='TRIA_UP' )
            col2.operator(AR_OT_Record_MoveDown.bl_idname , text='' , icon='TRIA_DOWN' )
    AR_PT_Local.__name__ = "AR_PT_Local_%s" % spaceType
    classespanel.append(AR_PT_Local)

    class AR_PT_MacroEditer(Panel):
        bl_space_type = spaceType
        bl_region_type = 'UI'
        bl_category = 'Action Recorder'
        bl_label = 'Macro Editor'
        bl_idname = "AR_PT_MacroEditer_%s" % spaceType
        bl_order = 1

        def draw(self, context):
            AR_Var = context.preferences.addons[__package__].preferences
            scene = context.scene
            layout = self.layout
            box = layout.box()
            box_row = box.row()
            col = box_row.column()
            col.template_list('AR_UL_Command' , '' , AR_Var.Record_Coll[CheckCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)] , 'Command' , AR_Var.Record_Coll[CheckCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)] , 'Index', rows=4)
            col = box_row.column()
            if not AR_preferences.Record :
                col2 = col.column(align= True)
                col2.operator(AR_OT_Command_Add.bl_idname , text='' , icon='ADD' )
                col2.operator(AR_OT_AddEvent.bl_idname, text= '', icon= 'MODIFIER').Num = -1
                col2.operator(AR_OT_Command_Remove.bl_idname , text='' , icon='REMOVE' )
                col2 = col.column(align= True)
                col2.operator(AR_OT_Command_MoveUp.bl_idname , text='' , icon='TRIA_UP' )
                col2.operator(AR_OT_Command_MoveDown.bl_idname , text='' , icon='TRIA_DOWN' )
            #----------------------------------------
            row = layout.row()
            if AR_preferences.Record :
                row.scale_y = 2
                row.operator(AR_OT_Record_Stop.bl_idname , text='Stop')
            else :
                row2 = row.row(align= True)
                row2.operator(AR_OT_Record_Start.bl_idname , text='Record' , icon='REC' )
                row2.operator(AR_OT_Command_Clear.bl_idname , text= 'Clear')
                col = layout.column()
                row = col.row()
                row.scale_y = 2
                row.operator(AR_OT_Record_Play.bl_idname , text='Play' )
                col.operator(AR_OT_RecordToButton.bl_idname , text='Local to Global' )
                row = col.row(align= True)
                row.enabled = len(AR_Var.Record_Coll[CheckCommand(0)].Command) > 0
                row.prop(AR_Var, 'RecToBtn_Mode', expand= True)
    AR_PT_MacroEditer.__name__ = "AR_PT_MacroEditer_%s" % spaceType
    classespanel.append(AR_PT_MacroEditer)

    class AR_PT_Global(Panel):
        bl_space_type = spaceType
        bl_region_type = 'UI'
        bl_category = 'Action Recorder'
        bl_label = 'Global Actions'
        bl_idname = "AR_PT_Global_%s" % spaceType
        bl_order = 2

        def draw_header(self, context):
            AR_Var = context.preferences.addons[__package__].preferences
            layout = self.layout
            row = layout.row(align= True)
            row.prop(AR_Var, 'HideMenu', icon= 'COLLAPSEMENU', text= "", emboss= True)

        def draw(self, context):
            AR_Var = context.preferences.addons[__package__].preferences
            scene = bpy.context.scene
            layout = self.layout
            if not AR_Var.HideMenu:
                col = layout.column()
                row = col.row()
                row.scale_y = 2
                row.operator(AR_OT_ButtonToRecord.bl_idname, text='Global to Local' )
                row = col.row(align= True)
                row.enabled =  len(AR_Var.Instance_Coll) > 0
                row.prop(AR_Var, 'BtnToRec_Mode', expand= True)
                row = layout.row().split(factor= 0.4)
                row.label(text= 'Buttons')
                row2 = row.row(align= True)
                row2.operator(AR_OT_Button_MoveUp.bl_idname , text='' , icon='TRIA_UP' )
                row2.operator(AR_OT_Button_MoveDown.bl_idname , text='' , icon='TRIA_DOWN' )
                row2.operator(AR_OT_Category_MoveButton.bl_idname, text= '', icon= 'PRESET')
                row2.operator(AR_OT_Button_Remove.bl_idname, text='' , icon='TRASH' )
                row = layout.row()
                row2 = row.split(factor= 0.7)
                col = row2.column()
                col.enabled = len(AR_Var.Instance_Coll) > 0 and not (multiselection_buttons[0] and len(InstanceLastselected) > 1)
                col.prop(AR_Var , 'Rename' , text='')
                row2.operator(AR_OT_Button_Rename.bl_idname , text='ReName')
    AR_PT_Global.__name__ = "AR_PT_Global_%s" % spaceType
    classespanel.append(AR_PT_Global)

    class AR_PT_Help(Panel):
        bl_space_type = spaceType
        bl_region_type = 'UI'
        bl_category = 'Action Recorder'
        bl_label = 'Help'
        bl_idname = "AR_PT_Help_%s" % spaceType
        bl_options = {'DEFAULT_CLOSED'}
        bl_order = 3

        def draw_header(self, context):
            layout = self.layout
            layout.label(icon= 'INFO')

        def draw(self, context):
            layout = self.layout
            AR_Var = context.preferences.addons[__package__].preferences
            layout.operator(AR_OT_Help_OpenURL.bl_idname, text= "Manual", icon= 'ASSET_MANAGER').url = config["Manual_URL"]
            layout.operator(AR_OT_Help_OpenURL.bl_idname, text= "Hint", icon= 'HELP').url = config["Hint_URL"]
            layout.operator(AR_OT_Help_OpenURL.bl_idname, text= "Bug Report", icon= 'URL').url = config["BugReport_URL"]
            row = layout.row()
            if AR_Var.Update:
                row.operator(AR_OT_update.bl_idname, text= "Update")
                row.operator(AR_OT_ReleaseNotes.bl_idname, text= "Release Notes")
            else:
                row.operator(AR_OT_update_check.bl_idname, text= "Check For Updates")
                if AR_Var.Restart:
                    row.operator(AR_OT_restart.bl_idname, text= "Restart to Finsih")
            if AR_Var.Version != '':
                if AR_Var.Update:
                    layout.label(text= "new Version available (" + AR_Var.Version + ")")
                else:
                    layout.label(text= "latest Vesion installed (" + AR_Var.Version + ")")
    AR_PT_Help.__name__ = "AR_PT_Help_%s" % spaceType
    classespanel.append(AR_PT_Help)

    class AR_PT_Advanced(Panel):
        bl_space_type = spaceType
        bl_region_type = 'UI'
        bl_category = 'Action Recorder'
        bl_label = 'Advanced'
        bl_idname = "AR_PT_Advanced_%s" % spaceType
        #bl_parent_id = AR_PT_Global.bl_idname
        bl_options = {'DEFAULT_CLOSED'}
        bl_order = 4

        def draw(self, context):
            AR_Var = context.preferences.addons[__package__].preferences
            layout = self.layout
            col = layout.column()
            col.label(text= "Category", icon= 'GROUP')
            row = col.row(align= True)
            selectedCat_index = GetCatRadioIndex(AR_Var.Selected_Category)
            row.label(text= '')
            row2 = row.row(align= True)
            row2.scale_x = 1.5
            row2.operator(AR_OT_Category_MoveUp.bl_idname, text= '',icon= 'TRIA_UP').Index = selectedCat_index
            row2.operator(AR_OT_Category_MoveDown.bl_idname, text= '',icon= 'TRIA_DOWN').Index = selectedCat_index
            row2.operator(AR_OT_category_add.bl_idname, text= '', icon= 'ADD').edit = False
            row2.operator(AR_OT_category_delete.bl_idname, text= '', icon= 'TRASH')
            row.label(text= '')
            row = col.row(align= False)
            row.operator(AR_OT_category_edit.bl_idname, text= 'Edit')
            row.prop(AR_Var, 'ShowAllCategories', text= "", icon= 'RESTRICT_VIEW_OFF' if AR_Var.ShowAllCategories else 'RESTRICT_VIEW_ON')
            col.label(text= "Data Management", icon= 'FILE_FOLDER')
            col.operator(AR_OT_Import.bl_idname, text= 'Import')
            col.operator(AR_OT_Export.bl_idname, text= 'Export')
            col.label(text= "Storage File Settings", icon= "FOLDER_REDIRECT")
            row = col.row()
            row.label(text= "AutoSave")
            row.prop(AR_Var, 'Autosave', toggle= True, text= "On" if AR_Var.Autosave else "Off")
            col.operator(AR_OT_Save.bl_idname , text='Save to File' )
            col.operator(AR_OT_Load.bl_idname , text='Load from File' )
            row2 = col.row(align= True)
            row2.operator(AR_OT_Record_LoadLoaclActions.bl_idname, text='Load Local Actions')
            row2.prop(AR_Var, 'hideLocal', text= "", toggle= True, icon= "HIDE_ON" if AR_Var.hideLocal else "HIDE_OFF")
            col.label(text= "Local Settings")
            col.prop(AR_Var, 'CreateEmpty', text= "Create Empty Macro on Error")
    AR_PT_Advanced.__name__ = "AR_PT_Advanced_%s" % spaceType
    classespanel.append(AR_PT_Advanced)

# endregion
        
# region Opertators







class AR_OT_Category_MoveUp(Operator):
    bl_idname = "ar.category_move_up"
    bl_label = "Move Up"
    bl_description = "Move the Category up"

    Index : IntProperty()

    def invoke(self, context, event):
        AR_Var = context.preferences.addons[__package__].preferences
        i = self.Index
        categories = AR_Var.Categories
        y = i - 1
        if y >= 0:
            cat2 = categories[y]
            while not showCategory(cat2.pn_name, context):
                y -= 1
                if y < 0:
                    return {"CANCELLED"}
                cat2 = categories[y]
            cat1 = categories[i]
            cat1.name, cat2.name = cat2.name, cat1.name
            cat1.pn_name, cat2.pn_name = cat2.pn_name, cat1.pn_name
            cat1.pn_show, cat2.pn_show = cat2.pn_show, cat1.pn_show
            cat1.pn_selected, cat2.pn_selected = cat2.pn_selected, cat1.pn_selected
            cat1.Instance_Start, cat2.Instance_Start = cat2.Instance_Start, cat1.Instance_Start
            cat1.Instance_length, cat2.Instance_length = cat2.Instance_length, cat1.Instance_length
            AR_Var.Selected_Category[y].selected = True
        bpy.context.area.tag_redraw()
        TempSaveCats()
        if AR_Var.Autosave:
            Save()
        return {"FINISHED"}
classes.append(AR_OT_Category_MoveUp)

class AR_OT_Category_MoveDown(Operator):
    bl_idname = "ar.category_move_down"
    bl_label = "Move Down"
    bl_description = "Move the Category down"

    Index : IntProperty()

    def invoke(self, context, event):
        AR_Var = context.preferences.addons[__package__].preferences
        i = self.Index
        categories = AR_Var.Categories
        y = i + 1 
        if y < len(categories):
            cat2 = categories[y]
            while not showCategory(cat2.pn_name, context):
                y += 1
                if y >= len(categories):
                    return {"CANCELLED"}
                cat2 = categories[y]
            cat1 = categories[i]
            cat1.name, cat2.name = cat2.name, cat1.name
            cat1.pn_name, cat2.pn_name = cat2.pn_name, cat1.pn_name
            cat1.pn_show, cat2.pn_show = cat2.pn_show, cat1.pn_show
            cat1.pn_selected, cat2.pn_selected = cat2.pn_selected, cat1.pn_selected
            cat1.Instance_Start, cat2.Instance_Start = cat2.Instance_Start, cat1.Instance_Start
            cat1.Instance_length, cat2.Instance_length = cat2.Instance_length, cat1.Instance_length
            AR_Var.Selected_Category[y].selected = True
        bpy.context.area.tag_redraw()
        TempSaveCats()
        if AR_Var.Autosave:
            Save()
        return {"FINISHED"}
classes.append(AR_OT_Category_MoveDown)

class AR_OT_RecordToButton(Operator):
    bl_idname = "ar.record_record_to_button"
    bl_label = "Action to Global"
    bl_description = "Add the selected Action to a Category"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Record_Coll[CheckCommand(0)].Command)

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        categories = AR_Var.Categories
        if len(categories):
            for cat in categories:
                if cat.pn_selected:
                    Recorder_to_Instance(cat)
                    break
            if AR_Var.RecToBtn_Mode == 'move':
                Remove(0)
                TempUpdate()
            TempSaveCats()
            if AR_Var.Autosave:
                Save()
            bpy.context.area.tag_redraw()
            return {"FINISHED"}
        else:
            return {'CANCELLED'}

    def draw(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        categories = AR_Var.Categories
        layout = self.layout
        if len(categories):
            for cat in categories:
                layout.prop(cat, 'pn_selected', text= cat.pn_name)
        else:
            box = layout.box()
            col = box.column()
            col.scale_y = 0.9
            col.label(text= 'Please Add a Category first', icon= 'INFO')
            col.label(text= 'To do that, go to the Advanced menu', icon= 'BLANK1')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
classes.append(AR_OT_RecordToButton)

class AR_OT_Import(Operator, ImportHelper):
    bl_idname = "ar.data_import"
    bl_label = "Import"
    bl_description = "Import the Action file into the storage"

    filter_glob: StringProperty( default='*.zip', options={'HIDDEN'} )

    Category : StringProperty(default= "Imports")
    AddNewCategory : BoolProperty(default= False)
    Mode : EnumProperty(name= 'Mode', items= [("add","Add",""),("overwrite", "Overwrite", "")])

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        scene = context.scene
        ar_categories = AR_Var.Categories
        if self.filepath.endswith(".zip"):
            if self.AddNewCategory:
                dirfileslist, sorteddirlist = ImportSortedZip(self.filepath)
                with zipfile.ZipFile(self.filepath, 'r') as zip_out:
                    mycat = ar_categories.add()
                    name = CheckForDublicates([n.pn_name for n in ar_categories], self.Category)
                    mycat.name = name
                    mycat.pn_name = name
                    mycat.Instance_Start = len(AR_Var.Instance_Coll)
                    RegisterUnregister_Category(ar_category.functions.get_panel_index(mycat))
                    for dirs in dirfileslist:
                        for btn_file in dirs:
                            name_icon = os.path.splitext(os.path.basename(btn_file))[0]
                            name = "".join(name_icon.split("~")[1:-1])
                            inst = AR_Var.Instance_Coll.add()
                            inst.name = CheckForDublicates([AR_Var.Instance_Coll[i].name for i in range(mycat.Instance_Start, mycat.Instance_Start + mycat.Instance_length)], name)
                            inst.icon = check_icon(name_icon.split("~")[-1])
                            for line in zip_out.read(btn_file).decode("utf-8").splitlines():
                                cmd = inst.command.add()
                                cmd.name = line
                            new_e = AR_Var.ar_enum.add()
                            e_index = len(AR_Var.ar_enum) - 1
                            new_e.name = str(e_index)
                            new_e.Index = e_index
                            mycat.Instance_length += 1
            else:
                if not len(AR_Var.Importsettings):
                    if bpy.ops.ar.data_import_options('EXEC_DEFAULT', filepath= self.filepath, fromoperator= True) == {'CANCELLED'}:
                        self.report({'ERROR'}, "The selected file is not compatible")
                        return {'CANCELLED'}
                for icat in AR_Var.Importsettings:
                    Index = -1
                    mycat = None
                    if icat.enum == 'append':
                        Index = AR_Var.Categories.find(icat.cat_name)
                    if Index == -1:
                        mycat = ar_categories.add()
                        name = icat.cat_name
                        name = CheckForDublicates([n.pn_name for n in ar_categories], name)
                        mycat.name = name
                        mycat.pn_name = name
                        mycat.Instance_Start = len(AR_Var.Instance_Coll)
                        RegisterUnregister_Category(ar_category.functions.get_panel_index(mycat))
                    else:
                        mycat = ar_categories[Index]
                        for btn in icat.Buttons:
                            if btn.enum == 'overwrite':
                                for i in range(mycat.Instance_Start, mycat.Instance_Start + mycat.Instance_length):
                                    inst = AR_Var.Instance_Coll[i]
                                    if btn.btn_name == inst.name:
                                        inst.name = btn.btn_name
                                        inst.icon = check_icon(btn.icon)
                                        inst.command.clear()
                                        for cmd in btn.command.splitlines():
                                            new = inst.command.add()
                                            new.name = cmd
                                        break
                                else:
                                    btn.enum = 'add'

                    for btn in icat.Buttons:
                        if btn.enum == 'overwrite':
                            continue
                        inserti = mycat.Instance_Start + mycat.Instance_length
                        name = btn.btn_name
                        icon = btn.icon
                        data = {"name": CheckForDublicates([AR_Var.Instance_Coll[i].name for i in range(mycat.Instance_Start, mycat.Instance_Start + mycat.Instance_length)], name),
                                "command": btn.command.splitlines(),
                                "icon": icon}
                        Inst_Coll_Insert(inserti, data, AR_Var.Instance_Coll)
                        new_e = AR_Var.ar_enum.add()
                        e_index = len(AR_Var.ar_enum) - 1
                        new_e.name = str(e_index)
                        new_e.Index = e_index
                        mycat.Instance_length += 1
                        if Index != -1:
                            for cat in ar_categories[Index + 1:] :
                                cat.Instance_Start += 1
            set_enum_index()()
            if AR_Var.Autosave:
                Save()
        else:
            self.report({'ERROR'}, "{ " + self.filepath + " } Select a .zip file")
        AR_Var = context.preferences.addons[__package__].preferences
        AR_Var.Importsettings.clear()
        TempSaveCats()
        return {"FINISHED"}
    
    def draw(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        layout = self.layout
        layout.prop(self, 'AddNewCategory', text= "Append to new Category")
        if self.AddNewCategory:
            layout.prop(self, 'Category', text= "Name")
        else:
            layout.operator(AR_OT_ImportLoadSettings.bl_idname, text= "Load Importsettings").filepath = self.filepath
            for cat in AR_Var.Importsettings:
                box = layout.box()
                col = box.column()
                row = col.row()
                if cat.show:
                    row.prop(cat, 'show', icon="TRIA_DOWN", text= "", emboss= False)
                else:
                    row.prop(cat, 'show', icon="TRIA_RIGHT", text= "", emboss= False)
                row.label(text= cat.cat_name)
                row.prop(cat, 'enum', text= "")
                if cat.show:
                    col = box.column()
                    for btn in cat.Buttons:
                        row = col.row()
                        row.label(text= btn.btn_name)
                        if cat.enum == 'append':
                            row.prop(btn, 'enum', text= "")
        
    def cancel(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        AR_Var.Importsettings.clear()
classes.append(AR_OT_Import)

class AR_OT_ImportLoadSettings(Operator):
    bl_idname = "ar.data_import_options"
    bl_label = "Load Importsettings"
    bl_description = "Load the select the file to change the importsettings"

    filepath : StringProperty()
    fromoperator : BoolProperty()

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        if os.path.exists(self.filepath) and self.filepath.endswith(".zip"):
            dirfileslist, sorteddirlist = ImportSortedZip(self.filepath)
            if dirfileslist is None:
                if not self.fromoperator:
                    self.report({'ERROR'}, "The selected file is not compatible")
                self.fromoperator = False
                return {'CANCELLED'}
            with zipfile.ZipFile(self.filepath, 'r') as zip_out:
                AR_Var.Importsettings.clear()
                for i in range(len(sorteddirlist)):
                    cat = AR_Var.Importsettings.add()
                    cat.cat_name = "".join(sorteddirlist[i].split("~")[1:])
                    for dir_file in dirfileslist[i]:
                        btn = cat.Buttons.add()
                        name_icon = os.path.splitext(os.path.basename(dir_file))[0]
                        btn.btn_name = "".join(name_icon.split("~")[1:-1])
                        btn.icon = name_icon.split("~")[-1]
                        btn.command = zip_out.read(dir_file).decode("utf-8")
                return {"FINISHED"}
        else:
            self.report({'ERROR'}, "You need to select a .zip file")
            return {'CANCELLED'}
classes.append(AR_OT_ImportLoadSettings)

class AR_OT_Export(Operator, ExportHelper):
    bl_idname = "ar.data_export"
    bl_label = "Export"
    bl_description = "Export the Action file as a ZIP"

    filter_glob: StringProperty( default='*.zip', options={'HIDDEN'} )
    filename_ext = ".zip"
    filepath : StringProperty (name = "File Path", maxlen = 1024, default = "ActionRecorderButtons")
    allcats : BoolProperty(name= "All", description= "Export every Category")

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Instance_Coll)

    def execute(self, context):
        scene = context.scene
        temppath = bpy.app.tempdir + "AR_Zip"
        if not os.path.exists(temppath):
            os.mkdir(temppath)
        with zipfile.ZipFile(self.filepath, 'w') as zip_it:
            catindex = 0
            written = False
            for cat in scene.ar_filecategories:
                folderpath = os.path.join(temppath, f"{catindex}~" + cat.pn_name)
                if not os.path.exists(folderpath):
                    os.mkdir(folderpath)
                if cat.pn_selected or self.allcats:
                    written = True
                    for i in range(cat.FileDisp_Start, cat.FileDisp_Start + cat.FileDisp_length):
                        zip_path = os.path.join(folderpath, f"{i}~" + AR_preferences.FileDisp_Name[i] + ".py")
                        with open(zip_path, 'w', encoding='utf8') as recfile:
                            for cmd in AR_preferences.FileDisp_Command[i]:
                                recfile.write(cmd + '\n')
                        zip_it.write(zip_path, os.path.join(f"{catindex}~" + cat.pn_name, f"{i - cat.FileDisp_Start}~"+ AR_preferences.FileDisp_Name[i] + f"~{AR_preferences.FileDisp_Icon[i]}" + ".py"))
                        os.remove(zip_path)
                else:
                    index = 0
                    for i in range(cat.FileDisp_Start, cat.FileDisp_Start + cat.FileDisp_length):
                        if scene.ar_filedisp[i].Index:
                            written = True
                            zip_path = os.path.join(folderpath, f"{index}~" + AR_preferences.FileDisp_Name[i] + ".py")
                            with open(zip_path, 'w', encoding='utf8') as recfile:
                                for cmd in AR_preferences.FileDisp_Command[i]:
                                    recfile.write(cmd + '\n')
                            zip_it.write(zip_path, os.path.join(f"{catindex}~" + cat.pn_name, f"{index}~" + AR_preferences.FileDisp_Name[i] + f"~{AR_preferences.FileDisp_Icon[i]}" + ".py"))
                            os.remove(zip_path)
                            index += 1
                if written:
                    catindex += 1
                    written = False
                os.rmdir(folderpath)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        box = layout.box()
        box.prop(self, 'allcats', text= "All")
        for cat in scene.ar_filecategories:
            box = layout.box()
            col = box.column()
            row = col.row()
            if cat.pn_show:
                row.prop(cat, 'pn_show', icon="TRIA_DOWN", text= "", emboss= False)
            else:
                row.prop(cat, 'pn_show', icon="TRIA_RIGHT", text= "", emboss= False)
            row.label(text= cat.pn_name)
            row.prop(cat, 'pn_selected', text= "")
            if cat.pn_show:
                col = box.column(align= False)
                if self.allcats or cat.pn_selected:
                    for i in range(cat.FileDisp_Start, cat.FileDisp_Start + cat.FileDisp_length):
                        col.label(text= AR_preferences.FileDisp_Name[i], icon= 'CHECKBOX_HLT')
                else:
                    for i in range(cat.FileDisp_Start, cat.FileDisp_Start + cat.FileDisp_length):
                        col.prop(scene.ar_filedisp[i], 'Index' , text= AR_preferences.FileDisp_Name[i])
    
    def invoke(self, context, event):
        AR_Var = context.preferences.addons[__package__].preferences
        scene = context.scene
        scene.ar_filecategories.clear()
        for cat in AR_Var.Categories:
            new = scene.ar_filecategories.add()
            new.name = cat.name
            new.pn_name = cat.pn_name
            new.FileDisp_Start = cat.Instance_Start
            new.FileDisp_length = cat.Instance_length
        AR_preferences.FileDisp_Name.clear()
        AR_preferences.FileDisp_Command.clear()
        AR_preferences.FileDisp_Icon.clear()
        for inst in AR_Var.Instance_Coll:
            AR_preferences.FileDisp_Name.append(inst.name)
            AR_preferences.FileDisp_Icon.append(inst.icon)
            AR_preferences.FileDisp_Command.append([cmd.name for cmd in inst.command])
        scene.ar_filedisp.clear()
        for i in range(len(AR_Var.ar_enum)):
            scene.ar_filedisp.add()
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
classes.append(AR_OT_Export)

class AR_OT_Record_Add(Operator):
    bl_idname = "ar.record_add"
    bl_label = "Add"
    bl_description = "Add a New Action"

    def execute(self, context):
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        scene = context.scene
        Add(0)
        TempSave(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)
        bpy.context.area.tag_redraw()
        SaveToDataHandler(None)
        return {"FINISHED"}
classes.append(AR_OT_Record_Add)

class AR_OT_Record_Remove(Operator):
    bl_idname = "ar.record_remove"
    bl_label = "Remove"
    bl_description = "Remove the selected Action"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Record_Coll[CheckCommand(0)].Command)

    def execute(self, context):
        scene = context.scene
        Remove(0)
        TempUpdate()
        bpy.context.area.tag_redraw()
        SaveToDataHandler(None)
        return {"FINISHED"}
classes.append(AR_OT_Record_Remove)

class AR_OT_Record_MoveUp(Operator):
    bl_idname = "ar.record_move_up"
    bl_label = "Move Up"
    bl_description = "Move the selected Action Up"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Record_Coll[CheckCommand(0)].Command)

    def execute(self, context):
        scene = context.scene
        Move(0 , 'Up')
        TempUpdate()
        bpy.context.area.tag_redraw()
        SaveToDataHandler(None)
        return {"FINISHED"}
classes.append(AR_OT_Record_MoveUp)

class AR_OT_Record_MoveDown(Operator):
    bl_idname = "ar.record_move_down"
    bl_label = "Move Down"
    bl_description = "Move the selected Action Down"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Record_Coll[CheckCommand(0)].Command)
        
    def execute(self, context):
        scene = context.scene
        Move(0 , 'Down')
        TempUpdate()
        bpy.context.area.tag_redraw()
        SaveToDataHandler(None)
        return {"FINISHED"}
classes.append(AR_OT_Record_MoveDown)

class AR_LLA_TextProps(PropertyGroup):
    name : StringProperty()
    apply : BoolProperty(default= False)
classes.append(AR_LLA_TextProps)

class AR_OT_Record_LoadLoaclActions(Operator):
    bl_idname = "ar.record_loadlocalactions"
    bl_label = "Load Loacl Actions"
    bl_description = "Load the Local Action from the last Save"

    Source : EnumProperty(name= 'Source', description= "Choose the source from where to load", items= [('scene', 'Scene', ''), ('text', 'Texteditor', '')])
    Texts : CollectionProperty(type= AR_LLA_TextProps)

    def execute(self, context):
        if self.Source == 'scene':
            LoadLocalActions(None)
        else:
            texts = []
            for text in self.Texts:
                if text.apply:
                    texts.append(text.name)
            LoadActionFromTexteditor(texts)
        TempUpdate()
        bpy.context.area.tag_redraw()
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'Source', expand= True)
        if self.Source == 'text':
            box = layout.box()
            texts = [txt.name for txt in bpy.data.texts]
            for text in self.Texts:
                if text.name in texts:
                    row = box.row()
                    row.label(text= text.name)
                    row.prop(text, 'apply', text= '')

    def invoke(self, context, event):
        texts = self.Texts
        texts.clear()
        for text in bpy.data.texts:
            txt = texts.add()
            txt.name = text.name
        return bpy.context.window_manager.invoke_props_dialog(self)
classes.append(AR_OT_Record_LoadLoaclActions)

class AR_OT_Save(Operator):
    bl_idname = "ar.data_save"
    bl_label = "Save"
    bl_description = "Save all Global Actions to the Storage"

    def execute(self, context):
        Save()
        return {"FINISHED"}
classes.append(AR_OT_Save)

class AR_OT_Load(Operator):
    bl_idname = "ar.data_load"
    bl_label = "Load"
    bl_description = "Load all Action data from the Storage"

    def execute(self, context):
        Load()
        TempSaveCats()
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_Load)

class AR_OT_ButtonToRecord(Operator):
    bl_idname = "ar.category_button_to_record"
    bl_label = "Action Button to Local"
    bl_description = "Add the selected Action Button as a Local"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Instance_Coll)

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        
        Instance_to_Recorder()
        if AR_Var.BtnToRec_Mode == 'move':
            I_Remove()
            TempSaveCats()
            if AR_Var.Autosave:
                Save()
        TempUpdate()
        bpy.context.area.tag_redraw()
        SaveToDataHandler(None)
        return {"FINISHED"}
classes.append(AR_OT_ButtonToRecord)

class AR_OT_Button_Remove(Operator):
    bl_idname = "ar.category_remove_button"
    bl_label = "Remove Action Button"
    bl_description = "Remove the selected Action Button "

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Instance_Coll)

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        I_Remove()
        TempSaveCats()
        bpy.context.area.tag_redraw()
        if AR_Var.Autosave:
            Save()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
classes.append(AR_OT_Button_Remove)

class AR_OT_Button_MoveUp(Operator):
    bl_idname = "ar.category_move_up_button"
    bl_label = "Move Button Up"
    bl_description = "Move the selected Action Button Up"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        if len(AR_Var.Instance_Coll):
            index = AR_Var.Instance_Index
            start, end = getCollectionBorderOfButtonIndex(index, AR_Var)
            return len(AR_Var.Instance_Coll) and index > start and index <= end
        else:
            return False

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        I_Move('Up')
        TempSaveCats()
        bpy.context.area.tag_redraw()
        if AR_Var.Autosave:
            Save()
        return {"FINISHED"}
classes.append(AR_OT_Button_MoveUp)

class AR_OT_Button_MoveDown(Operator):
    bl_idname = "ar.category_move_down_button"
    bl_label = "Move Action Button Down"
    bl_description = "Move the selected Action Button Down"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        if len(AR_Var.Instance_Coll):
            AR_Var = context.preferences.addons[__package__].preferences
            index = AR_Var.Instance_Index
            start, end = getCollectionBorderOfButtonIndex(index, AR_Var)
            return len(AR_Var.Instance_Coll) and index >= start and index < end
        else:
            return False
        
    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        I_Move('Down')
        TempSaveCats()
        bpy.context.area.tag_redraw()
        if AR_Var.Autosave:
            Save()
        return {"FINISHED"}
classes.append(AR_OT_Button_MoveDown)

class AR_OT_Button_Rename(Operator):
    bl_idname = "ar.category_rename_button"
    bl_label = "Rename Button"
    bl_description = "Rename the selected Button"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Instance_Coll) and not (multiselection_buttons[0] and len(InstanceLastselected) > 1)

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        Rename_Instance()
        TempSaveCats()
        bpy.context.area.tag_redraw()
        if AR_Var.Autosave:
            Save()
        return {"FINISHED"}
classes.append(AR_OT_Button_Rename)

class AR_OT_Category_Cmd(Operator):
    bl_idname = 'ar.category_cmd_button'
    bl_label = 'ActRec Action Button'
    bl_description = 'Play this Action Button'
    bl_options = {'UNDO', 'INTERNAL'}

    Index : IntProperty()

    def execute(self, context):
        if Execute_Instance(self.Index):
            Data.alert_index = self.Index
            bpy.app.timers.register(AlertTimerCmd, first_interval = 1)
        return{'FINISHED'}
classes.append(AR_OT_Category_Cmd)

class AR_OT_Category_Cmd_Icon(icontable, Operator):
    bl_idname = "ar.category_cmd_icon"

    notInit : BoolProperty(default=False)
    index : IntProperty()
    search : StringProperty(name= "Icon Search", description= "search Icon by name", options= {'TEXTEDIT_UPDATE'})

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        AR_Var.Instance_Coll[self.index].icon = AR_preferences.SelectedIcon
        AR_preferences.SelectedIcon = 101 #Icon: BLANK1
        TempSaveCats()
        if AR_Var.Autosave:
            Save()
        bpy.context.area.tag_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        AR_Var = context.preferences.addons[__package__].preferences
        AR_preferences.SelectedIcon = AR_Var.Instance_Coll[self.index].icon
        self.search = ''
        return context.window_manager.invoke_props_dialog(self, width=1000)
classes.append(AR_OT_Category_Cmd_Icon)



class AR_OT_Record_SelectorUp(Operator):
    bl_idname = 'ar.record_selector_up'
    bl_label = 'ActRec Selection Up'

    def execute(self, context):
        Select_Command('Up')
        bpy.context.area.tag_redraw()
        return{'FINISHED'}
classes.append(AR_OT_Record_SelectorUp)

class AR_OT_Record_SelectorDown(Operator):
    bl_idname = 'ar.record_selector_down'
    bl_label = 'ActRec Selection Down'

    def execute(self, context):
        Select_Command('Down')
        bpy.context.area.tag_redraw()
        return{'FINISHED'}
classes.append(AR_OT_Record_SelectorDown)

class AR_OT_Record_Play(Operator):
    bl_idname = 'ar.record_play'
    bl_label = 'ActRec Play'
    bl_description = 'Play the selected Action.'
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Record_Coll[CheckCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)].Command)

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        index = AR_Var.Record_Coll[CheckCommand(0)].Index
        Play(AR_Var.Record_Coll[CheckCommand(index + 1)].Command, index)
        return{'FINISHED'}
classes.append(AR_OT_Record_Play)

class AR_OT_Record_Start(Operator):
    bl_idname = "ar.record_start"
    bl_label = "Start Recording"
    bl_description = "Starts Recording the Macros"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Record_Coll[CheckCommand(0)].Command)

    def execute(self, context):
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        scene = bpy.context.scene
        Record(AR_Var.Record_Coll[CheckCommand(0)].Index + 1 , 'Start')
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_Record_Start)

class AR_OT_Record_Stop(Operator):
    bl_idname = "ar.record_stop"
    bl_label = "Stop Recording"
    bl_description = "Stops Recording the Macros"

    def execute(self, context):
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        scene = bpy.context.scene
        messages = Record(AR_Var.Record_Coll[CheckCommand(0)].Index + 1 , 'Stop')
        if len(messages):
            self.report({'ERROR'}, "Not all actions were added because they are not of type Operator:\n    %s" % "\n    ".join(messages))
        TempUpdateCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)
        bpy.context.area.tag_redraw()
        SaveToDataHandler(None)
        return {"FINISHED"}
classes.append(AR_OT_Record_Stop)

class AR_OT_Record_Icon(icontable, Operator):
    bl_idname = "ar.record_icon"

    index : IntProperty()
    search : StringProperty(name= "Icon Search", description= "search Icon by name", options= {'TEXTEDIT_UPDATE'})

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        AR_Var.Record_Coll[0].Command[self.index].icon = AR_preferences.SelectedIcon
        AR_preferences.SelectedIcon = 101 #Icon: BLANK1
        bpy.context.area.tag_redraw()
        SaveToDataHandler(None)
        return {"FINISHED"}

    def invoke(self, context, event):
        self.search = ''
        AR_Var = context.preferences.addons[__package__].preferences
        AR_preferences.SelectedIcon = AR_Var.Record_Coll[0].Command[self.index].icon
        return context.window_manager.invoke_props_dialog(self, width=1000)
classes.append(AR_OT_Record_Icon)

class AR_OT_Record_Execute(Operator):
    bl_idname = "ar.record_execute"
    bl_label = "Execute Action"

    index : IntProperty()

    def execute(self, content):
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        Play(AR_Var.Record_Coll[CheckCommand(self.index)].Command, self.index - 1)
        return {"FINISHED"}
classes.append(AR_OT_Record_Execute)

class AR_OT_Command_Add(Operator):
    bl_idname = "ar.command_add"
    bl_label = "ActRec Add Macro"
    bl_description = "Add the last operation you executed"

    command : StringProperty()

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Record_Coll[CheckCommand(0)].Command)

    def execute(self, context):
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        scene = context.scene
        if self.command == "":
            message = Add(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)
        else:
            message = Add(AR_Var.Record_Coll[CheckCommand(0)].Index + 1, self.command)
        if message == "<Empty>":
            rec = AR_Var.Record_Coll[CheckCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)]
            index = len(rec.Command) - 1
            rec.Index = index
            bpy.ops.ar.command_edit('INVOKE_DEFAULT', index= index, Edit= True)
        elif type(message) == str:
            self.report({'ERROR'}, "Action could not be added because it is not of type Operator:\n %s" % message)
        elif message:
            self.report({'ERROR'}, "No Action could be added")
        if (AR_Var.CreateEmpty and message) or not message:
            rec = AR_Var.Record_Coll[CheckCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)]
            rec.Index = len(rec.Command) - 1
        TempUpdateCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)
        bpy.context.area.tag_redraw()
        SaveToDataHandler(None)
        return {"FINISHED"}
classes.append(AR_OT_Command_Add)

class AR_OT_Command_Remove(Operator):
    bl_idname = "ar.command_remove"
    bl_label = "Remove Macro"
    bl_description = "Remove the selected Macro"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Record_Coll[CheckCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)].Command)

    def execute(self, context):
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        scene = context.scene
        Remove(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)
        TempUpdateCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)
        bpy.context.area.tag_redraw()
        SaveToDataHandler(None)
        return {"FINISHED"}
classes.append(AR_OT_Command_Remove)

class AR_OT_Command_MoveUp(Operator):
    bl_idname = "ar.command_move_up"
    bl_label = "Move Macro Up"
    bl_description = "Move the selected Macro up"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Record_Coll[CheckCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)].Command)

    def execute(self, context):
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        scene = context.scene
        Move(AR_Var.Record_Coll[CheckCommand(0)].Index + 1 , 'Up')
        TempUpdateCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)
        bpy.context.area.tag_redraw()
        SaveToDataHandler(None)
        return {"FINISHED"}
classes.append(AR_OT_Command_MoveUp)

class AR_OT_Command_MoveDown(Operator):
    bl_idname = "ar.command_move_down"
    bl_label = "Move Macro Down"
    bl_description = "Move the selected Macro down"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Record_Coll[CheckCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)].Command)

    def execute(self, context):
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        scene = context.scene
        Move(AR_Var.Record_Coll[CheckCommand(0)].Index + 1 , 'Down')
        TempUpdateCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)
        bpy.context.area.tag_redraw()
        SaveToDataHandler(None)
        return {"FINISHED"}
classes.append(AR_OT_Command_MoveDown)

class AR_OT_Command_Clear(Operator):
    bl_idname = "ar.command_clear"
    bl_label = "Clear Macros"
    bl_description = "Delete all Macro of the selected Action"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Record_Coll[CheckCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)].Command)

    def execute(self, context):
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        scene = context.scene
        Clear(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)
        TempUpdateCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)
        bpy.context.area.tag_redraw()
        SaveToDataHandler(None)
        return {"FINISHED"}
classes.append(AR_OT_Command_Clear)

class FontText():
    def __init__(self, fontpath):
        self.path = fontpath
        # install the fonttools to blender modules if not exists
        if importlib.util.find_spec('fontTools') is None:
            ensurepip.bootstrap()
            os.environ.pop("PIP_REQ_TRACKER", None)
            try:
                output = subprocess.check_output([bpy.app.binary_path_python, '-m', 'pip', 'install', 'fonttools', '--no-color'])
                logger.info(output)
            except subprocess.CalledProcessError as e:
                logger.warning(e.output)
                self.use_dynamic_text = False
                return
        self.use_dynamic_text = True
        from fontTools.ttLib import TTFont

        font = TTFont(fontpath)
        self.t = font['cmap'].getcmap(3,1).cmap
        self.s = font.getGlyphSet()
        self.width_in_pixels = 10/font['head'].unitsPerEm
    
    def getWidthOfText(self, text):
        total = []
        for c in text:
            total.append(self.s[self.t[ord(c)]].width * self.width_in_pixels)
        return total
def Edit_Commandupdate(self, context):
    Data.Edit_Command = self.Command
cmd_edit_time = [0]
class AR_OT_Command_Edit(Operator):
    bl_idname = "ar.command_edit"
    bl_label = "Edit"
    bl_description = "Double click to Edit"

    Name : StringProperty(name= "Name")
    Command : StringProperty(name= "Command", update= Edit_Commandupdate)
    last : StringProperty()
    index : IntProperty()
    Edit : BoolProperty(default= False)
    CopyData : BoolProperty(default= False, name= "Copy Previous", description= "Copy the data of the previous recorded Macro and place it in this Macro")
    class AR_Multiline(PropertyGroup):
        line : StringProperty()
    classes.append(AR_Multiline)
    text : CollectionProperty(type= AR_Multiline)
    active_line : IntProperty(default= 0)
    width = 500
    font_text = FontText(getFontPath())

    def execute(self, context):
        self.Edit = False
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        index_btn = AR_Var.Record_Coll[CheckCommand(0)].Index + 1
        index_macro = AR_Var.Record_Coll[CheckCommand(index_btn)].Index
        macro = AR_Var.Record_Coll[CheckCommand(index_btn)].Command[index_macro]
        if self.CopyData:
            macro.macro = AR_Var.LastLine
            macro.cname = AR_Var.LastLineCmd
        else:
            macro.macro = self.Name
            macro.cname = self.Command
        TempUpdateCommand(index_btn)
        bpy.context.area.tag_redraw()
        SaveToDataHandler(None)
        return {"FINISHED"}

    def draw(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        layout = self.layout
        self.Command = ""
        for line in self.text:
            self.Command += line.line
        command = ""
        if self.CopyData:
            layout.prop(AR_Var, 'LastLine', text= "Name")
            command = AR_Var.LastLineCmd
        else:
            layout.prop(self, 'Name', text= "Name")
            command = self.Command
        self.text.clear()
        for line in TextToLines(command, self.font_text, self.width - 16): # 8 left and right of the Stringproperty begins text
            new = self.text.add()
            new.line = line
        col = layout.column(align= True)
        for line in self.text:
            col.prop(line, 'line', text= "")
        row = layout.row().split(factor= 0.65)
        ops = row.operator(AR_OT_ClearOperator.bl_idname)
        ops.Command = self.Command
        row.prop(self, 'CopyData', toggle= True)

    def invoke(self, context, event):
        AR_Var = context.preferences.addons[__package__].preferences
        index_btn = AR_Var.Record_Coll[CheckCommand(0)].Index + 1
        macro = AR_Var.Record_Coll[CheckCommand(index_btn)].Command[self.index]
        mlast = f"{index_btn}.{self.index}" 
        t = time.time()
        self.CopyData = False
        if self.last == mlast and cmd_edit_time[0] + 0.7 > t or self.Edit:
            self.last = mlast
            cmd_edit_time[0] = t
            split = macro.cname.split(":")
            if split[0] == 'ar.event':
                data = json.loads(":".join(split[1:]))
                if data['Type'] == 'Timer':
                    bpy.ops.ar.addevent('INVOKE_DEFAULT', Type= data['Type'], Num= self.index, time= data['Time'])
                elif data['Type'] == 'Loop':
                    if data['StatementType'] == 'python':
                        bpy.ops.ar.addevent('INVOKE_DEFAULT', Type= data['Type'], Num= self.index, Statements= data['StatementType'], PythonStatement= data["PyStatement"])
                    else:
                        bpy.ops.ar.addevent('INVOKE_DEFAULT', Type= data['Type'], Num= self.index, Statements= data['StatementType'], Startnumber= data["Startnumber"], Endnumber= data["Endnumber"], Stepnumber= data["Stepnumber"])
                elif data['Type'] == 'Select Object':
                    bpy.ops.ar.addevent('INVOKE_DEFAULT', Type= data['Type'], Num= self.index, SelectedObject= data['Object'])
                elif data['Type'] == 'Select Vertices':
                    bpy.ops.ar.addevent('INVOKE_DEFAULT', Type= data['Type'], Num= self.index, VertObj= data['Object'])
                else:
                    bpy.ops.ar.addevent('INVOKE_DEFAULT', Type= data['Type'], Num= self.index)
                SaveToDataHandler(None)
                return {"FINISHED"}
            self.Name = macro.macro
            self.Command = macro.cname
            Data.Edit_Command = self.Command
            fontpath = getFontPath()
            if self.font_text.path != fontpath:
                logger.debug("path", self.font_text.path != fontpath)
                self.font_text = FontText(fontpath)
            self.text.clear()
            for line in TextToLines(self.Command, self.font_text, self.width - 15):
                new = self.text.add()
                new.line = line
            return context.window_manager.invoke_props_dialog(self, width=self.width)
        else:
            self.last = mlast
            cmd_edit_time[0] = t
            AR_Var.Record_Coll[CheckCommand(index_btn)].Index = self.index
        return {"FINISHED"}

    def cancel(self, context):
        self.Edit = False
classes.append(AR_OT_Command_Edit)

class AR_OT_Command_Run_Queued(Operator):
    bl_idname = "ar.command_run_queued"
    bl_label = "Run Queued Commands"
    bl_options ={'INTERNAL'}

    _timer = None

    def execute(self, context):
        while not execution_queue.empty():
            function = execution_queue.get()
            function()
            Data.ActiveTimers -= 1
        return {"FINISHED"}
    
    def modal(self, context, event):
        if Data.ActiveTimers > 0:
            self.execute(context)
            return {'PASS_THROUGH'}
        else:
            self.cancel(context)
            return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.05, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
classes.append(AR_OT_Command_Run_Queued)

class AR_OT_AddEvent(Operator):
    bl_idname = "ar.addevent"
    bl_label = "Add Event"
    bl_description = "Add a Event which wait until the Event is Triggered"

    TypesList = [('Timer', 'Timer', 'Wait the chosen Time and continue with the Macros', 'SORTTIME', 0),
                ('Render Complet', 'Render complet', 'Wait until the rendering has finished', 'IMAGE_RGB_ALPHA', 1),
                ('Render Init', 'Render Init', 'Wait until the rendering has started', 'IMAGE_RGB', 2),
                ('Loop', 'Loop', 'Loop the conatining Makros until the Statment is False \nNote: The Loop need the EndLoop Event to work, otherwise the Event get skipped', 'FILE_REFRESH', 3),
                ('EndLoop', 'EndLoop', 'Ending the latetest called loop, when no Loop Event was called this Event get skipped', 'FILE_REFRESH', 4),
                ('Clipboard', 'Clipboard', 'Adding a command with the data from the Clipboard', 'CONSOLE', 5),
                ('Empty', 'Empty', 'Crates an Empty Macro', 'SHADING_BBOX', 6) #,
                #('Select Object', 'Select Object', 'Select the choosen object', 'OBJECT_DATA', 7),
                #('Select Vertices', 'Select Vertices', 'Select the choosen verts', 'GROUP_VERTEX', 8)
                ]
    Type : EnumProperty(items= TypesList, name= "Event Type", description= 'Shows all possible Events', default= 'Timer')
    time : FloatProperty(name= "Time", description= "Time in Seconds", unit='TIME')
    Statements : EnumProperty(items=[('count', 'Count', 'Count a Number from the Startnumber with the Stepnumber to the Endnumber, \nStop when Number > Endnumber', '', 0),
                                    ('python', 'Python Statment', 'Create a custom statement with python code', '', 1)])
    Startnumber : FloatProperty(name= "Startnumber", description= "Startnumber of the Count statements", default=0)
    Stepnumber : FloatProperty(name= "Stepnumber", description= "Stepnumber of the Count statements", default= 1)
    Endnumber : FloatProperty(name= "Endnumber", description= "Endnumber of the Count statements", default= 1)
    PythonStatement : StringProperty(name= "Statement", description= "Statment for the Python Statement")
    Num : IntProperty(default= -1)
    SelectedObject : StringProperty(name= "Object", description= "Choose an Object which get select when this Event is played")
    VertObj : StringProperty(name= "Object", description= "Choose an Object to get the selected verts from")

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Record_Coll[CheckCommand(0)].Command)

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        selected_action = CheckCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)
        if self.Num == -1:
            Item = AR_Var.Record_Coll[selected_action].Command.add()
        else:
            Item = AR_Var.Record_Coll[selected_action].Command[self.Num]
        selected_action = CheckCommand(AR_Var.Record_Coll[CheckCommand(0)].Index + 1)
        rec = AR_Var.Record_Coll[selected_action]
        index = len(rec.Command) - 1
        rec.Index = index
        if self.Type == 'Clipboard':
            cmd = context.window_manager.clipboard
            macro = GetMacro(cmd)
            if type(macro) != str:
                macro = cmd
            Item.macro = macro
            Item.cname = cmd
        elif self.Type == 'Empty':
            Item.macro = "<Empty>"
            Item.cname = ""
            bpy.ops.ar.command_edit('INVOKE_DEFAULT', index= index, Edit= True)
        else:
            Item.macro = "Event: " + self.Type
            data = {'Type': self.Type}
            if self.Type == 'Timer':
                data['Time'] = self.time
            elif self.Type == 'Loop':
                data['StatementType'] = self.Statements
                if self.Statements == 'python':
                    data["PyStatement"] = self.PythonStatement
                else:
                    data["Startnumber"] = self.Startnumber
                    data["Endnumber"] = self.Endnumber
                    data["Stepnumber"] = self.Stepnumber
            elif self.Type == 'Select Object':
                data['Object'] = self.SelectedObject
            elif self.Type == 'Select Vertices':
                data['Object'] = self.VertObj
                selverts = []
                obj = bpy.context.view_layer.objects[self.VertObj]
                obj.update_from_editmode()
                verts = obj.data.vertices
                for v in verts:
                    if v.select:
                        selverts.append(v.index)
                data['Verts'] = selverts
            Item.cname = "ar.event:" + json.dumps(data)
        TempUpdateCommand(selected_action)
        if not AR_Var.hideLocal:
            UpdateRecordText(selected_action)
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'Type')
        if self.Type == 'Timer':
            box = layout.box()
            box.prop(self, 'time')
        elif self.Type == 'Loop':
            box = layout.box()
            box.prop(self, 'Statements')
            box.separator()
            if self.Statements == 'python':
                box.prop(self, 'PythonStatement')
            else:
                box.prop(self, 'Startnumber')
                box.prop(self, 'Endnumber')
                box.prop(self, 'Stepnumber')
        elif self.Type == 'Select Object':
            box = layout.box()
            box.prop_search(self, 'SelectedObject', bpy.context.view_layer, 'objects')
        elif self.Type == 'Select Vertices':
            box = layout.box()
            box.prop_search(self, 'VertObj', bpy.data, 'meshes')

    def invoke(self, context, event):
        if bpy.context.object != None:
            obj = bpy.context.object.name
            self.SelectedObject = obj
            index = bpy.data.meshes.find(obj)
            if index != -1:
                self.VertObj = obj
        return context.window_manager.invoke_props_dialog(self)
classes.append(AR_OT_AddEvent)

class AR_OT_CopyToActRec(Operator):
    bl_idname = "ar.copy_to_actrec"
    bl_label = "Copy to Action Recorder"
    bl_description = "Copy the selected Operator to Action Recorder Macro"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return context.active_object is not None and len(AR_Var.Record_Coll[CheckCommand(0)].Command)

    def execute(self, context):
        bpy.ops.ui.copy_python_command_button()
        bpy.ops.ar.command_add('EXEC_DEFAULT', command= bpy.context.window_manager.clipboard)
        return {"FINISHED"}
classes.append(AR_OT_CopyToActRec)

class AR_OT_ClearOperator(Operator):
    bl_idname = "ar.command_clearoperator"
    bl_label = "Clear Operator"
    bl_options = {'INTERNAL'}

    Command : StringProperty()
    
    def execute(self, context):
        Data.Edit_Command = self.Command.split("(")[0] + "()"
        return {"FINISHED"}
classes.append(AR_OT_ClearOperator)


# endregion

# region Menus
class AR_MT_Action_Pie(Menu):
    bl_idname = "view3d.menuname"
    bl_label = "ActRec Pie Menu"
    bl_idname = "AR_MT_Action_Pie"

    def draw(self, context):
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        pie = self.layout.menu_pie()
        actions = AR_Var.Record_Coll[CheckCommand(0)].Command
        for i in range(len(actions)):
            if i >= 8:
                break
            ops = pie.operator(AR_OT_Record_Execute.bl_idname, text= actions[i].cname).index = i + 1
classes.append(AR_MT_Action_Pie)

def menu_func(self, context):
    if bpy.ops.ui.copy_python_command_button.poll():
        layout = self.layout
        layout.separator()
        layout.operator(AR_OT_CopyToActRec.bl_idname)

class WM_MT_button_context(Menu):
    bl_label = "Add Viddyoze Tag"

    def draw(self, context):
        pass
blendclasses.append(WM_MT_button_context)

# endregion

# region PropertyGroups
def SavePrefs(self, context):
    if not ontempload[0]:
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        TempUpdateCommand(AR_Var.Record_Coll[0].Index + 1)

def SetRecordName(self, value):
    textI = bpy.data.texts.find(self.cname)
    if textI != -1:
        text = bpy.data.texts[textI]
        text.name = value
    self['cname'] = value
    SaveToDataHandler(None)

def GetCname(self):
    return self.get('cname', '')

class AR_Record_Struct(PropertyGroup):
    cname : StringProperty(set= SetRecordName, get=GetCname) #AR_Var.name
    macro : StringProperty()
    active : BoolProperty(default= True, update= SavePrefs, description= 'Toggles Macro on and off.')
    alert : BoolProperty()
    icon : IntProperty(default= 286) #Icon: MESH_PLANE
classes.append(AR_Record_Struct)

class AR_Record_Merge(PropertyGroup):
    Index : IntProperty()
    Command : CollectionProperty(type = AR_Record_Struct)
classes.append(AR_Record_Merge)

class AR_FileDisp(PropertyGroup):
    Index : BoolProperty(default= False)
classes.append(AR_FileDisp)

class AR_CategorizeFileDisp(PropertyGroup):
    pn_name : StringProperty()
    pn_show : BoolProperty(default= True)
    pn_selected : BoolProperty(default= False)
    FileDisp_Start : IntProperty(default= 0)
    FileDisp_length : IntProperty(default= 0)
classes.append(AR_CategorizeFileDisp)


class AR_ImportButton(PropertyGroup):
    btn_name: StringProperty()
    icon: StringProperty()
    command: StringProperty()
    enum: EnumProperty(items= [("add", "Add", ""),("overwrite", "Overwrite", "")], name= "Import Mode")
classes.append(AR_ImportButton)

class AR_ImportCategory(PropertyGroup):
    cat_name: StringProperty()
    Buttons : CollectionProperty(type= AR_ImportButton)
    enum: EnumProperty(items= [("new", "New", "Create a new Category"),("append", "Append", "Append to an existing Category")], name= "Import Mode")
    show : BoolProperty(default= True)
classes.append(AR_ImportCategory)


class AR_CommandEditProp(PropertyGroup):
    prop : bpy.types.Property

# endregion



# region Registration
for spaceType in spaceTypes:
    panelFactory( spaceType )

def Initialize_Props():
    bpy.types.Scene.ar_filecategories = CollectionProperty(type= AR_CategorizeFileDisp)
    bpy.types.Scene.ar_filedisp = CollectionProperty(type= AR_FileDisp)
    bpy.types.Scene.ar_local = StringProperty(name= 'AR Local', description= 'Scene Backup-Data of AddonPreference.RecordColl (= Local Actions)', default= '{}')
    bpy.app.handlers.depsgraph_update_pre.append(InitSavedPanel)
    bpy.app.handlers.undo_post.append(TempLoad) # add TempLoad to ActionHandler and call ist after undo
    bpy.app.handlers.redo_post.append(TempLoad) # also for redo
    bpy.app.handlers.undo_post.append(TempLoadCats)
    bpy.app.handlers.redo_post.append(TempLoadCats)
    bpy.app.handlers.save_pre.append(SaveToDataHandler)
    bpy.app.handlers.load_post.append(LoadLocalActions)
    bpy.app.handlers.render_complete.append(runRenderComplete)
    bpy.app.handlers.render_init.append(runRenderInit)
    bpy.types.WM_MT_button_context.append(menu_func)
    if bpy.context.window_manager.keyconfigs.addon:
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Screen')
        AR_preferences.addon_keymaps.append(km)
        for (idname, key, event, ctrl, alt, shift, name) in AR_preferences.key_assign_list:
            kmi = km.keymap_items.new(idname, key, event, ctrl=ctrl, alt=alt, shift=shift)
            if not name is None:
                kmi.properties.name = name
    bpy.app.timers.register(TimerInitSavedPanel, first_interval = 1)
    
def Clear_Props():
    del bpy.types.Scene.ar_filedisp
    del bpy.types.Scene.ar_filecategories
    del bpy.types.Scene.ar_local
    bpy.app.handlers.undo_post.remove(TempLoad)
    bpy.app.handlers.redo_post.remove(TempLoad)
    bpy.app.handlers.undo_post.remove(TempLoadCats)
    bpy.app.handlers.redo_post.remove(TempLoadCats)
    bpy.app.handlers.save_pre.remove(SaveToDataHandler)
    bpy.app.handlers.load_post.remove(LoadLocalActions)
    try:
        bpy.app.handlers.render_complete.remove(runRenderComplete)
    except:
        logger.debug("runRenderComplete already removed")
    try:
        bpy.app.handlers.render_init.remove(runRenderInit)
    except:
        logger.debug("runRenderInit already removed")
    try:
        bpy.types.WM_MT_button_context.remove(menu_func)
    except:
        logger.debug('menu_func already removed')
    try:
        bpy.app.handlers.depsgraph_update_pre.remove(InitSavedPanel)
    except:
        pass
    bpy.context.window_manager.keyconfigs.addon.keymaps.remove(AR_preferences.addon_keymaps[0])
    AR_preferences.addon_keymaps.clear() #Unregister Preview Collection
# endregion