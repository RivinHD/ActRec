# region Imports
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

# region Functions
def CheckCommand(num): #Add a new Collection if necessary
    AR = bpy.context.preferences.addons[__module__].preferences
    while len(AR.Record_Coll) <= num:
        AR.Record_Coll.add()
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

def CreateTempFile():
    tpath = bpy.app.tempdir + "temp.json"
    if not os.path.exists(tpath):
        logger.info(tpath)
        with open(tpath, 'w', encoding='utf-8') as tempfile:
            json.dump({"0":[]}, tempfile)
    return tpath

def TempSave(Num):  # write new record to temp.json file
    tpath = CreateTempFile()
    AR = bpy.context.preferences.addons[__module__].preferences
    with open(tpath, 'r+', encoding='utf-8') as tempfile:   
        data = json.load(tempfile)
        data.update({str(Num):[]})
        data["0"] = [{"name": i.cname, "macro": i.macro, "icon": i.icon, "active": i.active} for i in AR.Record_Coll[CheckCommand(0)].Command]
        tempfile.truncate(0)
        tempfile.seek(0)
        json.dump(data, tempfile)

def TempUpdate(): # update all records in temp.json file
    tpath = CreateTempFile()
    AR = bpy.context.preferences.addons[__module__].preferences
    with open(tpath, 'r+', encoding='utf-8') as tempfile:
        tempfile.truncate(0)    
        tempfile.seek(0)
        data = {}
        for cmd in range(len(AR.Record_Coll[CheckCommand(0)].Command) + 1):
            data.update({str(cmd):[{"name": i.cname, "macro": i.macro, "icon": i.icon, "active": i.active} for i in AR.Record_Coll[CheckCommand(cmd)].Command]})
        json.dump(data, tempfile)

def TempUpdateCommand(Key): # update one record in temp.json file
    tpath = CreateTempFile()
    AR = bpy.context.preferences.addons[__module__].preferences
    with open(tpath, 'r+', encoding='utf-8') as tempfile:
        data = json.load(tempfile)
        data[str(Key)] = [{"name": i.cname, "macro": i.macro, "icon": i.icon, "active": i.active} for i in AR.Record_Coll[CheckCommand(int(Key))].Command]
        tempfile.truncate(0)
        tempfile.seek(0)
        json.dump(data, tempfile)

@persistent
def TempLoad(dummy): # load records after undo
    tpath = bpy.app.tempdir + "temp.json"
    ontempload[0] = True
    AR = bpy.context.preferences.addons[__module__].preferences
    if os.path.exists(tpath):
        with open(tpath, 'r', encoding='utf-8') as tempfile:
            data = json.load(tempfile)
        command = AR.Record_Coll[CheckCommand(0)].Command
        command.clear()
        keys = list(data.keys())
        for i in range(1, len(data)):
            Item = command.add()
            Item.macro = data["0"][i - 1]["macro"]
            Item.cname = data["0"][i - 1]["name"]
            Item.icon = data["0"][i - 1]["icon"]
            record = AR.Record_Coll[CheckCommand(i)].Command
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
    AR = bpy.context.preferences.addons[__module__].preferences
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
                if macro is None and AR.CreateEmpty:
                    Item = AR.Record_Coll[CheckCommand(Num)].Command.add()
                    Item.macro = "<Empty>"
                    Item.cname = ""
            elif AR.LastLineIndex == line and AR.LastLineCmd == name:
                notadded = "<Empty>"
                Item = AR.Record_Coll[CheckCommand(Num)].Command.add()
                Item.macro = "<Empty>"
                Item.cname = ""
            else:
                Item = AR.Record_Coll[CheckCommand(Num)].Command.add()
                Item.macro = macro
                Item.cname = name
                if line != -1:
                    AR.LastLine = macro
                    AR.LastLineIndex = line
                    AR.LastLineCmd = name
            if not AR.hideLocal:
                UpdateRecordText(Num)
            return notadded
        except Exception as err:
            if AR.CreateEmpty:
                Item = AR.Record_Coll[CheckCommand(Num)].Command.add()
                Item.macro = "<Empty>"
                Item.cname = ""
            logger.error("Action Adding Failure: " + str(err))
            return True
    else: # Add Record
        Item = AR.Record_Coll[CheckCommand(Num)].Command.add()
        if command == None:
            Item.cname = CheckForDublicates([cmd.cname for cmd in AR.Record_Coll[CheckCommand(0)].Command], 'Untitled.001')
        else:
            Item.cname = CheckForDublicates([cmd.cname for cmd in AR.Record_Coll[CheckCommand(0)].Command], command)
    AR.Record_Coll[CheckCommand(Num)].Index = len(AR.Record_Coll[CheckCommand(Num)].Command) - 1
    if not AR.hideLocal:
        bpy.data.texts.new(Item.cname)

def Remove(Num): # Remove Record or Macro
    AR = bpy.context.preferences.addons[__module__].preferences
    index = AR.Record_Coll[CheckCommand(Num)].Index
    if Num:
        UpdateRecordText(Num)
    else:
        txtname = AR.Record_Coll[CheckCommand(Num)].Command[index].cname
        if bpy.data.texts.find(txtname) != -1:
            bpy.data.texts.remove(bpy.data.texts[txtname])
    AR.Record_Coll[Num].Command.remove(index)
    if not Num:
        AR.Record_Coll.remove(index + 1)
    AR.Record_Coll[Num].Index = (index - 1) * (index - 1 > 0)

def Move(Num , Mode) :# Move Record or Macro
    AR = bpy.context.preferences.addons[__module__].preferences
    index1 = AR.Record_Coll[CheckCommand(Num)].Index
    if Mode == 'Up' :
        index2 = AR.Record_Coll[CheckCommand(Num)].Index - 1
    else :
        index2 = AR.Record_Coll[CheckCommand(Num)].Index + 1
    LengthTemp = len(AR.Record_Coll[CheckCommand(Num)].Command)
    if (2 <= LengthTemp) and (0 <= index1 < LengthTemp) and (0 <= index2 < LengthTemp):
        AR.Record_Coll[CheckCommand(Num)].Command.move(index1, index2)
        AR.Record_Coll[CheckCommand(Num)].Index = index2
        if not Num:
            AR.Record_Coll.move(index1 + 1, index2 + 1)

def Select_Command(Mode): # Select the upper/lower Record
    AR = bpy.context.preferences.addons[__module__].preferences
    currentIndex = AR.Record_Coll[CheckCommand(0)].Index
    listlen = len(AR.Record_Coll[CheckCommand(0)].Command) - 1
    if Mode == 'Up':
        if currentIndex == 0:
            AR.Record_Coll[CheckCommand(0)].Index = listlen
        else:
            AR.Record_Coll[CheckCommand(0)].Index = currentIndex - 1
    else:
        if currentIndex == listlen:
            AR.Record_Coll[CheckCommand(0)].Index = 0
        else:
            AR.Record_Coll[CheckCommand(0)].Index = currentIndex + 1

def Alert(Command, index, CommandIndex):
    AR = bpy.context.preferences.addons[__module__].preferences
    Command.alert = True
    AR.Record_Coll[CheckCommand(index + 1)].Index = CommandIndex
    AR.Record_Coll[CheckCommand(0)].Command[index].alert = True
    bpy.app.timers.register(functools.partial(AlertTimerPlay, index), first_interval = 1)
    try:
        bpy.context.area.tag_redraw()
    except:
        redrawLocalANDMacroPanels()

def Clear(Num) : # Clear all Macros
    AR = bpy.context.preferences.addons[__module__].preferences
    AR.Record_Coll[CheckCommand(Num)].Command.clear()
    UpdateRecordText(Num)

def Load():#Load Buttons from Storage
    logger.info('Load')
    AR = bpy.context.preferences.addons[__module__].preferences
    for cat in AR.Categories:
        RegisterUnregister_Category(ar_category.functions.get_panel_index(cat), False)
    AR.Categories.clear()
    AR.ar_enum.clear()
    AR.Instance_Coll.clear()
    AR.Instance_Index = 0
    path = AR.storage_path
    for folder in sorted(os.listdir(path)):
        folderpath = os.path.join(path, folder)
        if os.path.isdir(folderpath):
            textfiles = os.listdir(folderpath)
            new = AR.Categories.add()
            name = "".join(folder.split('~')[1:])
            new.name = name
            new.pn_name = name
            new.Instance_Start = len(AR.Instance_Coll)
            new.Instance_length = len(textfiles)
            sortedtxt = [None] * len(textfiles)
            RegisterUnregister_Category(ar_category.functions.get_panel_index(new))
            for i in textfiles:
                new_e = AR.ar_enum.add()
                e_index = len(AR.ar_enum) - 1
                new_e.name = str(e_index)
                new_e.Index = e_index
                new_e.Value = False
            for txt in textfiles:
                sortedtxt[int(txt.split('~')[0])] = txt #get the index 
            for i in range(len(sortedtxt)):
                txt = sortedtxt[i]
                inst = AR.Instance_Coll.add()
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
                with open(os.path.join(folderpath, txt), 'r', encoding='utf-8') as text:
                    for line in text.readlines():
                        cmd = inst.commands.add()
                        line_split = line.strip().split('#')
                        updated_cmd = update_command(line_split[0])
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
    for iconpath in os.listdir(AR.IconFilePath): # Load Icons
        filepath = os.path.join(AR.IconFilePath, iconpath)
        if os.path.isfile(filepath):
            load_icons(filepath, True)
    set_enum_index()()

@persistent
def LoadLocalActions(dummy):
    logger.info('Load Local Actions')
    scene = bpy.context.scene
    AR = bpy.context.preferences.addons[__module__].preferences
    AR.Record_Coll.clear()
    local = json.loads(scene.ar_local)
    for ele in local:
        loc = AR.Record_Coll.add()
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
        loc = AR.Record_Coll[i]
        if  loc.name == ele['name'] and loc.Index == ele['Index'] and len(ele['Command']) == len(loc.Command):
            i += 1
        else:
            AR.Record_Coll.remove(i)
    SaveToDataHandler(None)

def Recorder_to_Instance(panel): #Convert Record to Button
    AR = bpy.context.preferences.addons[__module__].preferences
    i = panel.Instance_Start + panel.Instance_length
    rec_commands = []
    rec_macros = []
    for Command in AR.Record_Coll[CheckCommand(AR.Record_Coll[CheckCommand(0)].Index + 1)].Command:
        rec_commands.append(Command.cname)
        rec_macros.append(Command.macro)
    data = {"name":CheckForDublicates([AR.Instance_Coll[j].name for j in range(panel.Instance_Start, i)], AR.Record_Coll[CheckCommand(0)].Command[AR.Record_Coll[CheckCommand(0)].Index].cname),
            "command": rec_commands,
            "macro" : rec_macros,
            "icon": AR.Record_Coll[CheckCommand(0)].Command[AR.Record_Coll[CheckCommand(0)].Index].icon}
    Inst_Coll_Insert(i, data , AR.Instance_Coll)
    panel.Instance_length += 1
    new_e = AR.ar_enum.add()
    e_index = len(AR.ar_enum) - 1
    new_e.name = str(e_index)
    new_e.Index = e_index
    categories = AR.Categories
    for cat in categories:
        if cat.Instance_Start > panel.Instance_Start:
            cat.Instance_Start -= 1

def Execute_Instance(Num): #Execute a Button
    AR = bpy.context.preferences.addons[__module__].preferences
    for cmd in AR.Instance_Coll[Num].commands:
        try:
            exec(cmd.name)
        except:
            return True # Alert

def Rename_Instance(): #Rename a Button
    AR = bpy.context.preferences.addons[__module__].preferences
    AR.Instance_Coll[AR.Instance_Index].name = AR.Rename

def I_Remove(): # Remove a Button
    AR = bpy.context.preferences.addons[__module__].preferences
    scene = bpy.context.scene
    l = []
    if multiselection_buttons[0]:
        for i in range(len(AR.ar_enum)):
            if AR.ar_enum[i].Value:
                l.append(i)
    else:
        l.append(AR.Instance_Index)
    offset = 0
    for Index in l:
        if len(AR.Instance_Coll) :
            Index = Index - offset
            AR.Instance_Coll.remove(Index)
            AR.ar_enum.remove(len(AR.ar_enum) - 1)
            categories = AR.Categories
            for cat in categories:
                if Index >= cat.Instance_Start and Index < cat.Instance_Start + cat.Instance_length:
                    cat.Instance_length -= 1
                    for cat2 in categories:
                        if cat2.Instance_Start > cat.Instance_Start:
                            cat2.Instance_Start -= 1
                    break
            if len(AR.Instance_Coll) and len(AR.Instance_Coll)-1 < Index :
                AR.Instance_Index = len(AR.Instance_Coll)-1
            offset += 1
    set_enum_index()()

def I_Move(Mode): # Move a Button to the upper/lower
    AR = bpy.context.preferences.addons[__module__].preferences
    scene = bpy.context.scene
    l = []
    if multiselection_buttons[0]:
        multiselection_buttons[1] = False
        for i in range(len(AR.ar_enum)):
            if AR.ar_enum[i].Value:
                l.append(i)
    else:
        l.append(AR.Instance_Index)
    if Mode == 'Down':
        l.reverse()
    for index1 in l:
        if Mode == 'Up' :
            index2 = index1 - 1
        else :
            index2 = index1 + 1
        LengthTemp = len(AR.Instance_Coll)
        if (2 <= LengthTemp) and (0 <= index1 < LengthTemp) and (0 <= index2 < LengthTemp):
            AR.Instance_Coll[index1].name , AR.Instance_Coll[index2].name = AR.Instance_Coll[index2].name , AR.Instance_Coll[index1].name
            AR.Instance_Coll[index1].icon , AR.Instance_Coll[index2].icon = AR.Instance_Coll[index2].icon , AR.Instance_Coll[index1].icon
            index1cmd = [cmd.name for cmd in AR.Instance_Coll[index1].commands]
            index2cmd = [cmd.name for cmd in AR.Instance_Coll[index2].commands]
            AR.Instance_Coll[index1].commands.clear()
            AR.Instance_Coll[index2].commands.clear()
            for cmd in index2cmd:
                new = AR.Instance_Coll[index1].commands.add()
                new.name = cmd
            for cmd in index1cmd:
                new = AR.Instance_Coll[index2].commands.add()
                new.name = cmd
            AR.ar_enum[index1].Value = False
            AR.ar_enum[index2].Value = True
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
    AR = bpy.context.preferences.addons[__module__].preferences
    if bpy.data.filepath == '':
        AR.Record_Coll.clear()
    LoadLocalActions(None)
    AR.Update = False
    AR.Version = ''
    AR.Restart = False
    if AR.AutoUpdate:
        bpy.ops.ar.update_check('EXEC_DEFAULT')
    AR.storage_path = AR.storage_path #Update storage_path
    path = AR.storage_path
    if not os.path.exists(path):
        os.mkdir(path)
    if not os.path.exists(AR.IconFilePath):
        os.mkdir(AR.IconFilePath)
    AR.Selected_Category.clear()
    Load()
    catlength[0] = len(AR.Categories)
    TempSaveCats()
    TempUpdate()
    multiselection_buttons[0] = False
    oninit[0] = False

def TimerInitSavedPanel():
    InitSavedPanel()

@persistent
def TempLoadCats(dummy): #Load the Created tempfile
    AR = bpy.context.preferences.addons[__module__].preferences
    tcatpath = bpy.app.tempdir + "tempcats.json"
    AR.ar_enum.clear()
    reg = bpy.ops.screen.redo_last.poll()
    if reg:
        for cat in AR.Categories:
            RegisterUnregister_Category(ar_category.functions.get_panel_index(cat), False)
    AR.Categories.clear()
    AR.Instance_Coll.clear()
    with open(tcatpath, 'r', encoding='utf-8') as tempfile:
        data = json.load(tempfile)
        inst_coll = data["Instance_Coll"]
        for i in range(len(inst_coll)):
            inst = AR.Instance_Coll.add()
            inst.name = inst_coll[i]["name"]
            inst.icon = inst_coll[i]["icon"]
            for y in range(len(inst_coll[i]["command"])):
                cmd = inst.commands.add()
                cmd.name = inst_coll[i]["command"][y]
                cmd.maro = inst_coll[i]["macro"][y]
        index = data["Instance_Index"]
        AR.Instance_Index = index
        for i in range(len(AR.Instance_Coll)):
            new_e = AR.ar_enum.add()
            new_e.name = str(i)
            new_e.Index = i
        if len(AR.ar_enum):
            AR.ar_enum[index].Value = True
        for cat in data["Categories"]:
            new = AR.Categories.add()
            new.name = cat["name"]
            new.pn_name = cat["pn_name"]
            new.pn_show = cat["pn_show"]
            new.Instance_Start = cat["Instance_Start"]
            new.Instance_length = cat["Instance_length"]
            if reg:
                RegisterUnregister_Category(ar_category.functions.get_panel_index(new))



def AlertTimerPlay(recindex): #Remove alert after time passed for Recored
    AR = bpy.context.preferences.addons[__module__].preferences
    AR.Record_Coll[CheckCommand(0)].Command[recindex].alert = False
    for ele in AR.Record_Coll[CheckCommand(recindex + 1)].Command:
        ele.alert = False
    redrawLocalANDMacroPanels()

def AlertTimerCmd(): #Remove alert after time passed for Buttons
    Data.alert_index = None

def Inst_Coll_Insert(index, data, collection): # Insert in "Inst_Coll" Collection
    collection.add()
    for x in range(len(collection) - 1, index, -1):# go the array backwards
        collection[x].name = collection[x - 1].name
        collection[x].icon = collection[x - 1].icon
        collection[x].commands.clear()
        for command in collection[x - 1].commands:
            cmd = collection[x].commands.add()
            cmd.name = command.name
    collection[index].name = data["name"]
    collection[index].icon = check_icon(data["icon"])
    collection[index].commands.clear()
    commands = data["command"]
    macros = data["macro"]
    for i in range(len(commands)):
        cmd = collection[index].commands.add()
        cmd.name = commands[i]
        cmd.macro = macros[i]

def CreateNewProp(prop):
    name = "Edit_Command_%s" % prop.identifier
    exec("bpy.types.Scene.%s = prop" % name)
    return "bpy.context.scene.%s" % name

def DeleteProps(address):
    exec("del %s" % address)


def TimerCommads(Commands, index, offset):
    execution_queue.put(functools.partial(Play, Commands, index, offset=offset))


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
    AR = bpy.context.preferences.addons[__module__].preferences
    local = []
    for ele in AR.Record_Coll:
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
    AR = bpy.context.preferences.addons[__module__].preferences
    if replace:
        AR.Record_Coll.clear()
    for text in texts:
        if bpy.data.texts.find(text) == -1:
            continue
        text = bpy.data.texts[text]
        lines = [line.body for line in text.lines]
        Add(0, text.name)
        for line in lines:
            if line != '':
                AR = bpy.context.preferences.addons[__module__].preferences
                splitlines = line.split("#")
                Add(len(AR.Record_Coll[0].Command), "#".join(splitlines[:-1]), splitlines[-1])

def show_category(name, context):
    AR = context.preferences.addons[__module__].preferences
    if AR.ShowAllCategories:
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

def getCollectionBorderOfButtonIndex(index, AR):
    for cat in AR.Categories:
        if index < cat.Instance_Start + cat.Instance_length and index >= cat.Instance_Start:
            return (cat.Instance_Start, cat.Instance_Start + cat.Instance_length - 1)
# endregion



# region PropertyGroups
def SavePrefs(self, context):
    if not ontempload[0]:
        AR = bpy.context.preferences.addons[__module__].preferences
        TempUpdateCommand(AR.Record_Coll[0].Index + 1)

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
    cname : StringProperty(set= SetRecordName, get=GetCname) #AR.name
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

"""
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
"""

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
