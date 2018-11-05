
import numpy as np
import cv2
import yolo as yolo
import plate_chars_dict as pcd
import common as cn

class Plate_recog:
    def __init__(self,alg_type):
        self.img = None
        self.M_perspective = None
        self.img_perspective = None
        self.img_detect = None
        self.src_points = []
        self.dst_points = []
        self.dst_w = 0
        self.dst_h = 0

        # algorithm type: classify or detection
        self.alg_type = alg_type 

        self.pr = []
        self.is_plr = False

        # result 
        self.chars = ''
        self.probs = []

        # thresh for chars box overlap
        self.iou_thresh = 0.3
        # thresh for chars box and  label box
        self.iou_thresh_to_label = 0.05

    def init(self, plate_region):
        # initialize yolo
        if plate_region == '台湾':
            # plate detection for taiwan 
            cfg_file = b"yolov2-tiny-TW-char.cfg"
            weights_file = b"yolov2-tiny-TW-char.weights"
        else:
            # plate detection
            cfg_file = b"yolov3-tiny-char.cfg"
            weights_file = b"yolov3-tiny-char_final.weights"
        self.pr = yolo.Yolo()
        self.is_plr = self.pr.init(cfg_file,weights_file,self.alg_type)
        
        return self.is_plr

    def getBound(self,point4):
        r = point4
        xmin = min(r[0][0],r[1][0],r[2][0],r[3][0])
        ymin = min(r[0][1],r[1][1],r[2][1],r[3][1])
        xmax = max(r[0][0],r[1][0],r[2][0],r[3][0])
        ymax = max(r[0][1],r[1][1],r[2][1],r[3][1])
        return int(xmin),int(ymin),int(xmax),int(ymax)

    def getDstPoint(self):
        xmin,ymin,xmax,ymax = self.getBound(self.src_points)
        w = xmax - xmin
        h = ymax - ymin
        center_x = (xmin+xmax)/2
        center_y = (ymin+ymax)/2
        self.dst_w = w
        self.dst_h = h
        if self.src_points[1][0] > center_x:
            self.dst_points = [[0,0],[w,0],[w,h],[0,h]]
        else:
            self.dst_points = [[0,0],[0,h],[w,h],[w,0]]

    def getImgPerspective(self):
        #pts3 = np.float32([[point_LT[0], point_LT[1]],[point_RT[0], point_RT[1]],[point_LB[0], point_LB[1]],[point_RB[0], point_RB[1]]])
        #pts4 = np.float32([[0,0],[dst_w-1,0],[0,dst_h-1],[dst_w-1,dst_h-1]])
        pts3 = self.src_points
        pts4 = self.dst_points
        self.M_perspective = cv2.getPerspectiveTransform(np.float32(pts3),np.float32(pts4))
        self.img_perspective = cv2.warpPerspective(self.img, self.M_perspective, (self.dst_w,self.dst_h))
        pad_h = int(self.dst_h/10)
        pad_w = int(self.dst_w/10)
        self.img_detect = np.empty((self.dst_h+pad_h*2,self.dst_w+pad_w*2,3),self.img_perspective.dtype)
        self.img_detect[pad_h:self.dst_h+pad_h,pad_w:self.dst_w+pad_w,:] = self.img_perspective
        # cv2.imshow("imgd",self.img_detect)

    def getPointPerspective(self, point):
        p = np.array([point[0],point[1],1])
        ro_p = np.dot(self.M_perspective,p)
        p = [ro_p[0]/ro_p[2], ro_p[1]/ro_p[2]]
        return p

    def rotate_palte(self, chars_roi_points):
        char_img_list = []

        for point0, point1, point2, point3 in chars_roi_points:

            coor = np.array([point0[0],point0[1],1])
            ro_coor = np.dot(self.M_perspective,coor)
            _point0 = [ro_coor[0]/ro_coor[2], ro_coor[1]/ro_coor[2]]

            coor = np.array([[point1[0]],[point1[1]],[1]])
            ro_coor = np.dot(self.M_perspective,coor)
            _point1 = [ro_coor[0]/ro_coor[2], ro_coor[1]/ro_coor[2]]

            coor = np.array([[point2[0]],[point2[1]],[1]])
            ro_coor = np.dot(self.M_perspective,coor)
            _point2 = [ro_coor[0]/ro_coor[2], ro_coor[1]/ro_coor[2]]

            coor = np.array([[point3[0]],[point3[1]],[1]])
            ro_coor = np.dot(self.M_perspective,coor)
            _point3 = [ro_coor[0]/ro_coor[2], ro_coor[1]/ro_coor[2]]

            char_rect = self.getBound([_point0, _point1, _point2, _point3])
            char_xmin, char_ymin, char_xmax, char_ymax = char_rect

            charimg = self.img_perspective[int(char_ymin):int(char_ymax), int(char_xmin):int(char_xmax)]
            
            char_img_list.append(charimg)
            
        return char_img_list

    # def classfiy(self,chars_box):
    #     self.chars = ''
    #     self.probs = []
    #     char_imgs = self.rotate_palte(chars_box)
    #     for im in char_imgs:
    #         im = np.array(im,np.uint8)
    #         # im = im[:,:,(2,1,0)]
    #         wh = im.shape

    #         obj_cls,prob = self.pr.classify(im,wh[1],wh[0])

    #         self.chars += pcd.PLATE_CHARS_CN[obj_cls]
    #         self.probs.append(prob)

    def checkCharsBox(self,chars_box,chars_box_label,probs):
        # mean distance of all chars box center
        minx = 9999
        maxx = 0
        centersx_label = []
        cboxes_label = []
        for box in chars_box_label:
            cbox = box[0:4]
            cbox_ro = []
            for p in cbox:
                cbox_ro.append(self.getPointPerspective(p))
            cboxes_label.append(self.getBound(cbox_ro))
            centerx = (box[0][0]+box[1][0]+box[2][0]+box[3][0])/4
            centersx_label.append(centerx)
            if minx > centerx:
                minx = centerx
            if maxx < centerx:
                maxx = centerx
        mean_dist = (maxx - minx)/float(len(chars_box_label) - 1)

        ind_dels = [False for f in range(len(chars_box))]
        for i in range(len(chars_box)):
            box1 = chars_box[i]
            center_x1 = box1[0] + box1[2]/2
            
            #check char location
            is_location_right = False
            for lbox in cboxes_label:
                iou = cn.box_iou(box1,lbox)
                if iou > 0.05:
                    is_location_right = True
                    break
            if not is_location_right:
                ind_dels[i] = True

            for j in range(i+1,len(chars_box)):
                box2 = chars_box[j]
                iou = cn.box_iou(box1,box2)

                # filter box
                center_x2 = box2[0] + box2[2]/2
                if iou < self.iou_thresh and abs(center_x1 - center_x2) > mean_dist/2:
                    continue
                
                ind = i
                if probs[i] > probs[j]:
                    ind = j
                ind_dels[ind] = True
        return ind_dels

    def detect(self,chars_box_label, plate_region):
        wh = self.img_detect.shape
        img_show = self.img_detect.copy()
        isdet,objs = self.pr.detect(self.img_detect,wh[1],wh[0])
        if isdet > 0:
            print(objs)
            char_boxes = []
            probs = []
            chars = []
            for obj in objs:
                obj_cls = obj[5]
                prob = obj[4]
                box = obj[0:4]
                char_boxes.append(box)
                chars.append(pcd.PLATE_CHARS_CN[obj_cls])
                probs.append(prob)

            ind_dels = self.checkCharsBox(char_boxes,chars_box_label,probs)
            # print(ind_dels)
            self.chars = ''
            self.probs = []
            centers_x = []
            cboxes = []
            chs = []
            for i in range(len(ind_dels)):
                if ind_dels[i]:
                    continue
                cboxes.append(char_boxes[i])
                chs.append(chars[i])
                self.probs.append(probs[i])

            #     print(char_boxes[i])

            #     obj = char_boxes[i]
            #     cv2.rectangle(img_show,(obj[0],obj[1]),(obj[0]+obj[2],obj[1]+obj[3]),(255,0,0),2)
            #     txt = "%c"%(chars[i])
            #     cv2.putText(img_show,txt,(obj[0],obj[1]),2,2,(0,255,0))
            # cv2.imshow('im',img_show)
            # cv2.waitKey()

            # sort chars
            for i in range(len(cboxes)-1):
                for j in range(len(cboxes)-i-1):
                    # print('%f %f'%(cboxes[j][0]+cboxes[j][2]/2,cboxes[j+1][0]+cboxes[j][2]/2))
                    if cboxes[j][0]+cboxes[j][2]/2 > cboxes[j+1][0]+cboxes[j][2]/2:
                        cboxes[j],cboxes[j+1] = cboxes[j+1],cboxes[j]
                        chs[j],chs[j+1] = chs[j+1],chs[j]
                        self.probs[j],self.probs[j+1] = self.probs[j+1],self.probs[j]

            for c in chs:
                self.chars += c

    def recogize(self,img,plate_box,chars_box,plate_region):
        if not self.is_plr:
            return # algorithm initialize error

        # compute perspective matrix and image
        self.img = np.array(img,np.uint8)
        self.img = self.img[:,:,(2,1,0)]
        self.src_points = plate_box
        self.getDstPoint()
        self.getImgPerspective()
        # cv2.imshow("imgp",self.img_perspective)

        
        # # classify each char
        # if self.alg_type == 'classify':
        #     self.classfiy(chars_box)

        # detect each char
        if self.alg_type == 'detection':
            self.detect(chars_box, plate_region)

        return self.chars,self.probs