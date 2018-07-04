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
        if mark_node is None:
            return
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
                E1.color(color)
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

# p = Plate()
# p.readXml('test/LPR_428.xml')
# p.writeXml('test/xml.xml')

# p.printPlate()
# print(p.plateLists)