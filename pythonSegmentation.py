from PIL import Image
import cv2
import sys
import locale
locale.setlocale(locale.LC_ALL, 'C')
from tesserocr import PyTessBaseAPI, RIL
import numpy as np
"""
Usage : python pythonSegmentation.py image_file segment_file outputType
image_file - Path to image file for which segmentation is to be performed
segment_file - Path to text file on which segmentation result is to be stored
outputType - Tells which type of segmentation to be performed
            1 : Blocks segmentation
            2 : Line segmentation
            3 : Word segmentation
"""
def runSegmentation(img_fl, seg_fl, output_type):
    image_file = img_fl
    segment_file = seg_fl
    outputType = output_type

    image = Image.open(image_file)



    with PyTessBaseAPI() as api:
        api.SetImage(image)
        segment_fl = open(segment_file, "w+")

        if outputType == 1:
            blocks = api.GetComponentImages(RIL.BLOCK, True)
        elif outputType == 2:
            blocks = api.GetComponentImages(RIL.TEXTLINE, True)
        else:
            blocks = api.GetComponentImages(RIL.WORD, True)
        
        for i, (im, box, _, _) in enumerate(blocks):
            # im is a PIL image object
            # box is a dict with x, y, w and h keys
            api.SetRectangle(box['x'], box['y'], box['w'], box['h'])
            segment_fl.write("{x}\t{y}\t{w}\t{h}\n".format(x=box['x'], y=box['y'], w=box['w'], h=box['h']))

