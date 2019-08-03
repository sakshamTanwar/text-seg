import cv2
import math
import sys
import os
import numpy as np
import random

def removeExt(fl):
    ind = fl.find(".")
    return fl[0:ind]

def getLines(fl):
    fl = open(fl, "r")
    lines = []
    for l in fl:
        line = [int(x) for x in l.split("\t")]
        lines.append(line)
    return lines

def getAvgHeight(lines):
    avg_height = 0
    for line in lines:
        avg_height += line[3]

    if len(lines) == 0:
        return 0
    return avg_height/len(lines)

def detectLines(img_fl, ln_fl):
    img = cv2.imread(img_fl)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    edges = cv2.Canny(gray, 0.5, 1)
    avgHt = getAvgHeight(getLines(ln_fl))
    multiplier = 10.0

    lines = cv2.HoughLinesP(gray, rho = 1, theta = np.pi/180, threshold = 50, minLineLength = multiplier*avgHt, maxLineGap = 10)
    lns = []
    if lines is None:
        return lns
    for line in lines:
        for x1, y1, x2, y2 in line:
            ln = [x1, y1, x2, y2]
            lns.append(ln)


    return lns

def getAngle(line):
    x1, y1, x2, y2 = line
    opp = abs(x1 - x2)
    base = abs(y1 - y2)
    return 180*math.asin(opp/math.sqrt(base*base + opp*opp))/np.pi

def removeLines(img_fl, lines, save_path):
    img = cv2.imread(img_fl)
    y, x, _ = img.shape
    cut = 0.3
    leftX = 0
    rightX = x
    for line in lines:
        x1, y1, x2, y2 = line
        if min(x1, x2) < x*cut:
            leftX = max(leftX, min(x1, x2))
        elif min(x1, x2) > (1 - cut)*x:
            rightX = min(rightX, max(x1, x2))
    crop_img = img[:, leftX:rightX]
    cv2.imwrite(save_path, crop_img)
    return leftX, rightX

def removeAndSave(img_fl, ln_fl, save_path):
    lines = detectLines(img_fl, ln_fl)
    if len(lines) == 0:
        print("No lines for border found")
        removeLines(img_fl, [], save_path)
        return
    remLines = []
    for line in lines:
        angle = getAngle(line)
        if angle < 5:
            remLines.append(line)
    removeLines(img_fl, remLines, save_path)

def runForAll(lang):
    for root, subfolder, files in os.walk("./images"):
        for f in files:
            if f.endswith('.jpg') and root.find(lang) != -1:
                print(os.path.join(root, f))
                directory = os.path.join(root, "..", "borderRemoved")
                if not os.path.exists(directory):
                    os.makedirs(directory)

                line_fl = os.path.join(root, "..", "tesserocrSegmentation", removeExt(f), f + "lines.txt")
                save_path = os.path.join(directory, f + "border.png")
                removeAndSave(os.path.join(root, f), line_fl, save_path)




if __name__ == "__main__":
    lang = sys.argv[1]
    runForAll(lang)
