
# -*- coding:utf-8 -*-

import cv2
import numpy as np

SrcImg = cv2.imread('../test/LPR_428.jpg')

SrcPoints = np.float32([[202,122],[468,106],[499,197],[239,215]])
CanvasPoints = np.float32([[0,0],[300,0],[300,300],[0,300]])

Img = SrcImg.copy()
cv2.imshow('Src', Img)

SrcPointsA = np.array(SrcPoints, dtype=np.float32)
CanvasPointsA = np.array(CanvasPoints, dtype=np.float32)

PerspectiveMatrix = cv2.getPerspectiveTransform(np.array(SrcPointsA),
                                                np.array(CanvasPointsA))
print(PerspectiveMatrix)
PerspectiveImg = cv2.warpPerspective(Img, PerspectiveMatrix, (300, 300))
cv2.imshow('PerspectiveImg', PerspectiveImg)

# coor = np.array([ [498.],  [196.], [1.]])
# ro_coor = np.dot(PerspectiveMatrix,coor)
# print(coor)
# print(ro_coor)

import plate_recog as pr

char_points = [
    [[227,143],[252,141],[271,197],[247,199]],
    [[260,142],[284,139],[305,195],[277,198]],
    [[306,137],[334,134],[354,192],[324,195]],
    [[342,134],[370,132],[386,188],[359,190]],
    [[376,132],[402,131],[420,186],[390,187]],
    [[407,131],[434,131],[447,187],[428,186]],
    [[446,128],[464,127],[482,184],[464,184]],
]
plr = pr.Plate_recog('detection')
if plr.init():
        
    chars,probs = plr.recogize(Img,SrcPoints,char_points)

    print(chars)
    print(probs)