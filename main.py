import cv2
import os
import sys
import findBestAngle
import borderRemoval
import lineMerge
import pythonSegmentation

def fixSkew(img_fl, save_fl):
    angle = findBestAngle.findAngleMinArea(img_fl)
    newImg = findBestAngle.rotateImage(img_fl, angle)
    cv2.imwrite(save_fl, newImg)

def fixBorder(img_fl, line_fl, save_fl):
    borderRemoval.removeAnsSave(img_fl, line_fl, save_fl)

def fixLineMerge(line_fl, out_fl):
    newLines, _ = lineMerge.mergeLines(line_fl)
    
    out_fl = open(out_fl, "w+")
    for line in newLines:
        new_fl.write("{a}\t{b}\t{c}\t{d}\n".format(a = line[0], b = line[1], c = line[2], d = line[3]))



if __name__ == "__main__":
    sz = len(sys.argv)
    if sz < 3:
        print("Usage: python main.py [OPTIONS] image_file line_file")
        print("Options:-\n-b include border removal\n-s include skew correction\n-l include line merge")
        exit()

    if not os.path.isfile(sys.argv[-2]):
        print("Image file does not exists")
        exit()

    if not os.path.isfile(sys.argv[-1]):
        print("Line Segmentation file does not exist")
        exit()

    actSkew = False
    actBord = False
    actMerge = False

    if "-b" in sys.argv:
        actBord = True
    
    if "-s" in sys.argv:
        actSkew = True

    if "-l" in sys.argv:
        actMerge = True

    tempFile = sys.argv[-2]

    if actSkew:
        fixSkew(sys.argv[-2], "temp_skew.png")
        tempFile = "temp_skew.png"

    if actBord:
        fixBorder(tempFile, sys.argv[-1], "temp.png")
        tempFile = "temp.png"

    if actMerge:
        pythonSegmentation.runSegmentation(tempFile, "temp_seg.txt", 2)
        fixLineMerge("temp_seg.txt", "final_seg.txt")
        exit()

    pythonSegmentation.runSegmentation(tempFile, "final_seg.txt", 2)


    





