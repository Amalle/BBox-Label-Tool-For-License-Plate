import os

class Language:
    def __init__(self, language_mode):
        # language mode
        self.language_mode = language_mode

        #label
        self.image_dir = ''
        self.plate_number = ''
        self.plate_color = ''
        self.label_list = ''
        self.goto_id = ''

        #button
        self.save = ''
        self.prev = ''
        self.next = ''
        self.index = ''
        self.go = ''
        self.clear = ''
        self.clear_all = ''
        self.delete_image = ''
        self.load = ''
        self.goto_unlabel = ''
        self.enlarge = ''
        self.erase_block = ''
        self.load_plate_cache = ''

        # set language
        self.setLanguage()

    def setLanguage(self):
        if self.language_mode == 'EN':
            #label
            self.image_dir = 'Image Dir'
            self.plate_number = 'Plate Number'
            self.plate_color = 'Plate Color'
            self.label_list = 'Label list'
            self.goto_id = 'Go to Image No.'

            #button
            self.save = 'Save(F2)'
            self.prev = '<<Prev(F1)'
            self.next = 'Next>>(F3)'
            self.index = 'Index'
            self.go = 'Go'
            self.clear = 'Clear'
            self.clear_all = 'ClearAll'
            self.delete_image = 'Delete Image'
            self.load = 'Load'
            self.goto_unlabel = 'GotoUnlabel'
            self.enlarge = 'Enlarge(F5)'
            self.erase_block = 'EraseBlock(F6)'
            self.load_plate_cache = 'LoadPLateCache(F7)'
        elif self.language_mode == 'CN':
            #label
            self.image_dir = '图片路径'
            self.plate_number = '车牌号码'
            self.plate_color = '车牌颜色'
            self.label_list = '标注列表'
            self.goto_id = '跳转到'

            #button
            self.save = '保存(F2)'
            self.prev = '<<上一张(F1)'
            self.next = '下一张>>(F3)'
            self.index = '图片索引'
            self.go = '跳转'
            self.clear = '删除选中车牌'
            self.clear_all = '删除全部车牌'
            self.delete_image = '删除图片'
            self.load = '打开'
            self.goto_unlabel = '跳过已标注图片'
            self.enlarge = '放大(F5)'
            self.erase_block = '涂黑(F6)'
            self.load_plate_cache = '载入最近车牌(F7)'