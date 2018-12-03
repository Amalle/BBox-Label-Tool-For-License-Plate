from lxml import etree, objectify
import os,glob
import xml.etree.ElementTree as ET

# import cv2

class Plate:
    def __init__(self):
        self.char_num = 0     #车牌字符数
        self.chars = []       #车牌号的所有字符
        self.pbox = []        #车牌的box
        self.cboxes = []       #车牌各个字符的box
        self.color = []      #车牌的颜色
        self.layer = []      #车牌的层数

        self.folder = []
        self.image_name = []
        self.imgW = 0
        self.imgH = 0

        self.plate = []       #车牌结构
        self.plateLists = []  #所有车牌

        self.xml_mode = 1  #xml标注格式：0-老版格式， 1-新版格式

    def printPlate(self):
        for pl in self.plateLists:
            for p in pl:
                print(p)

    def readXml(self,xmlfile):
        tree = ET.parse(xmlfile)
        root = tree.getroot()

        self.plateLists = []

        mark_node = root.find("markNode")
        if mark_node is None:
            if root.tag != 'annotation':
                return False
            else:
                self.xml_mode = 0
                self.readOldXml(xmlfile)
                return True
        obj = mark_node.find("object")
        if None != obj:
            for obj in mark_node.iter("object"):
                pbox = []
                chars = []
                cboxes = []
                color = ''
                layer = ''
                char_num = 0
                trunc = 0

                if 'plate' != obj.find('targettype').text:
                    continue
                cr = obj.find("color")
                if None != cr:
                    color = cr.text
                la = obj.find("mode")
                if None != la:
                    layer = la.text
                tc = obj.find('truncated')
                if None != tc:
                    if not tc.text is None:
                        trunc = int(tc.text)
                vertexs = obj.find("vertexs")
                if None != vertexs:
                    vertex = vertexs.find('vertex')
                    if None != vertex:
                        for ver in vertexs.iter('vertex'):
                            x = int(ver.find('x').text)
                            y = int(ver.find('y').text)
                            pbox.append([x,y])
                characters = obj.find('characters')
                if None != characters:
                    char = characters.find('char')
                    if None != char:
                        for char in characters.iter('char'):
                            c = char.find('data').text
                            chars.append(c)
                            vertex = char.find('vertex')
                            if None != vertex:
                                cbox = []
                                for ver in char.iter('vertex'):
                                    x = int(ver.find('x').text)
                                    y = int(ver.find('y').text)
                                    cbox.append([x,y])
                                char_num += 1
                                cboxes.append(cbox)
                plate = [char_num,chars,pbox,cboxes,color,layer,trunc]
                self.plateLists.append(plate)
        return True

    def readOldXml(self,xmlfile):
        tree = ET.parse(xmlfile)
        root = tree.getroot()

        self.plateLists = []

        if root.tag != 'annotation':
            return False

        folder_ = root.find('folder')
        if folder_ is not None:
            self.folder = folder_.text
        image_name_ = root.find('ImageName')
        if image_name_ is not None:
            self.image_name = image_name_.text

        size = root.find('size')
        if size is None:
            return False
        self.imgW = int(size.find('width').text)
        self.imgH = int(size.find('height').text)
        obj = root.find('object')
        if obj is None:
            return False
        plate = obj.find('plate')
        if plate is None:
            return False

        for p in obj.iter('plate'):
            pbox = []
            chars = []
            cboxes = []
            color = ''
            layer = ''
            char_num = 0
            trunc = 0

            cr = p.find('color')
            if cr != None:
                color = cr.text
            la = p.find('mode')
            if la != None:
                layer = la.text
            tc = p.find('truncated')
            if tc != None:
                if not tc.text is None:
                    trunc = int(tc.text)

            vertexs = p.find('vertexs')
            if vertexs is None:
                vertex = p.find('vertex')
                if vertex is None:
                    return False
                else:
                    vertexs = p
                
            count = 0
            for ver in vertexs.iter('vertex'):
                x = int(ver.find('x').text)
                y = int(ver.find('y').text)
                pbox.append([x,y])
                count += 1
                if count == 4:
                    break
            characters = p.find('characters')
            if characters is None:
                return False
            char = characters.find('c')
            if char is None:
                return False
            for char in characters.iter('c'):
                c = char.find('data').text
                if c is None:
                    return False
                chars.append(c)
                vertex = char.find('vertex')
                if None != vertex:
                    cbox = []
                    for ver in char.iter('vertex'):
                        x = int(ver.find('x').text)
                        y = int(ver.find('y').text)
                        cbox.append([x,y])
                    char_num += 1
                    cboxes.append(cbox)
            plate = [char_num,chars,pbox,cboxes,color,layer,trunc]
            self.plateLists.append(plate)
        return True
        
    def writeXml(self,xmlfile, imgW, imgH, imgD):
        if self.xml_mode == 0:
            self.writeOldXml(xmlfile, imgW, imgH, imgD)
            return
        E = objectify.ElementMaker(annotate=False)
        anno_tree = E.dataroot(
            E.folder(self.folder),
            E.filename(self.image_name),
            E.createdata(''),
            E.modifydata(''),
            E.width(imgW),
            E.height(imgH),
            E.depth(imgD),
            E.DayNight(''),
            E.weather(''),
            E.Marker(''),
            E.location(''),
            E.imageinfo(''),
            E.source(''),
            E.database('')
        )

        E3 = objectify.ElementMaker(annotate=False)
        anno_tree3 = E3.markNode()

        for plate in self.plateLists:
            char_num = plate[0]
            chars = plate[1]
            pbox = plate[2]
            cboxes = plate[3]
            color = plate[4]
            layer = plate[5]
            trunc = plate[6]
            E1 = objectify.ElementMaker(annotate=False)
            anno_tree1 = E1.object(
                E1.targettype('plate'),
                E1.cartype(''),
                E1.pose(''),
                E1.truncated(trunc),
                E1.difficult(''),
                E1.remark(''),
                E1.color(color),
                E1.mode(layer)
            )

            E5 = objectify.ElementMaker(annotate=False)
            anno_tree5 = E5.vertexs()

            for i in range(0,4):
                E6 = objectify.ElementMaker(annotate=False)
                anno_tree6 = E6.vertex(
                    E6.x(pbox[i][0]),
                    E6.y(pbox[i][1])
                )
                anno_tree5.append(anno_tree6)
            anno_tree1.append(anno_tree5)

            E4 = objectify.ElementMaker(annotate=False)
            anno_tree4 = E4.characters()

            for i in range(0,len(chars)):
                E2 = objectify.ElementMaker(annotate=False)
                c = chars[i]
                if c.isalnum():
                    c = chars[i].upper()
                anno_tree2 = E2.char(
                    E2.data(c),
                )
                for j in range(0,4):
                    if i < len(cboxes):
                        E7 = objectify.ElementMaker(annotate=False)
                        anno_tree7 = E7.vertex(
                            E7.x(cboxes[i][j][0]),
                            E7.y(cboxes[i][j][1])
                        )
                    else:
                        E7 = objectify.ElementMaker(annotate=False)
                        anno_tree7 = E7.vertex(
                            E7.x(0),
                            E7.y(0)
                        )
                    anno_tree2.append(anno_tree7)
                anno_tree4.append(anno_tree2)
            anno_tree1.append(anno_tree4)
            anno_tree3.append(anno_tree1)
        anno_tree.append(anno_tree3)

        etree.ElementTree(anno_tree).write(xmlfile, encoding='utf-8', xml_declaration=True)

    def writeOldXml(self,xmlfile, imgW, imgH, imgD):
        E = objectify.ElementMaker(annotate=False)
        anno_tree = E.annotation(
            E.folder(self.folder),
            E.filename(self.image_name),
            E.createdata(''),
            E.modifydata(''),
            E.segmented('')
        )
        E_source = objectify.ElementMaker(annotate=False)
        anno_tree_source = E_source.source(
            E_source.database(''),
            E_source.annotation(''),
            E_source.image(''),
            E_source.location(''),
            E_source.time('Day'),
            E_source.weather('Sunny')
        )
        anno_tree.append(anno_tree_source)
        E_owner = objectify.ElementMaker(annotate=False)
        anno_tree_owner = E_owner.owner(
            E_owner.name('')
        )
        anno_tree.append(anno_tree_owner)
        E_size = objectify.ElementMaker(annotate=False)
        anno_tree_size = E_size.size(
            E_size.width(imgW),
            E_size.height(imgH),
            E_size.depth(imgD)
        )
        anno_tree.append(anno_tree_size)
           
        E_object = objectify.ElementMaker(annotate=False)
        anno_tree_object = E_object.object(
            E_object.name('Plate'),
            E_object.pose('Front')
        )

        for plate in self.plateLists:
            char_num = plate[0]
            chars = plate[1]
            pbox = plate[2]
            cboxes = plate[3]
            color = plate[4]
            layer = plate[5]
            trunc = plate[6]
            E_plate = objectify.ElementMaker(annotate=False)
            anno_tree_plate = E_plate.plate(
                E_plate.color(color),
                E_plate.mode(layer),
                E_plate.truncated(trunc),
                E_plate.version('')
            )

            E5 = objectify.ElementMaker(annotate=False)
            anno_tree5 = E5.vertexs()

            for i in range(0,4):
                E6 = objectify.ElementMaker(annotate=False)
                anno_tree6 = E6.vertex(
                    E6.x(pbox[i][0]),
                    E6.y(pbox[i][1])
                )
                anno_tree5.append(anno_tree6)
            anno_tree_plate.append(anno_tree5)

            E4 = objectify.ElementMaker(annotate=False)
            anno_tree4 = E4.characters()

            for i in range(0,len(chars)):
                E2 = objectify.ElementMaker(annotate=False)
                c = chars[i]
                if c.isalnum():
                    c = chars[i].upper()
                anno_tree2 = E2.c(
                    E2.data(c),
                )
                for j in range(0,4):
                    if i < len(cboxes):
                        E7 = objectify.ElementMaker(annotate=False)
                        anno_tree7 = E7.vertex(
                            E7.x(cboxes[i][j][0]),
                            E7.y(cboxes[i][j][1])
                        )
                    else:
                        E7 = objectify.ElementMaker(annotate=False)
                        anno_tree7 = E7.vertex(
                            E7.x(0),
                            E7.y(0)
                        )
                    anno_tree2.append(anno_tree7)
                anno_tree4.append(anno_tree2)
            anno_tree_plate.append(anno_tree4)
            anno_tree_object.append(anno_tree_plate)
        anno_tree.append(anno_tree_object)

        etree.ElementTree(anno_tree).write(xmlfile, encoding='utf-8', xml_declaration=True)

    def convertOldXml2New(self,xmlDir):
        xmlList = glob.glob(os.path.join(xmlDir, '*.xml'))
        No = 0
        for xmlfile in xmlList:
            No += 1
            print(str(No)+'/'+str(len(xmlList))+'  '+xmlfile)
            if self.readOldXml(xmlfile):
                self.writeXml(xmlfile)
            # else:
            #     imgfile = xmlfile[:-4] + '.jpg'
            #     if os.path.exists(imgfile):
            #         os.remove(imgfile)
            #     os.remove(xmlfile)

#     def convertXml2Old(self, xmlDir):
#         xmlList = glob.glob(os.path.join(xmlDir, '*.xml'))
#         No = 0
#         for xmlfile in xmlList:
#             No += 1
#             print(str(No)+'/'+str(len(xmlList))+'  '+xmlfile)
#             imgfile = xmlfile[:-4] + '.jpg'
#             if self.readXml(xmlfile):
#                 img = cv2.imread(imgfile)
#                 if img is not None:
#                     for p in self.plateLists:
#                         p[5] = '单'
#                     self.writeOldXml(xmlfile, img.shape[1],img.shape[0],img.shape[2])
#             # else:
#             #     imgfile = xmlfile[:-4] + '.jpg'
#             #     if os.path.exists(imgfile):
#             #         os.remove(imgfile)
#             #     os.remove(xmlfile)

#     # change attribute
#     def convertXml2Xml(self, xmlDir):
#         xmlList = glob.glob(os.path.join(xmlDir, '*.xml'))
#         No = 0
#         for xmlfile in xmlList:
#             No += 1
#             print(str(No)+'/'+str(len(xmlList))+'  '+xmlfile)
#             imgfile = xmlfile[:-4] + '.jpg'
#             if self.readXml(xmlfile):
#                 img = cv2.imread(imgfile)
#                 if img is not None:
#                     # for p in self.plateLists:
#                     #     p[5] = '单'
#                     self.writeXml(xmlfile, img.shape[1],img.shape[0],img.shape[2])
#             # else:
#             #     imgfile = xmlfile[:-4] + '.jpg'
#             #     if os.path.exists(imgfile):
#             #         os.remove(imgfile)
#             #     os.remove(xmlfile)


# p = Plate()
# p.convertXml2Old("F:\\xg\\test1")