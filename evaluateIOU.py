import os
import sys
from shapely.geometry import box

def getBoxes(fl_path):
    fl = open(fl_path, "r")
    boxes = []
    for line in fl:
        line = [int(x) for x in line.rstrip().split("\t")]
        boxes.append(box(line[0], line[1], line[0] + line[2], line[1] + line[3]))
    return boxes

def getFigure(boxes):
    fig = boxes[0]
    for i in range(1, len(boxes)):
        fig = fig.union(boxes[i])

    return fig

def meanIou(fig1, fig2):
    return fig1.intersection(fig2).area/fig1.union(fig2).area
