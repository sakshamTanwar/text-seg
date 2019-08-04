import cv2
import os
import sys
import findBestAngle
import borderRemoval
import lineMerge
import pythonSegmentation

def fixSkew(img_fl, save_fl):
    angle = findBestAngle.findAngleMinArea(img_fl)
    img = cv2.imread(img_fl)
    newImg = findBestAngle.rotateImage(img, angle)
    cv2.imwrite(save_fl, newImg)

def fixBorder(img_fl, line_fl, save_fl):
    borderRemoval.removeAndSave(img_fl, line_fl, save_fl)

def fixLineMerge(line_fl, out_fl):
    lines = lineMerge.getLines(line_fl)
    newLines, _ = lineMerge.mergeLines(lines)
    
    out_fl = open(out_fl, "w+")
    for line in newLines:
        out_fl.write("{a}\t{b}\t{c}\t{d}\n".format(a = line[0], b = line[1], c = line[2], d = line[3]))



if __name__ == "__main__":
    sz = len(sys.argv)
    if sz < 2:
        print("Usage: python main.py [OPTIONS] image_file")
        print("Options:-\n-b include border removal\n-s include skew correction\n-l include line merge")
        exit()

    if not os.path.isfile(sys.argv[-1]):
        print("Image file does not exists")
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


    tempFile = sys.argv[-1]
    segFile = "init_seg.txt"
    pythonSegmentation.runSegmentation(tempFile, segFile, 2)

    if actSkew:
        fixSkew(sys.argv[-1], "temp_skew.png")
        tempFile = "temp_skew.png"

    if actBord:
        fixBorder(tempFile, segFile, "temp.png")
        tempFile = "temp.png"

    if actMerge:
        pythonSegmentation.runSegmentation(tempFile, "temp_seg.txt", 2)
        fixLineMerge("temp_seg.txt", "final_seg.txt")
        cv2.imwrite("final.png", cv2.imread(tempFile))
        exit()

    pythonSegmentation.runSegmentation(tempFile, "final_seg.txt", 2)
    cv2.imwrite("final.png", cv2.imread(tempFile))



    





