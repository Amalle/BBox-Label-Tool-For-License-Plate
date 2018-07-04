import ctypes as ct
import numpy as np
import cv2

#classify
FLOAT84 = ct.c_float*84
class cls_obj(ct.Structure):
    _fields_ = [
        ("cls_num",ct.c_int),
        ("predictions", FLOAT84)
    ]

#detection
class bbox_obj(ct.Structure):
    _fields_ = [
        ("x", ct.c_uint),
        ("y", ct.c_uint),
        ("w", ct.c_uint),
        ("h", ct.c_uint),
        ("prob", ct.c_float),  
        ("obj_id", ct.c_uint)
    ]
BBOX_OBJ50 = bbox_obj*50
class bbox_objs(ct.Structure):
    _fields_ = [
        ("obj_num", ct.c_uint),  
        ("bbox_obj", BBOX_OBJ50)
    ]

class Yolo:
    def __init__(self):
        #import dll
        self.dll = None

        # alg type
        self.alg_classify = 'classify'
        self.alg_detection = 'detection'
        self.alg_type = ''
        
    def loadDll(self):
        # import dll
        try:
            self.dll = ct.cdll.LoadLibrary('Yolo_DLL.dll')
        except:
            return False
        return True

    def init(self, cfg_file, weights_file, alg_type):
        # import dll
        if not self.loadDll():
            return False

        self.alg_type = alg_type

        yolo_ini = self.dll.yolo_init
        yolo_ini.argtypes = [ct.c_char_p,ct.c_char_p]
        yolo_ini.restype = ct.c_bool
        isyoloini = yolo_ini(cfg_file,weights_file)
        return isyoloini

    def classify(self,img,imgw,imgh):
        if self.alg_type != self.alg_classify:
            return -2,0
        if img is None:
            return -1,0
        if not img.flags['C_CONTIGUOUS']:
            img = np.ascontiguousarray(img, dtype=img.dtype)  # 如果不是C连续的内存，必须强制转换
        img_ctypes_ptr = ct.cast(img.ctypes.data, ct.POINTER(ct.c_uint8))   #转换为ctypes，这里转换后的可以直接利用ctypes转换为c语言中的int*，然后在c中使用

        cobj = cls_obj()
        classify = self.dll.Classify
        classify.argtypes = [ct.POINTER(ct.c_uint8),ct.POINTER(cls_obj),ct.c_int,ct.c_int]
        isdet = classify(img_ctypes_ptr,cobj,imgw,imgh)

        cls_max = -1
        prob_max = 0
        for i in range(cobj.cls_num):
            if cobj.predictions[i] > prob_max:
                cls_max = i
                prob_max = cobj.predictions[i]

        return cls_max,prob_max

    def detect(self, img , imgw, imgh):
        if self.alg_type != self.alg_detection:
            return -2,0
        if img is None:
            return -1,0
        if not img.flags['C_CONTIGUOUS']:
            img = np.ascontiguousarray(img, dtype=img.dtype)  # 如果不是C连续的内存，必须强制转换
        img_ctypes_ptr = ct.cast(img.ctypes.data, ct.POINTER(ct.c_uint8))   #转换为ctypes，这里转换后的可以直接利用ctypes转换为c语言中的int*，然后在c中使用

        bobjs = bbox_objs()
        detect = self.dll.Detect
        detect.argtypes = [ct.POINTER(ct.c_uint8),ct.POINTER(bbox_objs),ct.c_int,ct.c_int]
        isdet = detect(img_ctypes_ptr,bobjs,imgw,imgh)
        print(isdet)
        print(bobjs.obj_num)

        objs = []
        for i in range(bobjs.obj_num):
            obj = [bobjs.bbox_obj[i].x,bobjs.bbox_obj[i].y,bobjs.bbox_obj[i].w,bobjs.bbox_obj[i].h,
                   bobjs.bbox_obj[i].prob,bobjs.bbox_obj[i].obj_id]
            print(obj)
            objs.append(obj)
        
        return bobjs.obj_num,objs