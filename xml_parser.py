from lxml import etree, objectify
import os,glob
import xml.etree.ElementTree as ET

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
                return
            else:
                self.readOldXml(xmlfile)
                return
        obj = mark_node.find("object")
        if None != obj:
            for obj in mark_node.iter("object"):
                pbox = []
                chars = []
                cboxes = []
                color = ''
                layer = ''
                char_num = 0

                if 'plate' != obj.find('targettype').text:
                    continue
                cr = obj.find("color")
                if None != cr:
                    color = cr.text
                la = obj.find("mode")
                if None != la:
                    color = la.text
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
                plate = [char_num,chars,pbox,cboxes,color,layer]
                self.plateLists.append(plate)

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

            cr = p.find('color')
            if cr != None:
                color = cr.text
            la = p.find('mode')
            if la != None:
                layer = la.text

            vertexs = p.find('vertexs')
            if vertexs is None:
                return False
            for ver in vertexs.iter('vertex'):
                x = int(ver.find('x').text)
                y = int(ver.find('y').text)
                pbox.append([x,y])
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
            plate = [char_num,chars,pbox,cboxes,color,layer]
            self.plateLists.append(plate)
        return True
        
    def writeXml(self,xmlfile):
        E = objectify.ElementMaker(annotate=False)
        anno_tree = E.dataroot(
            E.folder(self.folder),
            E.filename(self.image_name),
            E.createdata(''),
            E.modifydata(''),
            E.width(''),
            E.height(''),
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
            E1 = objectify.ElementMaker(annotate=False)
            anno_tree1 = E1.object(
                E1.targettype('plate'),
                E1.cartype(''),
                E1.pose(''),
                E1.truncated(''),
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

            for i in range(0,char_num):
                cbox = cboxes[i]
                E2 = objectify.ElementMaker(annotate=False)
                anno_tree2 = E2.char(
                    E2.data(chars[i].upper()),
                )
                for j in range(0,4):
                    E7 = objectify.ElementMaker(annotate=False)
                    anno_tree7 = E7.vertex(
                        E7.x(cboxes[i][j][0]),
                        E7.y(cboxes[i][j][1])
                    )
                    anno_tree2.append(anno_tree7)
                anno_tree4.append(anno_tree2)
            anno_tree1.append(anno_tree4)
            anno_tree3.append(anno_tree1)
        anno_tree.append(anno_tree3)

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


# p = Plate()
# p.convertOldXml2New("Z:\\maqiao\\DNN\\MTCNN\\plate_data1\\data")