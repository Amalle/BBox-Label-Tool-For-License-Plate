#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label Plate box
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

# colors for the bboxes
COLORS = ['red', 'blue', 'PaleVioletRed', 
          'DeepPink', 'Plum', 'Brown', 'Thistle', 'Orchid']
PLATE_COLOR = ["白底黑字","白底红字","红底白字","绿底白字","白底绿字","黄底黑字","蓝底白字"]
# image sizes for the examples
WIDTH = 1600
HEIGHT = 900

class LabelTool():
    def __init__(self, master):
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
        self.convas_w = WIDTH    #画布宽
        self.convas_h = HEIGHT    #画布高
        self.imageDir = ''
        self.loadConf()

        # display scale
        self.scale_x = 1
        self.scale_y = 1
        self.scale_W = self.convas_w
        self.scale_H = self.convas_h

        # rect number
        self.rect_num = 0  #rects of plate and charactors 6~8
        self.rect_min = 6
        self.rect_max = 8

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
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.cboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # Plate number
        self.plate = xp.Plate()
        self.plate_cache = []  #存放最近标记过的车牌号码（最多5个，不重复）
        self.cacheIdx = 0  # plate cache index

        # Plate color
        self.plate_color = ''

        # Clear 
        self.clear = False

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
        self.mainPanel.bind("<Button-3>", self.cancelBBox)
        self.mainPanel.bind("<Motion>", self.mouseMove)
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
        self.pnumber = Label(self.rightPanel, text=self.la.plate_number)
        self.pnumber.pack(side=TOP, expand=YES, fill=X)
        e = StringVar() 
        self.pnumber_entry = Entry(self.rightPanel, textvariable=e)
        self.pnumber_entry.pack(side=TOP, expand=YES, fill=X)

        self.pcolor = Label(self.rightPanel, text=self.la.plate_color)
        self.pcolor.pack(side=TOP, expand=YES, fill=X)
        color_value = StringVar() 
        self.pcolor_list = ttk.Combobox(self.rightPanel, textvariable=color_value)
        self.pcolor_list['values'] = tuple(PLATE_COLOR)
        self.pcolor_list.current(0)
        self.pcolor_list.bind("<<ComboboxSelected>>", self.selectPlateColor)
        self.pcolor_list.pack(side=TOP, expand=YES, fill=X)

        self.lb1 = Label(self.rightPanel, text=self.la.label_list)
        self.lb1.pack(side=TOP, expand=YES, fill=X)
        self.listbox = Listbox(self.rightPanel, width=30, height=20)
        self.listbox.bind("<ButtonRelease-1>", self.selectPlateList)
        self.listbox.pack(side=TOP, expand=YES, fill=X)
        self.btnDel = Button(self.rightPanel, text=self.la.clear, command=self.delBBox)
        self.btnDel.pack(side=TOP, expand=YES, fill=X)
        self.btnClear = Button(self.rightPanel, text=self.la.clear_all, command=self.clearAll)
        self.btnClear.pack(side=TOP, expand=YES, fill=X)
        self.btnDeleteImage = Button(self.rightPanel, text=self.la.delete_image, command=self.deleteImage)
        self.btnDeleteImage.pack(side=TOP, expand=YES, fill=X)

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

        # for debugging
##        self.setImage()
##        self.loadDir()

        if self.isloadconfsuccess:
            self.loadDir()

    def selectPlateColor(self,event=None):
        self.plate_color = self.pcolor_list.get()

    def selectPlateList(self, event=None):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.selectedListboxId = idx
        self.pnumber_entry.delete(0,END)
        plate_number = ""
        plate_number = plate_number.join(self.plate.plateLists[idx][1])
        self.pnumber_entry.insert(0,plate_number)
        self.pcolor_list.current(PLATE_COLOR.index(self.plate.plateLists[idx][4]))

    def loadConf(self):
        self.isloadconfsuccess = False
        file_dir = os.path.abspath(self.config_file)
        if os.path.exists(file_dir):
            fl = open(file_dir,"r")
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
                if 'convas_w' == conf_name:
                    if 0 != len(conf_value):
                        self.convas_w = int(conf_value)
                    else:
                        self.convas_w = WIDTH
                if 'convas_h' == conf_name:
                    if 0 != len(conf_value):
                        self.convas_h = int(conf_value)
                    else:
                        self.convas_h = HEIGHT
                # if 'language' == conf_name:
                #     if 0 != len(conf_value):
                #         self.language = conf_value
                #     else:
                #         self.language = DEFAULT_LANGUAGE

            fl.close()

    def writeConf(self):
        file_dir = os.path.abspath(self.config_file)
        f = open(file_dir,"w")
        txt_dir = 'image Dir: %s\n' % (self.imageDir)
        f.write(txt_dir)
        txt_w = 'convas_w: %d\n' % (self.convas_w)
        f.write(txt_w)
        txt_h = 'convas_h: %d' % (self.convas_h)
        f.write(txt_h)
        # txt_la = 'language: %s' % (self.language)
        # f.write(txt_la)

    def loadDir(self):
        if not self.isloadconfsuccess:
            # chose image dir 
            self.imageDir = askdirectory()
            self.writeConf()
        else:
            self.isloadconfsuccess = False
        self.et.set(self.imageDir)

        # get image list
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        print(self.imageDir)
        if len(self.imageList) == 0:
            print('No .jpg images found')
            self.cur = 0
            self.total = len(self.imageList)
            self.mainPanel.delete('all')
            self.progLabel.config(text="%04d/%04d" %(self.cur, self.total))
            self.clearAll()
        else:
            # default to the 1st image in the collection
            self.cur = 1
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
        self.img = Image.open(imagepath)

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
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.xml'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        self.plate.plateLists = []
        if os.path.exists(self.labelfilename):
            self.plate.readXml(self.labelfilename)
        self.showLabel()
            
    def showLabel(self):
        self.clearBBox()
        plate_lists = self.plate.plateLists
        p_num = 0
        if self.isCrop:
            if self.isEnlarge: 
                idx = self.selectedListboxId
                chars = plate_lists[idx][1]
                pbox = plate_lists[idx][2]
                cboxes = plate_lists[idx][3]
                x1 = int((pbox[0] - self.crop_box[0])/(self.scale_x*self.crop_rate_x))
                y1 = int((pbox[1] - self.crop_box[1])/(self.scale_y*self.crop_rate_y))
                x2 = int((pbox[2] - self.crop_box[0])/(self.scale_x*self.crop_rate_x))
                y2 = int((pbox[3] - self.crop_box[1])/(self.scale_y*self.crop_rate_y))
                color = COLORS[p_num+1 % len(COLORS)]
                tmpId = self.mainPanel.create_rectangle(x1, y1, x2, y2, width=2, outline=color)
                self.bboxIdList.append(tmpId)
                self.listbox.insert(END, '%s (%d, %d)->(%d, %d)' %("".join(chars), x1, y1, x2, y2))
                self.listbox.itemconfig(p_num, fg=color)
                cboxId = []
                for cbox in cboxes:
                    x1 = int((cbox[0] - self.crop_box[0])/(self.scale_x*self.crop_rate_x))
                    y1 = int((cbox[1] - self.crop_box[1])/(self.scale_y*self.crop_rate_y))
                    x2 = int((cbox[2] - self.crop_box[0])/(self.scale_x*self.crop_rate_x))
                    y2 = int((cbox[3] - self.crop_box[1])/(self.scale_y*self.crop_rate_y))
                    tmpId = self.mainPanel.create_rectangle(x1, y1, x2, y2, width=1, outline=color)
                    cboxId.append(tmpId)
                self.cboxIdList.append(cboxId)
        else:
            for plate in plate_lists:
                char_num = plate[0]
                chars = plate[1]
                pbox = plate[2]
                cboxes = plate[3]
                x1 = int(pbox[0]/self.scale_x)
                y1 = int(pbox[1]/self.scale_y)
                x2 = int(pbox[2]/self.scale_x)
                y2 = int(pbox[3]/self.scale_y)
                color = COLORS[p_num+1 % len(COLORS)]
                tmpId = self.mainPanel.create_rectangle(x1, y1, x2, y2, width=2, outline=color)
                self.bboxIdList.append(tmpId)
                self.listbox.insert(END, '%s (%d, %d)->(%d, %d)' %("".join(chars), x1, y1, x2, y2))
                self.listbox.itemconfig(p_num, fg=color)
                cboxId = []
                for cbox in cboxes:
                    x1 = int(cbox[0]/self.scale_x)
                    y1 = int(cbox[1]/self.scale_y)
                    x2 = int(cbox[2]/self.scale_x)
                    y2 = int(cbox[3]/self.scale_y)
                    tmpId = self.mainPanel.create_rectangle(x1, y1, x2, y2, width=1, outline=color)
                    cboxId.append(tmpId)
                self.cboxIdList.append(cboxId)
                p_num += 1

    def enlargePlate(self, event=None):
        if not self.isEnlarge:
            sel = self.listbox.curselection()
            if len(sel) != 1 :
                return
            idx = int(sel[0])
            self.selectedListboxId = idx
            x1 = self.plate.plateLists[idx][2][0]
            y1 = self.plate.plateLists[idx][2][1]
            x2 = self.plate.plateLists[idx][2][2]
            y2 = self.plate.plateLists[idx][2][3]

            self.isCrop = True
            self.isEnlarge = True
            self.crop_box = (x1-20,y1-20,x2+20,y2+20)
            box_w = self.crop_box[2] - self.crop_box[0]
            box_h = self.crop_box[3] - self.crop_box[1]
            self.crop_rate_x = float(box_w/self.scale_x)/self.scale_W
            self.crop_rate_y = float(box_h/self.scale_y)/self.scale_H
            f,box = cn.checkbox(self.crop_box, self.img.width, self.img.height)
            if f:
                self.crop_box = box
            self.STATE['click'] = 0
        else:
            self.isEnlarge = False
            self.isCrop = False
        self.loadImage()

    def saveImage(self, event=None):
        if 0 == self.cur:
            return
        isPlateAdd = False
        plate_chars = ''
        self.plate_color = self.pcolor_list.get()
        if self.rect_min <= self.rect_num:
            plate_chars = str(self.pnumber_entry.get())
            self.plate.chars = plate_chars
            self.plate.color = self.plate_color
            self.plate.plate = [self.rect_num-1,self.plate.chars,
                                self.plate.pbox,self.plate.cboxes,
                                self.plate.color]
            if False == self.plate.chars.isalnum() or self.rect_num - 1 != len(self.plate.chars):
                messagebox.showerror("Plate", "车牌格式错误(The format of plate is error! )")
                return
            self.plate.plateLists.append(self.plate.plate)
            self.rect_num = 0
            self.plate.chars = []
            self.plate.pbox = []
            self.plate.cboxes = []
            self.plate.color = ''
            self.selectedListboxId = -1
            isPlateAdd = True
        
        # modify plate
        if self.selectedListboxId > -1 and not self.clear:
            plate_chars = str(self.pnumber_entry.get())
            if False == plate_chars.isalnum() or \
                self.plate.plateLists[self.selectedListboxId][0] != len(plate_chars):
                messagebox.showerror("Plate", "车牌格式错误(The format of plate is error! )")
                return
            self.plate.plateLists[self.selectedListboxId][1] = plate_chars
            self.plate.plateLists[self.selectedListboxId][4] = self.plate_color
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

        if self.clear:
            self.clear = False

        

        if 0 != len(self.plate.plateLists):
            self.plate.writeXml(self.labelfilename)
        else:
            if os.path.exists(self.labelfilename):
                os.remove(self.labelfilename)

        self.entry.delete(0,END)
        self.isCrop = False
        print('Image No. %d saved' %(self.cur))
        self.loadImage()

    def mouseClick(self, event):
        if 0 == self.cur:
            return
        box = []
        iscboxout = False
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
            self.pnumber_entry.delete(0,END)
            self.pcolor_list.current(0)
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            if self.isCrop:
                x1 = self.crop_box[0] + x1*self.crop_rate_x*self.scale_x
                x2 = self.crop_box[0] + x2*self.crop_rate_x*self.scale_x
                y1 = self.crop_box[1] + y1*self.crop_rate_y*self.scale_y
                y2 = self.crop_box[1] + y2*self.crop_rate_y*self.scale_y
            else:
                x1 = x1*self.scale_x
                x2 = x2*self.scale_x
                y1 = y1*self.scale_y
                y2 = y2*self.scale_y
            box = [int(x1), int(y1), int(x2), int(y2)]
            if 0 == self.rect_num:
                self.bboxIdList.append(self.bboxId)
            elif self.rect_max > self.rect_num:
                self.cboxIdList.append(self.bboxId)
            else:
                self.mainPanel.delete(self.bboxId)
                self.rect_num -= 1
                iscboxout = True
            self.bboxId = None
            self.rect_num += 1
        self.STATE['click'] = 1 - self.STATE['click']
        if iscboxout:
            return
        if 1 == self.rect_num and 0 == self.STATE['click']:
            self.plate.pbox = box
            self.listbox.insert(END, '(%d,%d)->(%d,%d)' %(box[0], box[1], box[2], box[3]))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg='red')
        elif 1 < self.rect_num and self.rect_num <= self.rect_max:
            if 0 == self.STATE['click']:
                self.plate.cboxes.append(box)

    def mouseClickUp(self, event):
        if self.isCrop or self.rect_num != 0:
            return
        if 1 == self.STATE['click']:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            box_w = x2 - x1
            box_h = y2 - y1
            if box_w > 20 and box_h > 20:
                self.isCrop = True
                self.crop_rate_x = float(box_w)/self.scale_W
                self.crop_rate_y = float(box_h)/self.scale_H
                self.crop_box = (int(x1*self.scale_x),int(y1*self.scale_y),
                                 int(x2*self.scale_x),int(y2*self.scale_y))
                self.STATE['click'] = 0
                self.loadImage()

    def mouseMove(self, event):
        self.disp.config(text='x: %d, y: %d' %(event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width=2, fill='red')
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width=2, fill='red')
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                        event.x, event.y, width=2, \
                                                        outline='red')

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0
        elif 0 == self.STATE['click']:
            if self.rect_num > 0:
                if self.rect_num > 1:
                    self.plate.cboxes.pop()
                    self.mainPanel.delete(self.cboxIdList[len(self.cboxIdList)-1])
                    self.cboxIdList.pop()
                else:
                    self.plate.pbox = []
                    self.mainPanel.delete(self.bboxIdList[len(self.bboxIdList)-1])
                    self.bboxIdList.pop()
                    self.listbox.delete(self.rect_num-2)
                self.rect_num -= 1
            else:
                self.isCrop = False
                self.loadImage()

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        for cboxId in self.cboxIdList[idx]:
            self.mainPanel.delete(cboxId)
        self.cboxIdList.pop(idx)
        self.listbox.delete(idx)

        self.plate.plateLists.pop(idx)
        #self.showLabel()
        # self.mainPanel.delete(self.bboxIdList[idx])
        # self.bboxIdList.pop(idx)
        # self.bboxList.pop(idx)
        # self.listbox.delete(idx)
        self.clear = True

    def clearAll(self):
        self.plate.plateLists = []
        for idx in range(len(self.bboxIdList)):
            for cdx in range(len(self.cboxIdList[idx])):
                self.mainPanel.delete(self.cboxIdList[idx][cdx])
        self.clearBBox()
        self.clear = True

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

    def clearBBox(self):
        self.listbox.delete(0, len(self.bboxIdList))
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList = []
        self.cboxIdList = []

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
            

    def nextImage(self, event = None):
        #self.saveImage()
        self.isCrop = False
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()
            self.clearLabelingBox()

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
            self.imagename = os.path.split(imagepath)[-1].split('.')[0]
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
        if 1 == self.rect_num and 0 == self.STATE['click']:
            box = (self.plate.pbox[0], self.plate.pbox[1], self.plate.pbox[2], self.plate.pbox[3])
            bw = box[2] - box[0]
            bh = box[3] - box[1]
            img_block = Image.new("RGB",(bw,bh),(0,0,0))
            self.img.paste(img_block,box)
            imagepath = self.imageList[self.cur - 1]
            self.img.save(imagepath,"JPEG")
            self.plate.pbox = []
            self.rect_num = 0
            self.loadImage()

    def loadPlateCache(self, event=None):
        if 0 == len(self.plate_cache):
            return
        self.pnumber_entry.delete(0,END)
        self.pnumber_entry.insert(0,self.plate_cache[self.cacheIdx])
        self.cacheIdx += 1
        if self.cacheIdx > len(self.plate_cache) - 1:
            self.cacheIdx = 0

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
