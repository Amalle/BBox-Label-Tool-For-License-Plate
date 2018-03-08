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