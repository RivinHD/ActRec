#==============================================================
#スタートアップ
#-------------------------------------------------------------------------------------------
import bpy #Blender内部のデータ構造にアクセスするために必要
from bpy.app.handlers import persistent
import os
import shutil
import json
from json.decoder import JSONDecodeError
import zipfile
import time
from addon_utils import check, paths, enable
from .IconList import Icons as IconList

from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, EnumProperty, PointerProperty, CollectionProperty
from bpy.types import Panel, UIList, Operator, PropertyGroup, AddonPreferences
from bpy_extras.io_utils import ImportHelper, ExportHelper

classes = []
categoriesclasses = []
register = [False]
catlength = [0]


# UIList ======================================================================================
class AR_UL_Selector(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        self.use_filter_show = False
        self.use_filter_sort_lock = True
        row = layout.row()
        row.alert = item.alert
        row.operator(AR_OT_Record_Edit.bl_idname, text= item.cname, emboss= False).index = index
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

# Functions =====================================================================================

def AR_(Data , Num):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    if Data == 'List' :
        return eval('AR_Var.List_Command_{0:03d}'.format(Num))
    elif Data == 'Index' :
        return eval('AR_Var.List_Index_{0:03d}'.format(Num))
    else :
        exec('AR_Var.List_Index_{0:03d} = {1}'.format(Num,Data))

def Get_Recent(Return_Bool):#操作履歴にアクセス
    #remove other Recent Reports
    reports = \
    [
    bpy.data.texts.remove(t, do_unlink=True)
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
        return bpy.data.texts['Recent Reports'].lines#操作履歴全ての行
    elif Return_Bool == 'Reports_Length':
        return len(bpy.data.texts['Recent Reports'].lines)#操作履歴の要素数

def GetMacro(name):
    if name.startswith("bpy.ops"):
        return eval(name.split("(")[0] + ".get_rna_type().name")
    else:
        return None

def Record(Num, Mode):
    Recent = Get_Recent('Reports_All')
    if Mode == 'Start':
        AR_Prop.Record = True
        AR_Prop.Temp_Num = len(Recent)
    else:
        AR_Prop.Record = False
        notadded = []
        for i in range (AR_Prop.Temp_Num, len(Recent)):
            TempText = Recent[i-1].body
            if TempText.count('bpy'):
                name = TempText[TempText.find('bpy'):]
                macro = GetMacro(name)
                if macro is None:
                    notadded.append(name)
                else:
                    Item = AR_('List', Num).add()
                    Item.macro = macro
                    Item.cname = name
        return notadded

def CreateTempFile():
    tpath = bpy.app.tempdir + "temp.json"
    if not os.path.exists(tpath):
        print(tpath)
        with open(tpath, 'w', encoding='utf8') as tempfile:
            json.dump({"0":[]}, tempfile)
    return tpath

def TempSave(Num):  # write new command to temp.json file
    tpath = CreateTempFile()
    with open(tpath, 'r+', encoding='utf8') as tempfile:   
        data = json.load(tempfile)
        data.update({str(Num):[]})
        data["0"] = [{"name": i.cname, "macro": i.macro} for i in  AR_('List', 0)]
        tempfile.seek(0)
        json.dump(data, tempfile)

def TempUpdate(): # update all commands in temp.json file
    tpath = CreateTempFile()
    with open(tpath, 'r+', encoding='utf8') as tempfile:
        tempfile.truncate(0)
        tempfile.seek(0)
        data = {}
        for cmd in range(len(AR_('List', 0)) + 1):
            data.update({str(cmd):[{"name": i.cname, "macro": i.macro} for i in AR_('List', cmd)]})
        json.dump(data, tempfile)

def TempUpdateCommand(Key): # update one command in temp.json file
    tpath = CreateTempFile()
    with open(tpath, 'r+', encoding='utf8') as tempfile:
        data = json.load(tempfile)
        data[str(Key)] = [{"name": i.cname, "macro": i.macro} for i in AR_('List', int(Key))]
        tempfile.truncate(0)
        tempfile.seek(0)
        json.dump(data, tempfile)

@persistent
def TempLoad(dummy): # load commands after undo
    tpath = bpy.app.tempdir + "temp.json"
    if os.path.exists(tpath):
        with open(tpath, 'r', encoding='utf8') as tempfile:
            data = json.load(tempfile)
        command = AR_('List', 0)
        command.clear()
        keys = list(data.keys())
        for i in range(1, len(data)):
            Item = command.add()
            Item.macro = data["0"][i - 1]["macro"]
            Item.cname = data["0"][i - 1]["name"]
            record = AR_('List', i)
            record.clear()
            for j in range(len(data[keys[i]])):
                Item = record.add()
                Item.macro = data[keys[i]][j]["macro"]
                Item.cname = data[keys[i]][j]["name"]

def GetCommand(index):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    return eval('AR_Var.List_Command_{0:03d}'.format(index))

def Add(Num):
    Recent = Get_Recent('Reports_All')
    if Num or len(AR_('List', 0)) < 250:
        if Num:
            try:
                if Recent[-2].body.count('bpy'):
                    Name_Temp = Recent[-2].body
                else:
                    Name_Temp = Recent[-3].body
                name = Name_Temp[Name_Temp.find('bpy'):]
                macro = GetMacro(name)
                notadded = False
                if macro is None:
                    notadded = name
                else:
                    Item = AR_('List', Num).add()
                    Item.macro = macro
                    Item.cname = name
                return notadded
            except:
                return True
        else:
            Item = AR_('List', Num).add()
            Item.cname = 'Untitled_{0:03d}'.format(len(AR_('List', Num)))
        AR_( len(AR_('List',Num))-1, Num )

def Remove(Num):
    if not Num:
        for Num_Loop in range(AR_('Index',0)+1 , len(AR_('List',0))+1) :
            AR_('List',Num_Loop).clear()
            for Num_Command in range(len(AR_('List',Num_Loop+1))) :
                Item = AR_('List',Num_Loop).add()
                Item.cname = AR_('List',Num_Loop+1)[Num_Command].cname
            AR_(AR_('Index',Num_Loop+1),Num_Loop)
    if len(AR_('List',Num)):
        AR_('List',Num).remove(AR_('Index',Num))
        if len(AR_('List',Num)) - 1 < AR_('Index',Num):
            AR_(len(AR_('List',Num))-1,Num)
            if AR_('Index',Num) < 0:
                AR_(0,Num)

def Move(Num , Mode) :
    index1 = AR_('Index',Num)
    if Mode == 'Up' :
        index2 = AR_('Index',Num) - 1
    else :
        index2 = AR_('Index',Num) + 1
    LengthTemp = len(AR_('List',Num))
    if (2 <= LengthTemp) and (0 <= index1 < LengthTemp) and (0 <= index2 <LengthTemp):
        AR_('List',Num).move(index1, index2)
        AR_(index2 , Num)

        #コマンドの入れ替え処理
        if not Num :
            index1 += 1
            index2 += 1
            AR_('List',254).clear()
            #254にIndex2を逃がす
            for Num_Command in AR_('List',index2) :
                Item = AR_('List',254).add()
                Item.cname = Num_Command.cname
            AR_(AR_('Index',index2),254)
            AR_('List',index2).clear()
            #Index1からIndex2へ
            for Num_Command in AR_('List',index1) :
                Item = AR_('List',index2).add()
                Item.cname = Num_Command.cname
            AR_(AR_('Index',index1),index2)
            AR_('List',index1).clear()
            #254からIndex1へ
            for Num_Command in AR_('List',254) :
                Item = AR_('List',index1).add()
                Item.cname = Num_Command.cname
            AR_(AR_('Index',254),index1)
            AR_('List',254).clear()

def Select_Command(Mode):
    currentIndex = AR_('Index',0)
    listlen = len(AR_('List',0)) - 1
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    if Mode == 'Up':
        if currentIndex == 0:
            AR_Var.List_Index_000 = listlen
        else:
            AR_Var.List_Index_000 = currentIndex - 1
    else:
        if currentIndex == listlen:
            AR_Var.List_Index_000 = 0
        else:
            AR_Var.List_Index_000 = currentIndex + 1

def Play(Commands):
    for Command in Commands:
        if Command.active:
            try:
                exec(Commands.cname)
            except:
                Command.alert = True
                return True # Alert

def Clear(Num) :
    AR_('List',Num).clear()

def Save():
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    for savedfolder in os.listdir(path):
        folderpath = os.path.join(path, savedfolder)
        for savedfile in os.listdir(folderpath):
            os.remove(os.path.join(folderpath, savedfile))
        os.rmdir(folderpath)
    for cat in AR_Var.Categories:
        panelpath = os.path.join(path, f"{GetPanelIndex(cat)}~" + cat.pn_name)
        os.mkdir(panelpath)
        start = cat.Instance_Start
        for cmd_i in range(start, start + cat.Instance_length):
            with open(os.path.join(panelpath, f"{cmd_i - start}~" + AR_Var.Instance_Coll[cmd_i].name + "~" + AR_Var.Instance_Coll[cmd_i].icon + ".txt"), 'w', encoding='utf8') as cmd_file:
                for cmd in AR_Var.Instance_Coll[cmd_i].command:
                    cmd_file.write(cmd.name + "\n")

def Load():
    print('------------------Load-----------------')
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    scene = bpy.context.scene
    for cat in AR_Var.Categories:
        RegisterUnregister_Category(GetPanelIndex(cat), False)
    AR_Var.Categories.clear()
    scene.ar_enum.clear()
    AR_Var.Instance_Coll.clear()
    for folder in os.listdir(path):
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
            if register[0]:
                RegisterUnregister_Category(GetPanelIndex(new))
            for i in textfiles:
                new_e = scene.ar_enum.add()
                e_index = len(scene.ar_enum) - 1
                new_e.name = str(e_index)
                new_e.Index = e_index
            for txt in textfiles:
                sortedtxt[int(txt.split('~')[0])] = txt #remove the .txtending, join to string again, get the index ''.join(txt.split('.')[:-1])
            for i in range(len(sortedtxt)):
                txt = sortedtxt[i]
                inst = AR_Var.Instance_Coll.add()
                inst.name = "".join(txt.split('~')[1:-1])
                inst.icon = os.path.splitext(txt)[0].split('~')[-1]
                CmdList = []
                with open(os.path.join(folderpath, txt), 'r', encoding='utf8') as text:
                    for line in text.readlines():
                        cmd = inst.command.add()
                        cmd.name = line.strip()
    SetEnumIndex()
    
def Recorder_to_Instance(panel):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    scene = bpy.context.scene
    i = panel.Instance_Start +  panel.Instance_length
    data = {"name":CheckForDublicates([ele.name for ele in AR_Var.Instance_Coll], AR_('List',0)[AR_('Index',0)].cname),
            "command": [Command.cname for Command in AR_('List',AR_('Index',0)+1)],
            "icon": 'BLANK1'}
    Inst_Coll_Insert(i, data , AR_Var.Instance_Coll)
    panel.Instance_length += 1
    new_e = scene.ar_enum.add()
    e_index = len(scene.ar_enum) - 1
    new_e.name = str(e_index)
    new_e.Index = e_index
    p_i = GetPanelIndex(panel)
    categories = AR_Var.Categories
    if p_i < len(categories):
        for cat in categories[ p_i + 1: ]:
            cat.Instance_Start += 1

def Instance_to_Recorder():
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    Item = AR_('List' , 0 ).add()
    Item.cname = AR_Var.Instance_Coll[AR_Var.Instance_Index].name
    for Command in AR_Var.Instance_Coll[AR_Var.Instance_Index].command:
        Item = AR_('List' , len(AR_('List',0)) ).add()
        Item.macro = GetMacro(Command.name)
        Item.cname = Command.name
    AR_( len(AR_('List',0))-1 , 0 )

def Execute_Instance(Num):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    for cmd in AR_Var.Instance_Coll[Num].command:
        try:
            exec(cmd.name)
        except:
            return True # Alert

def Rename_Instance():
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    AR_Var.Instance_Coll[AR_Var.Instance_Index].name = AR_Var.Rename

def I_Remove():
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    scene = bpy.context.scene
    if len(AR_Var.Instance_Coll) :
        Index = AR_Var.Instance_Index
        AR_Var.Instance_Coll.remove(Index)
        scene.ar_enum.remove(len(scene.ar_enum) - 1)
        categories = AR_Var.Categories
        for cat in categories:
            if Index >= cat.Instance_Start and Index < cat.Instance_Start + cat.Instance_length:
                cat.Instance_length -= 1
                p_i = GetPanelIndex(cat)
                if p_i < len(categories):
                    for cat in categories[ p_i + 1: ]:
                        cat.Instance_Start -= 1
                break
        if len(AR_Var.Instance_Coll) and len(AR_Var.Instance_Coll)-1 < Index :
            AR_Var.Instance_Index = len(AR_Var.Instance_Coll)-1
    SetEnumIndex()

def I_Move(Mode):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    scene = bpy.context.scene
    index1 = AR_Var.Instance_Index
    if Mode == 'Up' :
        index2 = AR_Var.Instance_Index - 1
    else :
        index2 = AR_Var.Instance_Index + 1
    LengthTemp = len(AR_Var.Instance_Coll)
    if (2 <= LengthTemp) and (0 <= index1 < LengthTemp) and (0 <= index2 <LengthTemp):
        AR_Var.Instance_Coll[index1].name , AR_Var.Instance_Coll[index2].name = AR_Var.Instance_Coll[index2].name , AR_Var.Instance_Coll[index1].name
        AR_Var.Instance_Coll[index1].icon , AR_Var.Instance_Coll[index2].icon = AR_Var.Instance_Coll[index2].icon , AR_Var.Instance_Coll[index1].icon
        index1cmd = [cmd.name for cmd in AR_Var.Instance_Coll[index1].command]
        index2cmd = [cmd.name for cmd in AR_Var.Instance_Coll[index2].command]
        AR_Var.Instance_Coll[index1].command.clear()
        AR_Var.Instance_Coll[index2].command.clear()
        for cmd in index1cmd:
            new = AR_Var.Instance_Coll[index1].command.add()
            new.name = cmd
        for cmd in index2cmd:
            new = AR_Var.Instance_Coll[index2].command.add()
            new.name = cmd
        scene.ar_enum[index2].Value = True

path = os.path.join(os.path.dirname(__file__), "Storage")
#Initalize Standert Button List
@persistent
def InitSavedPanel(scene):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    bpy.app.handlers.depsgraph_update_pre.remove(InitSavedPanel)
    if not os.path.exists(path):
        os.mkdir(path)
    if len(scene.ar_enum):
        catlength[0] = len(AR_Var.Categories)
        RegisterCategories()
    else: 
        Load()
        catlength[0] = len(AR_Var.Categories)
        AR_Var.Loaded = True
    TempSaveCats()

def GetPanelIndex(cat):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    for i in range(len(AR_Var.Categories)):
        if AR_Var.Categories[i] == cat:
            return i

def SetEnumIndex():
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    scene = bpy.context.scene
    if len(scene.ar_enum):
        enumIndex = AR_Var.Instance_Index * (AR_Var.Instance_Index < len(scene.ar_enum))
        scene.ar_enum[enumIndex].Value = True
        AR_Var.Instance_Index = enumIndex  

def CreateTempCats():
    tcatpath = bpy.app.tempdir + "tempcats.json"
    if not os.path.exists(tcatpath):
        with open(tcatpath, 'x', encoding='utf8') as tempfile:
            print(tcatpath)
    return tcatpath

def TempSaveCats():
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    scene = bpy.context.scene
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
                "command": [cmd.name for cmd in inst.command]
            })
        data = {
            "Instance_Index": AR_Var.Instance_Index,
            "Categories": cats,
            "Instance_Coll": insts
        }
        json.dump(data, tempfile)

@persistent
def TempLoadCats(dummy):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    scene = bpy.context.scene
    tcatpath = bpy.app.tempdir + "tempcats.json"
    scene.ar_enum.clear()
    reg = bpy.ops.screen.redo_last.poll()
    if reg:
        for cat in AR_Var.Categories:
            RegisterUnregister_Category(GetPanelIndex(cat), False)
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
        index = data["Instance_Index"]
        AR_Var.Instance_Index = index
        for i in range(len(AR_Var.Instance_Coll)):
            new_e = scene.ar_enum.add()
            new_e.name = str(i)
            new_e.Index = i
        scene.ar_enum[index].Value = True
        for cat in data["Categories"]:
            new = AR_Var.Categories.add()
            new.name = cat["name"]
            new.pn_name = cat["pn_name"]
            new.pn_show = cat["pn_show"]
            new.Instance_Start = cat["Instance_Start"]
            new.Instance_length = cat["Instance_length"]
            if reg:
                RegisterUnregister_Category(GetPanelIndex(new))

def CheckForDublicates(l, name, num = 1):
    if name in l:
        return CheckForDublicates(l, name.split(".")[0] +".{0:03d}".format(num), num + 1)
    return name

def AlertTimerPlay():
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    btnlist = AR_Var.List_Command_000
    for i in range(len(btnlist)):
        if btnlist[i].alert:
            btnlist[i].alert = False
            for ele in GetCommand(i + 1):
                if ele.alert:
                    ele.alert = False
                    return 

def AlertTimerCmd():
    alert_index[0] = None

def Inst_Coll_Insert(index, data, collection):
    collection.add()
    for x in range(len(collection) - 1, index, -1):# go the array backwards
        collection[x].name = collection[x - 1].name
        collection[x].icon = collection[x - 1].icon
        collection[x].command.clear()
        for command in collection[x - 1].command:
            cmd = collection[x].command.add()
            cmd.name = command.name
    collection[index].name = data["name"]
    collection[index].icon = data["icon"]
    collection[index].command.clear()
    for command in data["command"]:
        cmd = collection[index].command.add()
        cmd.name = command

# Panels ===================================================================================
def panelFactory(spaceType):

    class AR_PT_Local(Panel):
        bl_space_type = spaceType
        bl_region_type = 'UI'
        bl_category = 'Action Recorder'
        bl_label = 'Local'
        bl_idname = "AR_PT_Local_%s" % spaceType

        '''def draw_header(self, context):
            self.layout.label(text = '', icon = 'REC')'''
        #メニューの描画処理
        def draw(self, context):
            AR_Var = context.preferences.addons[__package__].preferences
            scene = bpy.context.scene
            layout = self.layout
            box = layout.box()
            box_row = box.row()
            col = box_row.column()
            col.template_list('AR_UL_Selector' , '' , AR_Var , 'List_Command_000' , AR_Var , 'List_Index_000', rows=4, sort_lock= True)
            col = box_row.column()
            col.operator(AR_OT_Record_Add.bl_idname , text='' , icon='ADD' )
            col.operator(AR_OT_Record_Remove.bl_idname , text='' , icon='REMOVE' )
            col.operator(AR_OT_Record_MoveUp.bl_idname , text='' , icon='TRIA_UP' )
            col.operator(AR_OT_Record_MoveDown.bl_idname , text='' , icon='TRIA_DOWN' )
    AR_PT_Local.__name__ = "AR_PT_Local_%s" % spaceType
    classes.append(AR_PT_Local)

    class AR_PT_MacroEditer(Panel):
        bl_space_type = spaceType
        bl_region_type = 'UI'
        bl_category = 'Action Recorder'
        bl_label = 'Macro Editor'
        bl_idname = "AR_PT_MacroEditer_%s" % spaceType

        def draw(self, context):
            AR_Var = context.preferences.addons[__package__].preferences
            scene = context.scene
            layout = self.layout
            box = layout.box()
            box_row = box.row()
            col = box_row.column()
            col.template_list('AR_UL_Command' , '' , AR_Var , 'List_Command_{0:03d}'.format(AR_('Index',0)+1) , AR_Var , 'List_Index_{0:03d}'.format(AR_('Index',0)+1), rows=4)
            col = box_row.column()
            if not AR_Prop.Record :
                col2 = col.column(align= True)
                col2.operator(AR_OT_Command_Add.bl_idname , text='' , icon='ADD' )
                col2.operator(AR_OT_Command_Remove.bl_idname , text='' , icon='REMOVE' )
                col2 = col.column(align= True)
                col2.operator(AR_OT_Command_MoveUp.bl_idname , text='' , icon='TRIA_UP' )
                col2.operator(AR_OT_Command_MoveDown.bl_idname , text='' , icon='TRIA_DOWN' )
            #----------------------------------------
            row = layout.row()
            if AR_Prop.Record :
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
                row.prop(AR_Var, 'RecToBtn_Mode', expand= True)
    AR_PT_MacroEditer.__name__ = "AR_PT_MacroEditer_%s" % spaceType
    classes.append(AR_PT_MacroEditer)
    
    class AR_PT_Global(Panel):
        bl_space_type = spaceType
        bl_region_type = 'UI'
        bl_category = 'Action Recorder'
        bl_label = 'Global'
        bl_idname = "AR_PT_Global_%s" % spaceType

        def draw_header(self, context):
            AR_Var = context.preferences.addons[__package__].preferences
            layout = self.layout
            row = layout.row(align= True)
            row.prop(AR_Var, 'HideMenu', icon= 'COLLAPSEMENU', text= "", emboss= True)
            row.operator(AR_OT_Global_Settings.bl_idname, text= "", icon= 'PREFERENCES', emboss= True)

        def draw(self, context):
            AR_Var = context.preferences.addons[__package__].preferences
            scene = bpy.context.scene
            layout = self.layout
            if not AR_Var.HideMenu:
                box = layout.box()
                col = box.column(align= True)
                if not AR_Var.Autosave:
                    col.operator(AR_OT_Save.bl_idname , text='Save to File' )
                    col.operator(AR_OT_Load.bl_idname , text='Load from File' )
                col = box.column(align= True)
                col.operator(AR_OT_Import.bl_idname, text= 'Import')
                col.operator(AR_OT_Export.bl_idname, text= 'Export')
                row = col.row()
                row.scale_y = 2
                row.operator(AR_OT_ButtonToRecord.bl_idname, text='Global to Local' )
                row = col.row(align= True)
                row.prop(AR_Var, 'BtnToRec_Mode', expand= True)
                row = box.row().split(factor= 0.4)
                row.label(text= 'Category')
                row2 = row.row(align= True)
                row2.scale_x = 1.1737
                row2.operator(AR_OT_Category_Add.bl_idname, text= '', icon= 'ADD')
                row2.operator(AR_OT_Category_Rename.bl_idname, text= '', icon= 'GREASEPENCIL')
                row2.operator(AR_OT_Category_Delet.bl_idname, text= '', icon= 'TRASH')
                row = box.row().split(factor= 0.4)
                row.label(text= 'Buttons')
                row2 = row.row(align= True)
                row2.operator(AR_OT_Button_MoveUp.bl_idname , text='' , icon='TRIA_UP' )
                row2.operator(AR_OT_Button_MoveDown.bl_idname , text='' , icon='TRIA_DOWN' )
                row2.operator(AR_OT_Category_MoveButton.bl_idname, text= '', icon= 'PRESET')
                row2.operator(AR_OT_Button_Remove.bl_idname, text='' , icon='TRASH' )
                row = box.row()
                row2 = row.split(factor= 0.7)
                col = row2.column()
                col.enabled = len(AR_Var.Instance_Coll) > 0
                col.prop(AR_Var , 'Rename' , text='')
                row2.operator(AR_OT_Button_Rename.bl_idname , text='Rename')
    AR_PT_Global.__name__ = "AR_PT_Global_%s" % spaceType
    classes.append(AR_PT_Global)

def RegisterCategories():
    for i in range(catlength[0]):
        RegisterUnregister_Category(i)

def RegisterUnregister_Category(index, register = True):
    for spaceType in spaceTypes:
        class AR_PT_Category(Panel):
            bl_space_type = spaceType
            bl_region_type = 'UI'
            bl_category = 'Action Recorder'
            bl_label = ' '
            bl_idname = "AR_PT_Category_%s_%s" %(index, spaceType)
            bl_parent_id = "AR_PT_Global_%s" % spaceType
            bl_order = index + 1

            def draw_header(self, context):
                AR_Var = context.preferences.addons[__package__].preferences
                index = int(self.bl_idname.split("_")[3])
                category = AR_Var.Categories[index]
                layout = self.layout
                row = layout.row()
                row.alignment = 'LEFT'
                row.label(text= category.pn_name)
                row2 = row.row(align= True)
                row2.operator(AR_OT_Category_MoveUp.bl_idname, icon="TRIA_UP", text= "").Index = index
                row2.operator(AR_OT_Category_MoveDown.bl_idname, icon="TRIA_DOWN", text="").Index = index

            def draw(self, context):
                AR_Var = context.preferences.addons[__package__].preferences
                scene = context.scene
                index = int(self.bl_idname.split("_")[3])
                category = AR_Var.Categories[index]
                layout = self.layout
                col = layout.column()
                for i in range(category.Instance_Start, category.Instance_Start + category.Instance_length):
                    row = col.row(align=True)
                    row.alert = alert_index[0] == i
                    row.prop(scene.ar_enum[i], 'Value' ,toggle = 1, icon= 'DECORATE_KEYFRAME' if scene.ar_enum[i].Value else 'DECORATE_ANIMATE', text= "")
                    row.operator(AR_OT_Category_Cmd_Icon.bl_idname, text= "", icon= AR_Var.Instance_Coll[i].icon).index = i
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

# Opertators ===============================================================================
class AR_OT_Category_Add(Operator):
    bl_idname = "ar.category_add"
    bl_label = "Add Category"

    Name : StringProperty(name = "Name", default="")

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        scene = context.scene
        new = AR_Var.Categories.add()
        new.name = self.Name
        new.pn_name = self.Name
        new.Instance_Start = len(AR_Var.Instance_Coll)
        new.Instance_length = 0
        bpy.context.area.tag_redraw()
        TempSaveCats()
        RegisterUnregister_Category(GetPanelIndex(new))
        if AR_Var.Autosave:
            Save()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'Name')         
classes.append(AR_OT_Category_Add)

class AR_OT_Category_Delet(Operator):
    bl_idname = "ar.category_delet"
    bl_label = "Delet Category"
    bl_description = "Delete the selected Category"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Categories)

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        categories = AR_Var.Categories
        scene = context.scene
        for cat in categories:
            if cat.pn_selected:
                index = GetPanelIndex(cat)
                start = cat.Instance_Start
                for i in range(start, start + cat.Instance_length):
                    scene.ar_enum.remove(len(scene.ar_enum) - 1)
                    AR_Var.Instance_Coll.remove(start)
                for nextcat in categories[index + 1 :]:
                    nextcat.Instance_Start -= cat.Instance_length
                categories.remove(index)
                RegisterUnregister_Category(len(categories), False)
                SetEnumIndex()
                break
        bpy.context.area.tag_redraw()
        TempSaveCats()
        if AR_Var.Autosave:
            Save()
        return {"FINISHED"}
    
    def draw(self, context):    
        AR_Var = context.preferences.addons[__package__].preferences    
        layout = self.layout
        categories = AR_Var.Categories
        for cat in categories:
            layout.prop(cat, 'pn_selected', text= cat.pn_name)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
classes.append(AR_OT_Category_Delet)

class AR_OT_Category_Rename(Operator):
    bl_idname = "ar.category_rename"
    bl_label = "Rename Category"
    bl_description = "Rename the selected Category"

    PanelName : StringProperty(name = "New Name", default="")

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Categories)

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        categories = AR_Var.Categories
        for cat in categories:
            if cat.pn_selected:
                cat.name = self.PanelName
                cat.pn_name = self.PanelName
                break
        bpy.context.area.tag_redraw()
        TempSaveCats()
        if AR_Var.Autosave:
            Save()
        return {"FINISHED"}

    def draw(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        layout = self.layout
        categories = AR_Var.Categories
        for cat in categories:
            layout.prop(cat, 'pn_selected', text= cat.pn_name)
        layout.prop(self, 'PanelName')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
classes.append(AR_OT_Category_Rename)

class AR_OT_Category_MoveButton(Operator):
    bl_idname = "ar.category_move_category_button"
    bl_label = "Move Button"
    bl_description = "Moves the selected Button of a Category to another Category"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Instance_Coll)

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        categories = AR_Var.Categories
        scene = context.scene
        for cat in categories:
            if cat.pn_selected:
                Index = AR_Var.Instance_Index
                catendl = cat.Instance_Start + cat.Instance_length
                for curcat in categories:
                    if Index >= curcat.Instance_Start and Index < curcat.Instance_Start + curcat.Instance_length:
                        curcat.Instance_length -= 1
                        for nextcat in categories[GetPanelIndex(curcat) + 1 :]:
                            nextcat.Instance_Start -= 1
                        break
                data ={
                    "name": AR_Var.Instance_Coll[Index].name,
                    "icon": AR_Var.Instance_Coll[Index].icon,
                    "command": [cmd.name for cmd in AR_Var.Instance_Coll[Index].command]
                }
                AR_Var.Instance_Coll.remove(Index)
                Inst_Coll_Insert(catendl -1 * (Index < catendl), data, AR_Var.Instance_Coll)
                for nextcat in categories[GetPanelIndex(cat) + 1:]:
                    nextcat.Instance_Start += 1
                cat.Instance_length += 1
                SetEnumIndex()
                break
        bpy.context.area.tag_redraw()
        TempSaveCats()
        if AR_Var.Autosave:
            Save()
        return {"FINISHED"}

    def draw(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        categories = AR_Var.Categories
        layout = self.layout
        for cat in categories:
            layout.prop(cat, 'pn_selected', text= cat.pn_name)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
classes.append(AR_OT_Category_MoveButton)

class AR_OT_Category_MoveUp(Operator):
    bl_idname = "ar.category_move_up"
    bl_label = "Move Up"
    bl_description = "Move the Category up"

    Index : IntProperty()

    def invoke(self, context, event):
        AR_Var = context.preferences.addons[__package__].preferences
        i = self.Index
        categories = AR_Var.Categories
        if i - 1 >= 0:
            cat1 = categories[i]
            cat2 = categories[i - 1]
            cat1.name, cat2.name = cat2.name, cat1.name
            cat1.pn_name, cat2.pn_name = cat2.pn_name, cat1.pn_name
            cat1.pn_show, cat2.pn_show = cat2.pn_show, cat1.pn_show
            cat1.pn_selected, cat2.pn_selected = cat2.pn_selected, cat1.pn_selected
            cat1.Instance_Start, cat2.Instance_Start = cat2.Instance_Start, cat1.Instance_Start
            cat1.Instance_length, cat2.Instance_length = cat2.Instance_length, cat1.Instance_length
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
        if i + 1 < len(categories):
            cat1 = categories[i]
            cat2 = categories[i + 1]
            cat1.name, cat2.name = cat2.name, cat1.name
            cat1.pn_name, cat2.pn_name = cat2.pn_name, cat1.pn_name
            cat1.pn_show, cat2.pn_show = cat2.pn_show, cat1.pn_show
            cat1.pn_selected, cat2.pn_selected = cat2.pn_selected, cat1.pn_selected
            cat1.Instance_Start, cat2.Instance_Start = cat2.Instance_Start, cat1.Instance_Start
            cat1.Instance_length, cat2.Instance_length = cat2.Instance_length, cat1.Instance_length
        bpy.context.area.tag_redraw()
        TempSaveCats()
        if AR_Var.Autosave:
            Save()
        return {"FINISHED"}
classes.append(AR_OT_Category_MoveDown)

class AR_OT_RecordToButton(Operator):
    bl_idname = "ar.record_record_to_button"
    bl_label = "Record to Button"
    bl_description = "Add the selectd Record to a Category"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.List_Command_000)

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        categories = AR_Var.Categories
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

    def draw(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        categories = AR_Var.Categories
        layout = self.layout
        for cat in categories:
            layout.prop(cat, 'pn_selected', text= cat.pn_name)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
classes.append(AR_OT_RecordToButton)

class AR_OT_Import(Operator, ImportHelper):
    bl_idname = "ar.data_import"
    bl_label = "Import"

    filter_glob: StringProperty( default='*.zip', options={'HIDDEN'} )
    files : CollectionProperty(type= PropertyGroup)

    Category : StringProperty(default= "Imports")
    AddNewCategory : BoolProperty(default= False)

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        scene = context.scene
        ar_categories = AR_Var.Categories
        if self.filepath.endswith(".zip"):
            with zipfile.ZipFile(self.filepath, 'r') as zip_out:
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
                    new_i = int(dirlist[i].split("~")[0])
                    sorteddirlist[new_i] = dirlist[i]
                    dirfileslist[new_i], dirfileslist[i] = dirfileslist[i], dirfileslist[new_i]
                    sortedfilelist = [None] * len(dirfileslist[new_i])
                    for fil in dirfileslist[new_i]:
                        sortedfilelist[int(os.path.basename(fil).split("~")[0])] = fil
                    dirfileslist[new_i] = sortedfilelist
                    
                if self.AddNewCategory:
                    mycat = ar_categories.add()
                    mycat.name = self.Category
                    mycat.pn_name = self.Category
                    mycat.Instance_Start = len(AR_Var.Instance_Coll)
                    RegisterUnregister_Category(GetPanelIndex(mycat))
                    for dirs in dirfileslist:
                        for btn_file in dirs:
                            name = "".join(os.path.splitext(os.path.basename(btn_file))[0].split("~")[1:])
                            inst = AR_Var.Instance_Coll.add()
                            inst.name = CheckForDublicates([ele.name for ele in AR_Var.Instance_Coll], name)
                            for line in zip_out.read(btn_file).decode("utf-8").splitlines():
                                cmd = inst.command.add()
                                cmd.name = line
                            new_e = scene.ar_enum.add()
                            e_index = len(scene.ar_enum) - 1
                            new_e.name = str(e_index)
                            new_e.Index = e_index
                            mycat.Instance_length += 1
                else:
                    for i in range(len(sorteddirlist)):
                        Index = None
                        mycat = None
                        for cat in ar_categories:
                            if cat.pn_name == "".join(sorteddirlist[i].split("~")[1:]):
                                Index = GetPanelIndex(cat)
                                break
                        if Index is None:
                            mycat = ar_categories.add()
                            name = "".join(sorteddirlist[i].split("~")[1:])
                            mycat.name = name
                            mycat.pn_name = name
                            mycat.Instance_Start = len(AR_Var.Instance_Coll)
                            RegisterUnregister_Category(GetPanelIndex(mycat))
                        else:
                            mycat = ar_categories[Index]
                        
                        for dir_file in dirfileslist[i]:
                            inserti = mycat.Instance_Start + mycat.Instance_length
                            name = "".join(os.path.splitext(os.path.basename(dir_file))[0].split("~")[1:])
                            data = {"name": CheckForDublicates([ele.name for ele in AR_Var.Instance_Coll], name),
                                    "command": zip_out.read(dir_file).decode("utf-8").splitlines(),
                                    "icon": 'BLANK1'}
                            Inst_Coll_Insert(inserti, data, AR_Var.Instance_Coll)
                            new_e = scene.ar_enum.add()
                            e_index = len(scene.ar_enum) - 1
                            new_e.name = str(e_index)
                            new_e.Index = e_index
                            mycat.Instance_length += 1
                            if Index is not None:
                                for cat in ar_categories[Index + 1:] :
                                    cat.Instance_Start += 1
            SetEnumIndex()
            if AR_Var.Autosave:
                Save()
        else:
            self.report({'ERROR'}, "{ " + path + " } Select a .zip file")
        return {"FINISHED"}
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'AddNewCategory', text= "Create new Category")
        if self.AddNewCategory:
            layout.prop(self, 'Category', text= "Name")
classes.append(AR_OT_Import)

class AR_OT_Export(Operator, ExportHelper):
    bl_idname = "ar.data_export"
    bl_label = "Export"

    filter_glob: StringProperty( default='*.zip', options={'HIDDEN'} )
    filename_ext = ".zip"
    filepath : StringProperty (name = "File Path", maxlen = 1024, default = "ComandRecorderButtons")

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
                if cat.pn_selected:
                    written = True
                    for i in range(cat.FileDisp_Start, cat.FileDisp_Start + cat.FileDisp_length):
                        path = os.path.join(folderpath, f"{i}~" + AR_Prop.FileDisp_Name[i] + ".py")
                        with open(path, 'w', encoding='utf8') as recfile:
                            for cmd in AR_Prop.FileDisp_Command[i]:
                                recfile.write(cmd + '\n')
                        zip_it.write(path, os.path.join(f"{catindex}~" + cat.pn_name, f"{i - cat.FileDisp_Start}~"+ AR_Prop.FileDisp_Name[i] + ".py"))
                        os.remove(path)
                else:
                    index = 0
                    for i in range(cat.FileDisp_Start, cat.FileDisp_Start + cat.FileDisp_length):
                        if scene.ar_filedisp[i].Index:
                            written = True
                            path = os.path.join(folderpath, f"{index}~" + AR_Prop.FileDisp_Name[i] + ".py")
                            with open(path, 'w', encoding='utf8') as recfile:
                                for cmd in AR_Prop.FileDisp_Command[i]:
                                    recfile.write(cmd + '\n')
                            zip_it.write(path, os.path.join(f"{catindex}~" + cat.pn_name, f"{index}~" + AR_Prop.FileDisp_Name[i] + ".py"))
                            os.remove(path)
                            index += 1
                if written:
                    catindex += 1
                    written = False
                os.rmdir(folderpath)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
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
                    if cat.pn_selected:
                        row2 = col.row()
                        for i in range(cat.FileDisp_Start, cat.FileDisp_Start + cat.FileDisp_length):
                            col.label(text= AR_Prop.FileDisp_Name[i], icon= 'CHECKBOX_HLT')
                    else:
                        for i in range(cat.FileDisp_Start, cat.FileDisp_Start + cat.FileDisp_length):
                            col.prop(scene.ar_filedisp[i], 'Index' , text= AR_Prop.FileDisp_Name[i])
    
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
        AR_Prop.FileDisp_Name.clear()
        AR_Prop.FileDisp_Command.clear()
        for inst in AR_Var.Instance_Coll:
            AR_Prop.FileDisp_Name.append(inst.name)
            AR_Prop.FileDisp_Command.append([cmd.name for cmd in inst.command])
        scene.ar_filedisp.clear()
        for i in range(len(scene.ar_enum)):
            scene.ar_filedisp.add()
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
classes.append(AR_OT_Export)

class AR_OT_Record_Add(Operator):
    bl_idname = "ar.record_add"
    bl_label = "Add"
    bl_description = "Add a new Record"

    def execute(self, context):
        scene = context.scene
        Add(0)
        TempSave(AR_('Index',0) + 1)
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_Record_Add)

class AR_OT_Record_Remove(Operator):
    bl_idname = "ar.record_remove"
    bl_label = "Remove"
    bl_description = "Remove the selected Record"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.List_Command_000)

    def execute(self, context):
        scene = context.scene
        Remove(0)
        TempUpdate()
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_Record_Remove)

class AR_OT_Record_MoveUp(Operator):
    bl_idname = "ar.record_move_up"
    bl_label = "Move Up"
    bl_description = "Move the selected Record up"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.List_Command_000)

    def execute(self, context):
        scene = context.scene
        Move(0 , 'Up')
        TempUpdate()
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_Record_MoveUp)

class AR_OT_Record_MoveDown(Operator):
    bl_idname = "ar.record_move_down"
    bl_label = "Move Down"
    bl_description = "Move the selected Record down"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.List_Command_000)
        
    def execute(self, context):
        scene = context.scene
        Move(0 , 'Down')
        TempUpdate()
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_Record_MoveDown)

class AR_OT_Save(Operator):
    bl_idname = "ar.data_save"
    bl_label = "Save"
    bl_description = "Save all data to the disk (delete the old data from the disk)"

    def execute(self, context):
        Save()
        return {"FINISHED"}
classes.append(AR_OT_Save)

class AR_OT_Load(Operator):
    bl_idname = "ar.data_load"
    bl_label = "Load"
    bl_description = "Load all data from the disk (delete the current data in Blender)"

    def execute(self, context):
        Load()
        TempSaveCats()
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_Load)

class AR_OT_ButtonToRecord(Operator):
    bl_idname = "ar.category_button_to_record"
    bl_label = "Button to Record"
    bl_description = "Load the selected Button as a Record"

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
        return {"FINISHED"}
classes.append(AR_OT_ButtonToRecord)

class AR_OT_Button_Remove(Operator):
    bl_idname = "ar.category_remove_button"
    bl_label = "Remove Button"
    bl_description = "Remove the selected Button"

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
    bl_description = "Move the selected Button up"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Instance_Coll)

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
    bl_label = "Move Button Down"
    bl_description = "Move the selected Button down"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.Instance_Coll)
        
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
        return len(AR_Var.Instance_Coll)

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        Rename_Instance()
        TempSaveCats()
        bpy.context.area.tag_redraw()
        if AR_Var.Autosave:
            Save()
        return {"FINISHED"}
classes.append(AR_OT_Button_Rename)

alert_index = [None]
class AR_OT_Category_Cmd(Operator):
    bl_idname = 'ar.category_cmd_button'
    bl_label = 'ComRec Command'
    bl_options = {'UNDO', 'INTERNAL'}

    Index : IntProperty()

    def execute(self, context):
        if Execute_Instance(self.Index):
            alert_index[0] = self.Index
            bpy.app.timers.register(AlertTimerCmd, first_interval = 2)
        return{'FINISHED'}
classes.append(AR_OT_Category_Cmd)

class AR_OT_Category_Cmd_Icon(bpy.types.Operator):
    bl_idname = "ar.category_cmd_icon"
    bl_label = "Icons"
    bl_description = "Press to select an Icon"

    index : IntProperty()

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        AR_Var.Instance_Coll[self.index].icon = AR_Prop.SelectedIcon
        AR_Prop.SelectedIcon = "BLANK1"
        return {"FINISHED"}
    
    def draw(self, execute):
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.label(text= "Selected Icon:")
        row.label(text=" ", icon= AR_Prop.SelectedIcon)
        row.operator(AR_OT_Category_Icon.bl_idname, text= "Clear Icon").icon = "BLANK1"
        box = layout.box()
        gridf = box.grid_flow(row_major=True, columns= 35, even_columns= True,  even_rows= True, align= True)
        for ic in IconList:
            gridf.operator(AR_OT_Category_Icon.bl_idname, text= "", icon= ic).icon = ic

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=1000)
classes.append(AR_OT_Category_Cmd_Icon)

class AR_OT_Category_Icon(Operator):
    bl_idname = "ar.category_icon"
    bl_label = "Icon"
    bl_options = {'REGISTER','INTERNAL'}

    icon : StringProperty(default= "BLANK1")

    def execute(self, context):
        AR_Prop.SelectedIcon = self.icon
        return {"FINISHED"}
classes.append(AR_OT_Category_Icon)

class AR_OT_Record_SelectorUp(Operator):
    bl_idname = 'ar.record_selector_up'
    bl_label = 'Action Recorder Selection Up'

    def execute(self, context):
        Select_Command('Up')
        bpy.context.area.tag_redraw()
        return{'FINISHED'}
classes.append(AR_OT_Record_SelectorUp)

class AR_OT_Record_SelectorDown(Operator):
    bl_idname = 'ar.record_selector_down'
    bl_label = 'Action Recorder Selection Down'

    def execute(self, context):
        Select_Command('Down')
        bpy.context.area.tag_redraw()
        return{'FINISHED'}
classes.append(AR_OT_Record_SelectorDown)

class AR_OT_Record_Play(Operator):
    bl_idname = 'ar.record_play'
    bl_label = 'Action Recorder Play'
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(eval("AR_Var.List_Command_{0:03d}".format(AR_Var.List_Index_000 + 1)))

    def execute(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        index = AR_('Index',0)
        alert = Play(AR_('List', index + 1))
        if alert:
            AR_Var.List_Command_000[index].alert = True
            bpy.app.timers.register(AlertTimerPlay, first_interval = 2)
        return{'FINISHED'}
classes.append(AR_OT_Record_Play)

class AR_OT_Record_Start(Operator):
    bl_idname = "ar.record_start"
    bl_label = "Start Recording"
    bl_description = "starts recording the actions"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.List_Command_000)

    def execute(self, context):
        scene = bpy.context.scene
        Record(AR_('Index',0)+1 , 'Start')
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_Record_Start)

class AR_OT_Record_Stop(Operator):
    bl_idname = "ar.record_stop"
    bl_label = "Stop Recording"
    bl_description = "stops recording the actions"

    def execute(self, context):
        scene = bpy.context.scene
        messages = Record(AR_('Index',0)+1 , 'Stop')
        if len(messages):
            mess = "\n    "
            for message in messages:
                mess += "%s \n    " %message
            self.report({'ERROR'}, "Not all actions were added because they are not of type Operator: %s" % mess)
        TempUpdateCommand(AR_('Index',0)+1)
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_Record_Stop)

class AR_OT_Command_Add(Operator):
    bl_idname = "ar.command_add"
    bl_label = "Action Recorder Add Command"
    bl_description = "Add a Command to the selected Record"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(AR_Var.List_Command_000)

    def execute(self, context):
        scene = context.scene
        message = Add(AR_('Index',0)+1)
        if type(message) == str:
            self.report({'ERROR'}, "Action could not be added because it is not of type Operator:\n %s" % message)
        elif message:
            self.report({'ERROR'}, "No Action could be added")
        TempUpdateCommand(AR_('Index',0)+1)
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_Command_Add)

class AR_OT_Command_Remove(Operator):
    bl_idname = "ar.command_remove"
    bl_label = "Remove Command"
    bl_description = "Remove the selected Command"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(eval("AR_Var.List_Command_{0:03d}".format(AR_Var.List_Index_000 + 1)))

    def execute(self, context):
        scene = context.scene
        Remove(AR_('Index',0)+1)
        TempUpdateCommand(AR_('Index',0)+1)
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_Command_Remove)

class AR_OT_Command_MoveUp(Operator):
    bl_idname = "ar.command_move_up"
    bl_label = "Move Command Up"
    bl_description = "Move the selected Command up"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(eval("AR_Var.List_Command_{0:03d}".format(AR_Var.List_Index_000 + 1)))

    def execute(self, context):
        scene = context.scene
        Move(AR_('Index',0)+1 , 'Up')
        TempUpdateCommand(AR_('Index',0)+1)
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_Command_MoveUp)

class AR_OT_Command_MoveDown(Operator):
    bl_idname = "ar.command_move_down"
    bl_label = "Move Command Down"
    bl_description = "Move the selected Command down"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(eval("AR_Var.List_Command_{0:03d}".format(AR_Var.List_Index_000 + 1)))

    def execute(self, context):
        scene = context.scene
        Move(AR_('Index',0)+1 , 'Down')
        TempUpdateCommand(AR_('Index',0)+1)
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_Command_MoveDown)

class AR_OT_Command_Clear(Operator):
    bl_idname = "ar.command_clear"
    bl_label = "Clear Command"
    bl_description = "Delete all Commands of the selected Record"

    @classmethod
    def poll(cls, context):
        AR_Var = context.preferences.addons[__package__].preferences
        return len(eval("AR_Var.List_Command_{0:03d}".format(AR_Var.List_Index_000 + 1)))

    def execute(self, context):
        scene = context.scene
        Clear(AR_('Index',0)+1)
        TempUpdateCommand(AR_('Index',0)+1)
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_Command_Clear)

class AR_OT_Global_Settings(bpy.types.Operator):
    bl_idname = "ar.global_settings"
    bl_label = "Settings"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        AR_Var = context.preferences.addons[__package__].preferences
        layout = self.layout
        layout.prop(AR_Var, 'Autosave')
        if AR_Var.Autosave:
            layout.operator(AR_OT_Load.bl_idname, text= "Load from File")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=100)
classes.append(AR_OT_Global_Settings)

cmd_edit_time = [0]
class AR_OT_Command_Edit(bpy.types.Operator):
    bl_idname = "ar.command_edit"
    bl_label = "Edit"
    bl_description = "Double click to Edit"

    Name : StringProperty(name= "Name")
    Command : StringProperty(name= "Command")
    last : StringProperty()
    index : IntProperty()

    def execute(self, context):
        index_btn = AR_('Index',0)+1
        index_macro = AR_('Index', index_btn)
        macro = AR_('List',index_btn)[index_macro]
        macro.macro = self.Name
        macro.cname = self.Command
        TempUpdateCommand(index_btn)
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'Name', text= "Name")
        layout.prop(self, 'Command', text= "")

    def invoke(self, context, event):
        AR_Var = context.preferences.addons[__package__].preferences
        index_btn = AR_('Index',0)+1
        macro = AR_('List',index_btn)[self.index]
        mlast = f"{index_btn}.{self.index}" 
        t = time.time()
        #print(str(self.last == mlast)+ "    " +str(cmd_edit_time[0] + 0.7 > t) + "      " + str(self.last) + "      " + str(mlast)+ "      " + str(cmd_edit_time[0])+ "      " + str(cmd_edit_time[0] + 0.7)+ "      " + str(t))
        if self.last == mlast and cmd_edit_time[0] + 0.7 > t:
            self.last = mlast
            cmd_edit_time[0] = t
            self.Name = macro.macro
            self.Command = macro.cname
            return context.window_manager.invoke_props_dialog(self, width=500)
        else:
            self.last = mlast
            cmd_edit_time[0] = t
            exec("AR_Var.List_Index_{0:03d} = self.index".format(index_btn))
        return {"FINISHED"}
classes.append(AR_OT_Command_Edit)

rec_edit_time = [0]
class AR_OT_Record_Edit(bpy.types.Operator):
    bl_idname = "ar.record_edit"
    bl_label = "Edit"
    bl_description = "Double Click to Edit"

    Name : StringProperty(name= "Name")
    last : StringProperty()
    index : IntProperty()

    def execute(self, context):
        index_btn = AR_('Index',0)
        record = AR_('List',0)[index_btn]
        record.cname = self.Name
        TempUpdateCommand(index_btn)
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'Name', text= "Name")

    def invoke(self, context, event):
        AR_Var = context.preferences.addons[__package__].preferences
        index_btn = AR_('Index',0)
        record =  AR_('List',0)[index_btn]
        mlast = f"{index_btn}"
        t = time.time()
        if self.last == mlast and rec_edit_time[0] + 0.7 > t:
            self.last = mlast
            rec_edit_time[0] = t
            self.Name = record.cname
            return context.window_manager.invoke_props_dialog(self, width=200)
        else:
            self.last = mlast
            rec_edit_time[0] = t
            AR_Var.List_Index_000 = self.index
        return {"FINISHED"}
classes.append(AR_OT_Record_Edit)

# PropertyGroups =======================================================================
class AR_OT_String(PropertyGroup):#リストデータを保持するためのプロパティグループを作成
    cname : StringProperty() #AR_Var.name
    macro : StringProperty()
    active : BoolProperty(default= True)
    alert : BoolProperty()
classes.append(AR_OT_String)

currentselected = [None]
lastselected = [None]
def UseRadioButtons(self, context):
    AR_Var = context.preferences.addons[__package__].preferences
    categories = AR_Var.Categories
    for cat in categories:
        if not cat.pn_selected and lastselected[0] == cat and currentselected[0] == cat:
            cat.pn_selected = True
        elif cat.pn_selected and lastselected[0] != cat and currentselected[0] != cat:
            currentselected[0] = cat
            if lastselected[0] is not None:
                lastselected[0].pn_selected = False
            lastselected[0] = cat

class AR_CategorizeProps(PropertyGroup):
    pn_name : StringProperty()
    pn_show : BoolProperty(default= True)
    pn_selected : BoolProperty(default= False, update= UseRadioButtons)
    Instance_Start : IntProperty(default= 0)
    Instance_length : IntProperty(default= 0)
classes.append(AR_CategorizeProps)

Icurrentselected = [None]
Ilastselected = [None]
def Instance_Updater(self, context):
    AR_Var = bpy.context.preferences.addons[__package__].preferences
    enum = context.scene.ar_enum
    for e in enum:
        if not e.Value and Ilastselected[0] == e.Index and Icurrentselected[0] == e.Index:
            e.Value = True
        elif e.Value and Ilastselected[0] != e.Index and Icurrentselected[0] != e.Index:
            Icurrentselected[0] = e.Index
            if Ilastselected[0] is not None:
                try:
                    enum[Ilastselected[0]].Value = False
                except:
                    Ilastselected[0] = None 
            Ilastselected[0] = e.Index
            AR_Var.Instance_Index = e.Index

class AR_Enum(PropertyGroup):
    Value : BoolProperty(default= False, update= Instance_Updater)
    Index : IntProperty()
    Init = True
classes.append(AR_Enum)

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

class AR_CommandString(PropertyGroup):
    name : StringProperty()
classes.append(AR_CommandString)

class AR_Struct(PropertyGroup):
    name: StringProperty()
    command: CollectionProperty(type= AR_CommandString)
    icon : StringProperty(default= 'BLANK1')
classes.append(AR_Struct)

class AR_Prop(AddonPreferences):#何かとプロパティを収納
    bl_idname = __package__

    Rename : StringProperty() #AR_Var.name
    Loaded : BoolProperty(default= False)
    Autosave : BoolProperty(default= False, name= "Autosave", description= "automatically saves all Global Buttons to the Storage")
    RecToBtn_Mode : EnumProperty(items=[("copy", "Copy", "Copy the Action over to Global"), ("move", "Move", "Move the Action over to Global and delete it from Local")], name= "Mode")
    BtnToRec_Mode : EnumProperty(items=[("copy", "Copy", "Copy the Action over to Local"), ("move", "Move", "Move the Action over to local and delete it from Global")], name= "Mode")
    SelectedIcon = "BLANK1"

    Instance_Coll : CollectionProperty(type= AR_Struct)
    Instance_Index : IntProperty(default= 0)

    Categories : CollectionProperty(type= AR_CategorizeProps)

    FileDisp_Name = []
    FileDisp_Command = []
    FileDisp_Index : IntProperty(default= 0)

    HideMenu : BoolProperty(name= "Hide Menu", description= "Hide Menu")
    ShowMacros : BoolProperty(name= "Show Macros" ,description= "Show Macros", default= True)

    Record = False
    Temp_Command = []
    Temp_Num = 0
    for Num_Loop in range(256) :
        exec('List_Index_{0:03d} : IntProperty(default = 0)'.format(Num_Loop))
        exec('List_Command_{0:03d} : CollectionProperty(type = AR_OT_String)'.format(Num_Loop))

    # (Operator.bl_idname, key, event, Ctrl, Alt, Shift)
    addon_keymaps = []
    key_assign_list = \
    [
    (AR_OT_Command_Add.bl_idname, 'COMMA', 'PRESS', False, False, True),
    (AR_OT_Record_Play.bl_idname, 'PERIOD', 'PRESS', False, False, True),
    (AR_OT_Record_SelectorUp.bl_idname, 'WHEELUPMOUSE','PRESS', False, False, True),
    (AR_OT_Record_SelectorDown.bl_idname, 'WHEELDOWNMOUSE','PRESS', False, False, True)
    ]
classes.append(AR_Prop)

# Registration ================================================================================================
spaceTypes = ["VIEW_3D", "IMAGE_EDITOR", "NODE_EDITOR", "SEQUENCE_EDITOR", "CLIP_EDITOR", "DOPESHEET_EDITOR", "GRAPH_EDITOR", "NLA_EDITOR", "TEXT_EDITOR"]
for spaceType in spaceTypes:
    panelFactory( spaceType )

def Initialize_Props():# プロパティをセットする関数
    bpy.types.Scene.ar_enum = CollectionProperty(type= AR_Enum)
    bpy.types.Scene.ar_filecategories = CollectionProperty(type= AR_CategorizeFileDisp)
    bpy.types.Scene.ar_filedisp = CollectionProperty(type= AR_FileDisp)
    bpy.app.handlers.depsgraph_update_pre.append(InitSavedPanel)
    bpy.app.handlers.undo_post.append(TempLoad) # add TempLoad to ActionHandler and call ist after undo
    bpy.app.handlers.redo_post.append(TempLoad) # also for redo
    bpy.app.handlers.undo_post.append(TempLoadCats)
    bpy.app.handlers.redo_post.append(TempLoadCats)
    register[0] = True
    if bpy.context.window_manager.keyconfigs.addon:
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Window', space_type='EMPTY')#Nullとして登録
        AR_Prop.addon_keymaps.append(km)
        for (idname, key, event, ctrl, alt, shift) in AR_Prop.key_assign_list:
            kmi = km.keymap_items.new(idname, key, event, ctrl=ctrl, alt=alt, shift=shift)# ショートカットキーの登録

def Clear_Props():
    del bpy.types.Scene.ar_enum
    del bpy.types.Scene.ar_filedisp
    del bpy.types.Scene.ar_filecategories
    bpy.app.handlers.undo_post.remove(TempLoad)
    bpy.app.handlers.redo_post.remove(TempLoad)
    bpy.app.handlers.undo_post.remove(TempLoadCats)
    bpy.app.handlers.redo_post.remove(TempLoadCats)
    bpy.app.handlers.depsgraph_update_pre.remove(InitSavedPanel)
    register[0] = False
    for km in AR_Prop.addon_keymaps:
        bpy.context.window_manager.keyconfigs.addon.keymaps.remove(km)
    AR_Prop.addon_keymaps.clear()
