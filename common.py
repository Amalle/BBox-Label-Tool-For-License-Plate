import os

def checkbox(box, w, h):
    x_left = box[0]
    y_top = box[1]
    x_right = box[2]
    y_bottom = box[3]
    ismodify = False
    if x_left < 0:
        x_left = 0
        ismodify = True
    if y_top < 0:
        y_top = 0
        ismodify = True
    if x_right > w - 1:
        x_right = w - 1
        ismodify = True
    if y_bottom > h - 1:
        y_bottom = h - 1
        ismodify = True

    return ismodify,[x_left,y_top,x_right,y_bottom]

def getFileNameFromPath(file_path):
    filename = os.path.split(file_path)[-1]
    img_type = filename.split('.')[-1]
    type_len = len(img_type)+1
    filename = filename[0:-type_len]
    return filename

def overlap(x1, w1, x2, w2):
    l1 = x1 - w1/2.
    l2 = x2 - w2/2.
    left = l1 if l1 > l2 else l2
    r1 = x1 + w1/2.
    r2 = x2 + w2/2.
    right = r1 if r1 < r2 else r2
    return right - left

def box_intersection(box1, box2):
    w = overlap(box1[0],box1[2],box2[0],box2[2])
    h = overlap(box1[1],box1[3],box2[1],box2[3])
    if w < 0 or h < 0:
        return 0
    area = w*h
    return area

def box_union(box1, box2):
    i = box_intersection(box1,box2)
    u = box1[2]*box1[3] + box2[2]*box2[3] - i
    return u

def box_iou(box1, box2):
    return box_intersection(box1,box2)/box_union(box1,box2)

def InPolygon(point, polygon_pts):
    nCross = 0
    nCount = len(polygon_pts)
    for i in range(nCount):
        p1 = polygon_pts[i]
        p2 = polygon_pts[(i+1)%nCount]
        # 求解y=point.y与p1、p2的交点
        if point[1] < min(p1[1],p2[1]):   # 交点在p1、p2的延长线上
            continue
        if point[1] > max(p1[1],p2[1]):   # 交点在p1、p2的延长线上
            continue
        # 求交点的 X 坐标 --------------------------------------------------------------
        x = (point[1] - p1[1])*(p2[0] - p1[0]) / (p2[1] - p1[1]) + p1[0]
        if x > point[0]:
            nCross += 1    # 只统计单边交点
    # 单边交点为偶数，则点在多边形之外
    return nCross%2 == 1
