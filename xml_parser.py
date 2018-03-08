from lxml import etree, objectify
import os
import xml.etree.ElementTree as ET

class Plate:
    def __init__(self):
        self.char_num = 0     #车牌字符数
        self.chars = []       #车牌号的所有字符
        self.pbox = []        #车牌的box
        self.cboxes = []       #车牌各个字符的box
        self.color = []      #车牌的颜色

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
        obj = mark_node.find("object")
        if None != obj:
            for obj in mark_node.iter("object"):
                pbox = []
                chars = []
                cboxes = []
                color = ''
                char_num = 0

                if 'plate' != obj.find('targettype').text:
                    continue
                cr = obj.find("color")
                if None != cr:
                    color = cr.text
                bndbox = obj.find("bndbox")
                if None != bndbox:
                    xmin = int(bndbox.find("xmin").text)
                    ymin = int(bndbox.find("ymin").text)
                    xmax = int(bndbox.find("xmax").text)
                    ymax = int(bndbox.find("ymax").text)
                    pbox = [xmin,ymin,xmax,ymax]
                characters = obj.find('characters')
                if None != characters:
                    char = characters.find('char')
                    if None != char:
                        for char in characters.iter('char'):
                            c = char.find('data').text
                            chars.append(c)
                            bndbox = char.find('bndbox')
                            cbox = []
                            if None != bndbox:
                                xmin = int(bndbox.find("xmin").text)
                                ymin = int(bndbox.find("ymin").text)
                                xmax = int(bndbox.find("xmax").text)
                                ymax = int(bndbox.find("ymax").text)
                                cbox = [xmin,ymin,xmax,ymax]
                                cboxes.append(cbox)
                                char_num += 1
                plate = [char_num,chars,pbox,cboxes,color]
                self.plateLists.append(plate)
                    
    def writeXml(self,xmlfile):
        E = objectify.ElementMaker(annotate=False)
        anno_tree = E.dataroot(
            E.folder(''),
            E.filename("test.jpg"),
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
            E1 = objectify.ElementMaker(annotate=False)
            anno_tree1 = E1.object(
                E1.targettype('plate'),
                E1.cartype(''),
                E1.pose(''),
                E1.truncated(''),
                E1.difficult(''),
                E1.remark(''),
                E1.color(color),
                E1.bndbox(
                    E1.xmin(pbox[0]),
                    E1.ymin(pbox[1]),
                    E1.xmax(pbox[2]),
                    E1.ymax(pbox[3])
                )
            )

            E4 = objectify.ElementMaker(annotate=False)
            anno_tree4 = E4.characters()

            for i in range(0,char_num):
                cbox = cboxes[i]
                E2 = objectify.ElementMaker(annotate=False)
                anno_tree2 = E2.char(
                    E2.data(chars[i].upper()),
                    E2.bndbox(
                        E2.xmin(cbox[0]),
                        E2.ymin(cbox[1]),
                        E2.xmax(cbox[2]),
                        E2.ymax(cbox[3])
                    )
                )
                anno_tree4.append(anno_tree2)
            anno_tree1.append(anno_tree4)
            anno_tree3.append(anno_tree1)
        anno_tree.append(anno_tree3)

        etree.ElementTree(anno_tree).write(xmlfile, encoding='utf-8', xml_declaration=True)

# p = Plate()
# p.readXml('test/LPR_428.xml')
# p.writeXml('test/xml.xml')

# p.printPlate()
# print(p.plateLists)