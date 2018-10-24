# license_plate_chars[] = { "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F",  //16
#                           "G", "H", "J", "K", "L", "M", "N", "P", "Q", "R", "S", "T", "U", "V", "W",  //15
# 						  "X", "Y", "Z","桂", "贵", "冀", "吉", "京", "琼", "陕", "苏", "湘", "渝", "豫",  //14
# 						  "藏", "川", "鄂", "甘", "赣", "黑", "沪", "津", "晋", "鲁", "蒙", "闽", "宁",    //13
# 						  "青", "使", "皖", "新", "粤", "云", "浙", "辽", "军", "空", "兰", "广", "海",    //13
# 						  "成", "济", "北", "学", "警", "港", "澳", "赛", "领", "挂", "WJ" }; //11

import cv2
import yolo as yolo
from PIL import Image
import numpy as np
import plate_chars_dict

pr = yolo.Yolo()

# # classify
# cfg_file = b"mnist.cfg"
# weights_file = b"mnist_2840.weights"

# detection
cfg_file = b"yolov2-tiny-TW-char.cfg"
weights_file = b"yolov2-tiny-TW-char.weights"

is_plr = pr.init(cfg_file,weights_file,'detection')
if is_plr:
	img1 = cv2.imread("0.jpg")
	img = Image.open("p1.jpg")
	# img.save("im.jpg")
	img = np.array(img,np.uint8)
	img = img[:,:,(2,1,0)]
	wh = img.shape
	
	# obj_cls,prob = pr.classify(img,wh[1],wh[0])
	# print(chars.PLATE_CHARS_CN[obj_cls])
	# print(prob)

	img_show = img.copy()
	img_show = cv2.resize(img_show,(wh[1]*10,wh[0]*10))
	isdet,objs = pr.detect(img_show,wh[1]*10,wh[0]*10)

	if isdet > 0:
		for obj in objs:
			cv2.rectangle(img_show,(obj[0],obj[1]),(obj[0]+obj[2],obj[1]+obj[3]),(255,0,0),2)
			txt = "%d"%(obj[5])
			cv2.putText(img_show,txt,(obj[0],obj[1]),2,2,(0,255,0))
			print(obj)
		
		cv2.imshow("im",img_show)
		cv2.waitKey()
else:
	print("init error")

