#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label Licence Plate
# Author:      mq
# Created:     12/27/2017
#
#-------------------------------------------------------------------------------

from tkinter import *
from tkinter import messagebox,ttk
from tkinter.filedialog import askdirectory
from PIL import Image, ImageTk
import os
import glob
import random
import xml_parser as xp
import common as cn
import Language as la
from win32api import GetSystemMetrics

import numpy as np
import plate_recog as pr
from parameters import * 
import log

class LabelTool():
    def __init__(self, master):
        # get display resolution
        WIDTH = GetSystemMetrics(0)
        HEIGHT = GetSystemMetrics(1)

        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.parent.resizable(width=FALSE, height=FALSE)
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=YES)

        # config 
        self.config_file = './config.ini'
        self.isloadconfsuccess = False
        # get image dir from saved text file
        scale = 3/4
        if WIDTH > 1280:
            scale = 4/5
        self.convas_w = int(WIDTH*scale)    #画布宽
        self.convas_h = int(HEIGHT*scale)    #画布高
        self.imageDir = ''
        self.cur = 1
        self.loadConf()

        # display scale
        self.scale_x = 1
        self.scale_y = 1
        self.scale_W = self.convas_w
        self.scale_H = self.convas_h

        # rect number
        self.rect_num = 0  #rects of plate and charactors 6~9
        self.rect_min = 5
        self.rect_max = 9

        # crop image
        self.isCrop = False
        self.crop_box = (0, 0, 0, 0)
        self.crop_rate_x = 1
        self.crop_rate_y = 1

        #enlarge plate
        self.isEnlarge = False
        self.selectedListboxId = -1

        # initialize global state
        self.imageList = []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.img = None
        self.img_src = None
        self.tkimg = None

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # four vertex
        self.click_num = 0
        self.vertex = [[0,0],[0,0],[0,0],[0,0]]

        # reference to bbox
        self.bboxIdList = []
        self.lineIdList = []
        self.cboxIdList = []
        self.cboxIds = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None
        self.mlineId = None
        self.lineId = None
        self.selectBoxId = None

        # Plate number
        self.plate = xp.Plate()
        self.plate_cache = []  #存放最近标记过的车牌号码（最多5个，不重复）
        self.cacheIdx = -1  # plate cache index

        # country/region
        self.region_no = 0
        self.plate_region = PLATE_REGION[self.region_no]
        self.dl_palte_dll_ini_ok = False
        self.tw_plate_dll_ini_ok = False

        # truncated   #车牌是否遮挡，默认没有遮挡(0)
        self.truncated = 0

        # Plate color
        self.PLATE_COLOR = PLATE_COLORS[0]
        self.plate_color = ''

        # Plate layer
        self.PLATE_LAYER = PLATE_LAYERS
        self.plate_layer = ''

        # Clear 
        self.clear = False   # 有车牌被删除

        # Interface language
        self.language = 'CN'
        self.la = la.Language(self.language)

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text=self.la.image_dir)
        self.label.grid(row=0, column=0, sticky=E)
        self.et = StringVar()
        self.entry = Entry(self.frame, textvariable=self.et)
        self.entry.grid(row=0, column=1, sticky=W+E)
        self.ldBtn = Button(self.frame, text=self.la.load, command=self.loadDir)
        self.ldBtn.grid(row=0, column=2, sticky=W+E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<ButtonRelease-1>", self.mouseClickUp)
        self.mainPanel.bind("<Button-3>", self.cancelOperation)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.mainPanel.bind("<B1-Motion>", self.mouseSelectCropBox)
        self.parent.bind("<F2>", self.saveImage)
        self.parent.bind("<F1>", self.prevImage) # press 'a' to go backforward
        self.parent.bind("<F3>", self.nextImage) # press 'd' to go forward
        self.parent.bind("<F5>", self.enlargePlate) 
        self.parent.bind("<F6>", self.eraseBlock)
        self.parent.bind("<F7>", self.loadPlateCache)
        self.mainPanel.grid(row=1, column=0, rowspan=6, columnspan=2, sticky=W+N)

        # showing bbox info & delete bbox
        self.rightPanel = Frame(self.frame)
        self.rightPanel.grid(row=1, column=2, rowspan=6, columnspan=1, sticky=W+N)
        # region
        self.pregion = Label(self.rightPanel, text=self.la.region)
        self.pregion.pack(side=TOP, expand=YES, fill=X, pady=5)
        e_region = StringVar() 
        self.pregion_list = ttk.Combobox(self.rightPanel, textvariable=e_region, state='readonly')
        self.pregion_list['values'] = tuple(PLATE_REGION)
        self.pregion_list.current(0)
        self.pregion_list.bind("<<ComboboxSelected>>", self.selectPlateRegion)
        self.pregion_list.pack(side=TOP, expand=YES, fill=X)
        # plate number
        self.pnumber = Label(self.rightPanel, text=self.la.plate_number)
        self.pnumber.pack(side=TOP, expand=YES, fill=X, pady=5)
        self.btn_plate_recog = Button(self.rightPanel, text=self.la.auto_plate_recog, command=self.plate_recognize)
        self.btn_plate_recog.pack(side=TOP, expand=YES, fill=X)
        e_number = StringVar() 
        self.pnumber_entry = Entry(self.rightPanel, textvariable=e_number)
        self.pnumber_entry.pack(side=TOP, expand=YES, fill=X)
        # truncated
        self.trunc_value = IntVar()
        self.truncated_cbn = Checkbutton(self.rightPanel,variable=self.trunc_value, command=self.selectTruncated,text=self.la.truncated)
        self.truncated_cbn.pack(side=TOP, expand=YES, fill=X)
        # plate color
        self.pcolor = Label(self.rightPanel, text=self.la.plate_color)
        self.pcolor.pack(side=TOP, expand=YES, fill=X, pady=5)
        color_value = StringVar()
        self.pcolor_list = ttk.Combobox(self.rightPanel, textvariable=color_value, state='readonly')
        self.pcolor_list['values'] = tuple(self.PLATE_COLOR)
        self.pcolor_list.current(0)
        self.pcolor_list.bind("<<ComboboxSelected>>", self.selectPlateColor)
        self.pcolor_list.pack(side=TOP, expand=YES, fill=X)
        # number of layer
        self.player = Label(self.rightPanel, text=self.la.plate_layer)
        self.player.pack(side=TOP, expand=YES, fill=X, pady=5)
        layer_value = StringVar()
        self.player_list = ttk.Combobox(self.rightPanel, textvariable=layer_value, state='readonly')
        self.player_list['values'] = tuple(self.PLATE_LAYER)
        self.player_list.current(0)
        self.player_list.bind("<<ComboboxSelected>>", self.selectPlateLayer)
        self.player_list.pack(side=TOP, expand=YES, fill=X)
        # plate list
        self.lb1 = Label(self.rightPanel, text=self.la.label_list)
        self.lb1.pack(side=TOP, expand=YES, fill=X, pady=3)
        self.listbox = Listbox(self.rightPanel, width=25, height=15)
        self.listbox.bind("<ButtonRelease-1>", self.selectPlateList)
        self.listbox.pack(side=TOP, expand=YES, fill=X, pady=3)
        self.btnDel = Button(self.rightPanel, text=self.la.clear, command=self.delBBox)
        self.btnDel.pack(side=TOP, expand=YES, fill=X, pady=3)
        self.btnClear = Button(self.rightPanel, text=self.la.clear_all, command=self.clearAll)
        self.btnClear.pack(side=TOP, expand=YES, fill=X, pady=3)
        self.btnDeleteImage = Button(self.rightPanel, text=self.la.delete_image, command=self.deleteImage)
        self.btnDeleteImage.pack(side=TOP, expand=YES, fill=X, pady=3)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row=7, column=0, columnspan=3, sticky=W+E)
        self.saveBtn = Button(self.ctrPanel, text=self.la.save, width=10, command=self.saveImage)
        self.saveBtn.pack(side=LEFT, padx=5, pady=3)
        self.prevBtn = Button(self.ctrPanel, text=self.la.prev, width=10, command=self.prevImage)
        self.prevBtn.pack(side=LEFT, padx=5, pady=3)
        self.nextBtn = Button(self.ctrPanel, text=self.la.next, width=10, command=self.nextImage)
        self.nextBtn.pack(side=LEFT, padx=5, pady=3)
        self.progLabel = Label(self.ctrPanel, text=self.la.index)
        self.progLabel.pack(side=LEFT, padx=5)
        self.tmpLabel = Label(self.ctrPanel, text=self.la.goto_id)
        self.tmpLabel.pack(side=LEFT, padx=5)
        self.idxEntry = Entry(self.ctrPanel, width=5)
        self.idxEntry.pack(side=LEFT)
        self.goBtn = Button(self.ctrPanel, text=self.la.go, command=self.gotoImage)
        self.goBtn.pack(side=LEFT)
        self.gotoUnlabelBtn = Button(self.ctrPanel, text=self.la.goto_unlabel, command=self.gotoFirstUnlabeledImage)
        self.gotoUnlabelBtn.pack(side=LEFT, padx=5, pady=3)
        self.enlargeBtn = Button(self.ctrPanel, text=self.la.enlarge, command=self.enlargePlate)
        self.enlargeBtn.pack(side=LEFT, padx=5, pady=3)
        self.eraseBlockBtn = Button(self.ctrPanel, text=self.la.erase_block, command=self.eraseBlock)
        self.eraseBlockBtn.pack(side=LEFT, padx=5, pady=3)
        self.loadPlateCacheBtn = Button(self.ctrPanel, text=self.la.load_plate_cache, \
                                        command=self.loadPlateCache)
        self.loadPlateCacheBtn.pack(side=LEFT, padx=5, pady=3)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side=RIGHT)

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(4, weight=1)

        # log
        self.log_path = "log.log"
        log.logIni(self.log_path)

        log.writeLog(self.log_path,"alg ini ...")
        #import plate recognization dll
        self.plr = pr.Plate_recog('detection')
        self.plate_recog_init = True
        if not self.plr.init("大陆"):
            self.plate_recog_init = False
            print("Alg init error...")
            log.writeLog(self.log_path, "alg ini error ...")
            return
        self.dl_palte_dll_ini_ok = True

        log.writeLog(self.log_path, "alg ini ok ...")
        if self.isloadconfsuccess:
            self.loadDir()

    def selectPlateRegion(self,event=None):
        self.plate_region = self.pregion_list.get()
        self.region_no = PLATE_REGION.index(self.plate_region)
        if not self.plr.init(self.plate_region):
            self.plate_recog_init = False
            print("Alg init error...")
            log.writeLog(self.log_path, "alg ini error ...")
            return
        if self.region_no == 0:
            self.dl_palte_dll_ini_ok = True
            self.tw_plate_dll_ini_ok = False
        else:
            self.dl_palte_dll_ini_ok = False
            self.tw_plate_dll_ini_ok = True
            
        self.PLATE_COLOR = PLATE_COLORS[self.pregion_list.current()]
        self.pcolor_list['values'] = tuple(self.PLATE_COLOR)
        self.pcolor_list.current(0)

    def selectTruncated(self,event=None):
        self.truncated = self.trunc_value.get()

    def selectPlateColor(self,event=None):
        self.plate_color = self.pcolor_list.get()

    def selectPlateLayer(self, event=None):
        self.plate_layer = self.player_list.get()

    def selectPlateList(self, event=None):
        if self.isEnlarge:
            return
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.selectedListboxId = idx
        self.pnumber_entry.delete(0,END)
        plate_number = ""
        plate_number = plate_number.join(self.plate.plateLists[idx][1])
        self.pnumber_entry.insert(0,plate_number)
        count = 0
        while self.plate.plateLists[idx][4] not in self.PLATE_COLOR:
            if count > REGION_NUM - 1:
                break
            count += 1
            if self.region_no + 1 < REGION_NUM:
                self.region_no += 1
            else:
                self.region_no = 0
            self.PLATE_COLOR = PLATE_COLORS[self.region_no]
        self.pregion_list.current(self.region_no)
        self.pcolor_list['values'] = tuple(self.PLATE_COLOR)
        self.pcolor_list.current(self.PLATE_COLOR.index(self.plate.plateLists[idx][4]))
        self.player_list['values'] = tuple(self.PLATE_LAYER)
        self.player_list.current(self.PLATE_LAYER.index(self.plate.plateLists[idx][5]))
        self.trunc_value.set(self.plate.plateLists[idx][6])
        self.truncated = self.trunc_value.get()
        self.showLabel()

    def plate_recognize(self):
        if self.rect_num < 1:
            return
        self.plate_region = self.pregion_list.get()
        self.region_no = PLATE_REGION.index(self.plate_region)
        is_plate_dll_ini = True
        if self.region_no == 0:
            if not self.dl_palte_dll_ini_ok:
                is_plate_dll_ini = False
        else:
            if not self.tw_plate_dll_ini_ok:
                is_plate_dll_ini = False
        if not is_plate_dll_ini:
            if not self.plr.init(self.plate_region):
                self.plate_recog_init = False
                print("Alg init error...")
                log.writeLog(self.log_path, "alg ini error ...")
                return
            if self.region_no == 0:
                self.dl_palte_dll_ini_ok = True
                self.tw_plate_dll_ini_ok = False
            else:
                self.dl_palte_dll_ini_ok = False
                self.tw_plate_dll_ini_ok = True
                
        if self.plate_region not in PLATE_REGION:
            messagebox.showerror(self.la.message_win_plate, self.la.plate_format_error)
            return
        if not self.plate_recog_init:
            return
        self.plate.chars = ''
        self.plate.char_num = 0
        # self.img_src.save("img.jpg")
        chars,probs = self.plr.recogize(self.img_src,self.plate.pbox,self.plate.cboxes,self.plate_region,self.truncated)
        self.pnumber_entry.delete(0,END)
        self.pnumber_entry.insert(0,chars)


    def loadConf(self):
        self.isloadconfsuccess = False
        file_dir = os.path.abspath(self.config_file)
        if os.path.exists(file_dir):
            fl = open(file_dir,"r", encoding='utf-8')
            lines = fl.readlines()
            if len(lines) == 0:
                return
            for line in lines:
                line = line.strip('\n')
                #line = line.strip(' ')
                ph = line.split(": ")
                conf_name  = ph[0]
                conf_value = ph[1]
                if 'image Dir' == conf_name:
                    if 0 != len(conf_value):
                        self.imageDir = conf_value
                        self.isloadconfsuccess = True
                if 'Last image No' == conf_name:
                    if 0 != len(conf_value):
                        self.cur = int(conf_value)
                    else:
                        self.cur = 1
                # if 'convas_w' == conf_name:
                #     if 0 != len(conf_value):
                #         self.convas_w = int(conf_value)
                #     else:
                #         self.convas_w = WIDTH
                # if 'convas_h' == conf_name:
                #     if 0 != len(conf_value):
                #         self.convas_h = int(conf_value)
                #     else:
                #         self.convas_h = HEIGHT
                # if 'language' == conf_name:
                #     if 0 != len(conf_value):
                #         self.language = conf_value
                #     else:
                #         self.language = DEFAULT_LANGUAGE

            fl.close()

    def writeConf(self):
        file_dir = os.path.abspath(self.config_file)
        f = open(file_dir,"w", encoding='utf-8')
        txt_dir = 'image Dir: %s\n' % (self.imageDir)
        f.write(txt_dir)
        txt_last_No = 'Last image No: %d\n' % (self.cur)
        f.write(txt_last_No)
        # txt_w = 'convas_w: %d\n' % (self.convas_w)
        # f.write(txt_w)
        # txt_h = 'convas_h: %d' % (self.convas_h)
        # f.write(txt_h)
        # txt_la = 'language: %s' % (self.language)
        # f.write(txt_la)
        f.close()

    def loadDir(self):
        if not self.isloadconfsuccess:
            # chose image dir 
            file_dir = askdirectory()
            if not '' == file_dir:
                self.imageDir = file_dir
                self.cur = 1
                self.writeConf()
        else:
            self.isloadconfsuccess = False
        self.et.set(self.imageDir)

        # get image list
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        print(self.imageDir)
        if len(self.imageList) == 0:
            print('No .jpg images found')
            self.cur = 1
            self.total = len(self.imageList)
            self.mainPanel.delete('all')
            self.progLabel.config(text="%04d/%04d" %(self.cur, self.total))
            self.clearAll()
        else:
            # default to the 1st image in the collection
            self.total = len(self.imageList)

            # set up output dir
            self.outDir = self.imageDir
            if not os.path.exists(self.outDir):
                os.mkdir(self.outDir)

            self.loadImage()
            print('%d images loaded' % (self.total))

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img_src = Image.open(imagepath)
        print(imagepath)
        self.img = self.img_src

        # Enlarge local image
        if self.isCrop:
            tmp = self.img.crop((self.crop_box[0],self.crop_box[1],
                                self.crop_box[2],self.crop_box[3]))
            self.img = tmp
        else:
            self.scale_x = float(self.img.width)/self.scale_W
            self.scale_y = float(self.img.height)/self.scale_H

        # resize image
        resize_img = self.img.resize((self.scale_W,self.scale_H)) 

        self.tkimg = ImageTk.PhotoImage(resize_img)
        self.mainPanel.config(width=max(self.tkimg.width(), 400), height=max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=NW)
        self.progLabel.config(text=" %s: %d/%d" %(self.la.index, self.cur, self.total))

        # load labels
        self.imagename = cn.getFileNameFromPath(imagepath)
        labelname = self.imagename + '.xml'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        self.plate.plateLists = []
        if os.path.exists(self.labelfilename):
            self.plate.readXml(self.labelfilename)
        if not self.isEnlarge:
            self.selectedListboxId = -1
        self.showLabel()
        self.writeConf()
            
    def showLabel(self):
        self.clearBBox()

        # check plate 
        i = 0
        while(i < len(self.plate.plateLists)):
            pf = True
            if 0 == len(self.plate.plateLists[i]):
                pf = False
                break
            for p in self.plate.plateLists[i]:
                if [] == p:
                    pf = False
                    break
            if not pf:
                self.plate.plateLists.pop(i)
                i -= 1
            i += 1

        p_num = 0

        #enlarge selected plate area
        if self.isCrop:
            if self.isEnlarge: 
                idx = self.selectedListboxId
                chars = self.plate.plateLists[idx][1]
                pbox = self.plate.plateLists[idx][2]
                cboxes = self.plate.plateLists[idx][3]

                # show plate box
                color = 'red'
                boxId = []
                x0,y0 = 0,0
                for i in range(0,len(pbox)-1):
                    x1 = int((pbox[i][0] - self.crop_box[0])/(self.scale_x*self.crop_rate_x))
                    y1 = int((pbox[i][1] - self.crop_box[1])/(self.scale_y*self.crop_rate_y))
                    x2 = int((pbox[i+1][0] - self.crop_box[0])/(self.scale_x*self.crop_rate_x))
                    y2 = int((pbox[i+1][1] - self.crop_box[1])/(self.scale_y*self.crop_rate_y))
                    tmpId = self.mainPanel.create_line(x1, y1, x2, y2, width=2, fill=color)
                    boxId.append(tmpId)
                x1 = int((pbox[-1][0] - self.crop_box[0])/(self.scale_x*self.crop_rate_x))
                y1 = int((pbox[-1][1] - self.crop_box[1])/(self.scale_y*self.crop_rate_y))
                x2 = int((pbox[0][0] - self.crop_box[0])/(self.scale_x*self.crop_rate_x))
                y2 = int((pbox[0][1] - self.crop_box[1])/(self.scale_y*self.crop_rate_y))
                tmpId = self.mainPanel.create_line(x1, y1, x2, y2, width=2, fill=color)
                boxId.append(tmpId)
                self.bboxIdList.append(boxId)
                # self.listbox.insert(END, '%s (%d, %d)' %("".join(chars), pbox[0][0], pbox[0][1]))
                # self.listbox.itemconfig(p_num, fg=color)

                # show char box
                cboxId = []
                for cbox in cboxes:
                    boxId = []
                    for i in range(0,len(cbox)-1):
                        x1 = int((cbox[i][0] - self.crop_box[0])/(self.scale_x*self.crop_rate_x))
                        y1 = int((cbox[i][1] - self.crop_box[1])/(self.scale_y*self.crop_rate_y))
                        x2 = int((cbox[i+1][0] - self.crop_box[0])/(self.scale_x*self.crop_rate_x))
                        y2 = int((cbox[i+1][1] - self.crop_box[1])/(self.scale_y*self.crop_rate_y))
                        tmpId = self.mainPanel.create_line(x1, y1, x2, y2, width=1, fill=color)
                        boxId.append(tmpId)
                    x1 = int((cbox[-1][0] - self.crop_box[0])/(self.scale_x*self.crop_rate_x))
                    y1 = int((cbox[-1][1] - self.crop_box[1])/(self.scale_y*self.crop_rate_y))
                    x2 = int((cbox[0][0] - self.crop_box[0])/(self.scale_x*self.crop_rate_x))
                    y2 = int((cbox[0][1] - self.crop_box[1])/(self.scale_y*self.crop_rate_y))
                    tmpId = self.mainPanel.create_line(x1, y1, x2, y2, width=1, fill=color)
                    boxId.append(tmpId)
                    cboxId.append(boxId)
                self.cboxIdList.append(cboxId)
        else:
            p_No = -1
            for plate in self.plate.plateLists:
                p_No += 1
                char_num = plate[0]
                chars = plate[1]
                pbox = plate[2]
                cboxes = plate[3]

                # show plate box
                # color = COLORS[p_num+1 % len(COLORS)]
                color = 'red'
                if self.selectedListboxId == p_No:
                    color = 'green'
                color_line = ['black','green','yellow']
                boxId = []
                x0,y0 = 0,0
                for i in range(0,len(pbox)-1):
                    x1 = int(pbox[i][0]/self.scale_x)
                    y1 = int(pbox[i][1]/self.scale_y)
                    x2 = int(pbox[i+1][0]/self.scale_x)
                    y2 = int(pbox[i+1][1]/self.scale_y)
                    tmpId = self.mainPanel.create_line(x1, y1, x2, y2, width=2, fill=color)
                    boxId.append(tmpId)
                x1 = int(pbox[-1][0]/self.scale_x)
                y1 = int(pbox[-1][1]/self.scale_y)
                x2 = int(pbox[0][0]/self.scale_x)
                y2 = int(pbox[0][1]/self.scale_y)
                tmpId = self.mainPanel.create_line(x1, y1, x2, y2, width=2, fill=color)
                boxId.append(tmpId)
                self.bboxIdList.append(boxId)
                self.listbox.insert(END, '%s (%d, %d)' %("".join(chars), pbox[0][0], pbox[0][1]))
                self.listbox.itemconfig(p_num, fg=color)

                # show char box
                cboxId = []
                for cbox in cboxes:
                    boxId = []
                    for i in range(0,len(cbox)-1):
                        x1 = int(cbox[i][0]/self.scale_x)
                        y1 = int(cbox[i][1]/self.scale_y)
                        x2 = int(cbox[i+1][0]/self.scale_x)
                        y2 = int(cbox[i+1][1]/self.scale_y)
                        tmpId = self.mainPanel.create_line(x1, y1, x2, y2, width=1, fill=color)
                        boxId.append(tmpId)
                    x1 = int(cbox[-1][0]/self.scale_x)
                    y1 = int(cbox[-1][1]/self.scale_y)
                    x2 = int(cbox[0][0]/self.scale_x)
                    y2 = int(cbox[0][1]/self.scale_y)
                    tmpId = self.mainPanel.create_line(x1, y1, x2, y2, width=1, fill=color)
                    boxId.append(tmpId)
                    cboxId.append(boxId)
                self.cboxIdList.append(cboxId)
                p_num += 1
            if self.selectedListboxId > -1:
                self.listbox.select_set(self.selectedListboxId)

    def enlargePlate(self, event=None):
        if not self.isEnlarge:
            sel = self.listbox.curselection()
            if len(sel) != 1 :
                return
            idx = int(sel[0])
            self.selectedListboxId = idx
            x1 = self.plate.plateLists[idx][2][0][0]
            y1 = self.plate.plateLists[idx][2][0][1]
            x2 = self.plate.plateLists[idx][2][1][0]
            y2 = self.plate.plateLists[idx][2][1][1]
            x3 = self.plate.plateLists[idx][2][2][0]
            y3 = self.plate.plateLists[idx][2][2][1]
            x4 = self.plate.plateLists[idx][2][3][0]
            y4 = self.plate.plateLists[idx][2][3][1]

            xmin = min(x1,x2,x3,x4)
            ymin = min(y1,y2,y3,y4)
            xmax = max(x1,x2,x3,x4)
            ymax = max(y1,y2,y3,y4)

            self.isCrop = True
            self.isEnlarge = True
            self.crop_box = (xmin-20,ymin-20,xmax+20,ymax+20)
            f,box = cn.checkbox(self.crop_box, self.img.width, self.img.height)
            if f:
                self.crop_box = box
            box_w = self.crop_box[2] - self.crop_box[0]
            box_h = self.crop_box[3] - self.crop_box[1]
            self.crop_rate_x = float(box_w/self.scale_x)/self.scale_W
            self.crop_rate_y = float(box_h/self.scale_y)/self.scale_H
            self.click_num = 0
        else:
            self.isEnlarge = False
            self.isCrop = False
            self.crop_rate_x = 1
            self.crop_rate_y = 1
        self.loadImage()

    def checkPlateChars(self,chars):
        is_wj = False
        p_chars = []
        if self.plate_region == "大陆":
            if chars[0] == 'w' or chars[0] == 'W':
                if chars[1] == 'j' or chars[1] == 'J':
                    is_wj = True
        if is_wj:
            p_chars.append('WJ')
            for i in range(2,len(chars)):
                p_chars.append(chars[i])
        else:
            for c in chars:
                p_chars.append(c)
        return p_chars

    def saveImage(self, event=None):
        if 0 == self.cur:
            return
        isPlateAdd = False
        plate_chars = []
        self.plate_color = self.pcolor_list.get()
        self.plate_layer = self.player_list.get()

        self.truncated = self.trunc_value.get()

        # modify plate
        if self.selectedListboxId > -1 and not self.clear:
            plate_chars = self.checkPlateChars(str(self.pnumber_entry.get()))
            # if self.truncated == 0:
            #     if False == plate_chars.isalnum() or \
            #         self.plate.plateLists[self.selectedListboxId][0] != len(plate_chars):
            #         messagebox.showerror(self.la.message_win_plate, self.la.plate_format_error)
            #         return
            self.plate.plateLists[self.selectedListboxId][1] = plate_chars
            self.plate.plateLists[self.selectedListboxId][4] = self.plate_color
            self.plate.plateLists[self.selectedListboxId][5] = self.plate_layer
            self.plate.plateLists[self.selectedListboxId][6] = self.truncated
            self.selectedListboxId = -1
            isPlateAdd = True
        # add new plate
        elif self.rect_num > 0:
            if self.truncated == 0:
                if self.rect_num < self.rect_min:
                    messagebox.showerror(self.la.message_win_plate, self.la.plate_format_error)
                    return
                elif self.rect_min <= self.rect_num: 
                    plate_chars = self.checkPlateChars(str(self.pnumber_entry.get()))
                    self.plate.chars = plate_chars
                    self.plate.color = self.plate_color
                    self.plate.layer = self.plate_layer
                    self.plate.plate = [self.rect_num-1,self.plate.chars,
                                        self.plate.pbox,self.plate.cboxes,
                                        self.plate.color, self.plate.layer,self.truncated]
                    if self.rect_num - 1 != len(self.plate.chars):
                        messagebox.showerror(self.la.message_win_plate, self.la.plate_format_error)
                        return
                    self.plate.plateLists.append(self.plate.plate)
            else:
                plate_chars = self.checkPlateChars(str(self.pnumber_entry.get()))
                self.plate.chars = plate_chars
                self.plate.color = self.plate_color
                self.plate.layer = self.plate_layer
                self.plate.plate = [self.rect_num-1,self.plate.chars,
                                    self.plate.pbox,self.plate.cboxes,
                                    self.plate.color, self.plate.layer,self.truncated]
                self.plate.plateLists.append(self.plate.plate)
            self.rect_num = 0
            self.plate.chars = []
            self.plate.pbox = []
            self.plate.cboxes = []
            self.plate.color = ''
            self.plate.layer = ''
            self.selectedListboxId = -1
            isPlateAdd = True
        
        # add new plate to plate cache
        if isPlateAdd:
            isSamePlate = False
            if len(self.plate_cache) > 0:
                for pc in self.plate_cache:
                    if pc == plate_chars:
                        isSamePlate = True
                        break
            if not isSamePlate:
                if len(self.plate_cache) > 5:
                    self.plate_cache.pop(1)
                self.plate_cache.append(plate_chars)

        if 0 != len(self.plate.plateLists):
            if isPlateAdd or self.clear:
                self.plate.writeXml(self.labelfilename, self.img_src.width, self.img_src.height, 3)
        else:
            if os.path.exists(self.labelfilename):
                os.remove(self.labelfilename)

        if self.clear:
            self.clear = False

        self.pnumber_entry.delete(0,END)
        self.isCrop = False
        print('Image No. %d saved' %(self.cur))
        self.loadImage()

    def mouseClick(self, event):
        if 0 == self.cur:
            return
        if self.isEnlarge:
            return
        # self.selectedListboxId = -1
        self.click_num += 1
        iscboxout = False

        x1, y1 = event.x, event.y
        self.vertex[self.click_num-1] = [x1,y1]
        self.pnumber_entry.delete(0,END)
        # self.pcolor_list.current(0)
        # self.player_list.current(0)
        self.trunc_value.set(0)
        if self.click_num == 1:
            is_selected = False
            p = [event.x*self.crop_rate_x*self.scale_x, event.y*self.crop_rate_y*self.scale_y]
            i = 0
            for plate in self.plate.plateLists:
                pbox = plate[2]
                is_in_polygon = cn.InPolygon(p,pbox)
                # print(pbox)
                # print(is_in_polygon)
                if is_in_polygon:
                    self.selectedListboxId = i
                    self.showLabel()
                    self.selectPlateList()
                    self.click_num = 0
                    is_selected = True
                    break
                i += 1
            if self.selectedListboxId > -1 and not is_selected:
                self.selectedListboxId = -1
                self.showLabel()

        if self.click_num > 1:
            self.lineId = self.mainPanel.create_line(self.vertex[self.click_num-1][0], \
                                       self.vertex[self.click_num-1][1], \
                                       self.vertex[self.click_num-2][0], \
                                       self.vertex[self.click_num-2][1], \
                                       width=2, fill='red')
            self.lineIdList.append(self.lineId)
            if self.click_num > 3:
                self.lineId = self.mainPanel.create_line(self.vertex[self.click_num-1][0], \
                                                         self.vertex[self.click_num-1][1], \
                                                         self.vertex[0][0], self.vertex[0][1], \
                                                         event.x, event.y, width=2, fill='red')
                self.lineIdList.append(self.lineId)
            if self.mlineId:
                self.mainPanel.delete(self.mlineId)
        if self.click_num > 3:
            if 0 == self.rect_num:
                self.bboxIdList.append(self.lineIdList)
                self.cboxIds = []
            elif self.rect_max > self.rect_num:
                self.cboxIds.append(self.lineIdList)
            else:
                for line_id in self.lineIdList:
                    self.mainPanel.delete(line_id)
                self.rect_num -= 1
                iscboxout = True
            self.lineId = None
            self.rect_num += 1
            self.click_num = 0
            self.lineIdList = []
            self.selectedListboxId = -1

            # convert location scale
            for i in range(0,len(self.vertex)):
                if self.isCrop:
                    self.vertex[i][0] = int(self.crop_box[0] + \
                                        self.vertex[i][0]*self.crop_rate_x*self.scale_x)
                    self.vertex[i][1] = int(self.crop_box[1] + \
                                        self.vertex[i][1]*self.crop_rate_y*self.scale_y)
                else:
                    self.vertex[i][0] = int(self.vertex[i][0]*self.scale_x)
                    self.vertex[i][1] = int(self.vertex[i][1]*self.scale_y)

            #save box
            if 1 == self.rect_num:
                self.plate.pbox = self.vertex
                self.listbox.insert(END, '(%d,%d)' %(self.vertex[0][0], self.vertex[0][1]))
                self.listbox.itemconfig(len(self.bboxIdList) - 1, fg='red')
            elif 1 < self.rect_num and self.rect_num <= self.rect_max:
                self.plate.cboxes.append(self.vertex)
            self.vertex = [[0,0],[0,0],[0,0],[0,0]]

        if iscboxout:
            return

    def mouseClickUp(self, event):
        if self.isCrop or self.rect_num != 0:
            return
        if 1 == self.click_num:
            x1, x2 = min(self.vertex[0][0], event.x), max(self.vertex[0][0], event.x)
            y1, y2 = min(self.vertex[0][1], event.y), max(self.vertex[0][1], event.y)
            box_w = x2 - x1
            box_h = y2 - y1
            if box_w > 20 and box_h > 20:
                self.isCrop = True
                self.crop_rate_x = float(box_w)/self.scale_W
                self.crop_rate_y = float(box_h)/self.scale_H
                self.crop_box = (int(x1*self.scale_x),int(y1*self.scale_y),
                                 int(x2*self.scale_x),int(y2*self.scale_y))
                self.click_num = 0
                self.selectedListboxId = -1
                
                self.loadImage()

    def mouseMove(self, event):
        self.disp.config(text='x: %d, y: %d' %(event.x, event.y))
        if 0 < self.click_num and self.click_num < 4:
            if self.mlineId:
                self.mainPanel.delete(self.mlineId)
            self.mlineId = self.mainPanel.create_line(self.vertex[self.click_num-1][0], \
                                       self.vertex[self.click_num-1][1], \
                                       event.x, event.y, width=2, \
                                       fill='red')
    
    def mouseSelectCropBox(self, event):
        if 1 == self.click_num and 0 == self.rect_num:
            if self.selectBoxId:
                self.mainPanel.delete(self.selectBoxId)
            self.selectBoxId = self.mainPanel.create_rectangle(self.vertex[self.click_num-1][0], \
                                       self.vertex[self.click_num-1][1], \
                                       event.x, event.y, width=2, \
                                       outline='red')

    def cancelOperation(self, event):
        if self.isEnlarge:
            self.isEnlarge = False
        if 4 > self.click_num and self.click_num > 1:
            line_id = self.lineIdList[-1]
            self.mainPanel.delete(line_id)
            self.click_num -= 1
            self.lineIdList.pop()
        elif 1 == self.click_num:
            self.click_num -= 1
            if self.mlineId:
                self.mainPanel.delete(self.mlineId)
        elif 0 == self.click_num:
            if self.rect_num > 0:
                if self.rect_num > 1:
                    self.plate.cboxes.pop()
                    for line_id in self.cboxIds[-1]:
                        self.mainPanel.delete(line_id)
                    self.cboxIds.pop()
                else:
                    self.plate.pbox = []
                    for line_id in self.bboxIdList[-1]:
                        self.mainPanel.delete(line_id)
                    self.bboxIdList.pop()
                    self.listbox.delete(END)
                self.rect_num -= 1
            else:
                self.isCrop = False
                self.crop_rate_x = 1
                self.crop_rate_y = 1
                self.selectedListboxId = -1
                self.loadImage()
    
        # fresh moveing line
        if 0 < self.click_num and self.click_num < 4:
            if self.mlineId:
                self.mainPanel.delete(self.mlineId)
            self.mlineId = self.mainPanel.create_line(self.vertex[self.click_num-1][0], \
                                       self.vertex[self.click_num-1][1], \
                                       event.x, event.y, width=2, \
                                       fill='red')

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        for line_id in self.bboxIdList[idx]:
            self.mainPanel.delete(line_id)
        self.bboxIdList.pop(idx)
        for cboxIds in self.cboxIdList[idx]:
            for line_id in cboxIds:
                self.mainPanel.delete(line_id)
        self.cboxIdList.pop(idx)
        self.listbox.delete(idx)

        self.plate.plateLists.pop(idx)
        self.selectedListboxId = -1
        self.clear = True

    def clearAll(self):
        self.plate.plateLists = []
        self.clearBBox()
        self.clear = True

    def clearBBox(self):
        self.listbox.delete(0, len(self.bboxIdList))
        for bboxIds in self.bboxIdList:
            for line_id in bboxIds:
                self.mainPanel.delete(line_id)
        for cboxIds in self.cboxIdList: 
            for cboxId in cboxIds:
                for line_id in cboxId:
                    self.mainPanel.delete(line_id)
        self.bboxIdList = []
        self.cboxIdList = []

    def deleteImage(self):
        df = False
        img_name = self.imagename + '.jpg'
        img_path = os.path.join(self.outDir, img_name)
        if os.path.exists(img_path):
            os.remove(img_path)
            df = True
        xml_name = self.imagename + '.xml'
        xml_path = os.path.join(self.outDir, xml_name)
        if os.path.exists(xml_path):
            os.remove(xml_path)
        if df:
            self.imageList.pop(self.cur - 1)
            if self.cur > len(self.imageList):
                self.cur -= 1
            if self.cur < 0:
                self.cur += 1
            self.loadImage()

    def clearLabelingBox(self):
        self.plate.pbox = []
        self.plate.char_num = 0
        self.plate.chars = []
        self.plate.cboxes = []
        self.rect_num = 0
        self.pnumber_entry.delete(0,END)

    def prevImage(self, event = None):
        #self.saveImage()
        self.isCrop = False
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()
            self.clearLabelingBox()
            self.crop_rate_x = 1
            self.crop_rate_y = 1
            self.selectedListboxId = -1
            

    def nextImage(self, event = None):
        #self.saveImage()
        self.isCrop = False
        self.isEnlarge = False
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()
            self.clearLabelingBox()
            self.crop_rate_x = 1
            self.crop_rate_y = 1
            self.selectedListboxId = -1
            

    def gotoImage(self):
        self.isCrop = False
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            #self.saveImage()
            self.cur = idx
            self.loadImage()

    def gotoFirstUnlabeledImage(self):
        self.isCrop = False
        while self.cur < self.total:
            imagepath = self.imageList[self.cur - 1]
            self.imagename = os.path.split(imagepath)[-1]
            self.imagename = self.imagename[:-4]
            labelname = self.imagename + '.xml'
            self.labelfilename = os.path.join(self.outDir, labelname)
            if os.path.exists(self.labelfilename):
                self.cur += 1
            else:
                break
        self.loadImage()
        self.clearLabelingBox()

    def eraseBlock(self, event=None):
        if self.isCrop:
            return
        log.writeLog(self.log_path, "erase block ...")
        if 1 == self.rect_num:
            x1 = min(self.plate.pbox[0][0], self.plate.pbox[1][0], \
                     self.plate.pbox[2][0], self.plate.pbox[3][0])
            y1 = min(self.plate.pbox[0][1], self.plate.pbox[1][1], \
                     self.plate.pbox[2][1], self.plate.pbox[3][1])   
            x2 = max(self.plate.pbox[0][0], self.plate.pbox[1][0], \
                     self.plate.pbox[2][0], self.plate.pbox[3][0])
            y2 = max(self.plate.pbox[0][1], self.plate.pbox[1][1], \
                     self.plate.pbox[2][1], self.plate.pbox[3][1])   
            box = (x1, y1, x2, y2)
            # log.writeLog(self.log_path, "x1,y1,x2,y2:"+str(x1)+' '+str(y1)+' '+str(x2)+' '+str(y2))
            bw = box[2] - box[0]
            bh = box[3] - box[1]
            # log.writeLog(self.log_path, "bw,bh:"+str(bw)+' '+str(bh))
            img_block = Image.new("RGB",(bw,bh),(0,0,0))
            self.img.paste(img_block,box)
            imagepath = self.imageList[self.cur - 1]
            # log.writeLog(self.log_path, imagepath)
            try:
                self.img.save(imagepath,"JPEG")
            except:
                print("save image error")
                log.writeLog(self.log_path, "save image error")
            self.plate.pbox = []
            self.rect_num = 0
            # log.writeLog(self.log_path, "load image")
            self.loadImage()
            # log.writeLog(self.log_path, "erase block ok")

    def loadPlateCache(self, event=None):
        if 0 == len(self.plate_cache):
            return
        p_last = ''
        for c in self.plate_cache[self.cacheIdx]:
            p_last += c
        self.pnumber_entry.delete(0,END)
        self.pnumber_entry.insert(0,p_last)
        self.cacheIdx -= 1
        if self.cacheIdx < -len(self.plate_cache):
            self.cacheIdx = -1

##    def setImage(self, imagepath = r'test2.png'):
##        self.img = Image.open(imagepath)
##        self.tkimg = ImageTk.PhotoImage(self.img)
##        self.mainPanel.config(width = self.tkimg.width())
##        self.mainPanel.config(height = self.tkimg.height())
##        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width=True, height=True)
    root.mainloop()
