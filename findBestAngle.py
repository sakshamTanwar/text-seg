import time
import pprint
from shapely.geometry import box
from shapely.affinity import rotate
import cv2
from PIL import Image
import os
from subprocess import Popen, PIPE, DEVNULL
import sys
import locale
locale.setlocale(locale.LC_ALL, 'C')
from tesserocr import PyTessBaseAPI, RIL
import numpy as np
import random
from scipy.ndimage import interpolation as inter
import matplotlib.pyplot as plt



n = 10

def readImage(fl):
    img = Image.open(fl)
    return img

def rotateImage(img, angle):
    rows, cols, _ = img.shape
    m = cv2.getRotationMatrix2D((cols/2, rows/2), angle, 1)
    return cv2.warpAffine(img, m, (cols, rows), cv2.INTER_LINEAR, cv2.BORDER_CONSTANT, borderValue=(255,255,255))

def getLineBoxes(img):
    with PyTessBaseAPI() as api:
        api.SetImage(img)
        boxes = []

        blocks = api.GetComponentImages(RIL.TEXTLINE, True)

        for i, (im, box, _, _) in enumerate(blocks):
            boxes.append([box['x'], box['y'], box['w'], box['h']])

        return boxes

def getEval(image, boxes):
    tot_box = 0
    occupied = 0
    for box in boxes:
        for i in range(box[0], box[0] + box[2]):
            for j in range(box[1], box[1] + box[3]):
                tot_box += 1
                if image[j-1, i-1, 0] == 0:
                    occupied += 1

    if tot_box == 0:
        return 0

    return occupied/tot_box

def getScore(imgCv, angle, lang):
    rotImg = rotateImage(imgCv, angle)
    cv2.imwrite("./tmpImage" + lang + ".png", rotImg)
    boxes = getLineBoxes(readImage("./tmpImage" + lang + ".png"))
    return getEval(rotImg, boxes)



def findBestAngle(image_file):
    imgCv = cv2.imread(image_file)
    angle_min = -1
    angle_max = 1
    mem = {}
    for i in range(3):
        random_nums = []
        scores = {}
        for j in range(n):
            random_nums.append(random.uniform(angle_min, angle_max))
            scores[random_nums[-1]] = getScore(imgCv, random_nums[-1])
            mem[random_nums[-1]] = scores[random_nums[-1]]
            print(random_nums[-1], " : ", scores[random_nums[-1]])
        
        mx1 = -1
        mx2 = -1
        for k in scores:
            if mx1 == -1:
                mx1 = k
                continue
            
            if mx2 == -1:
                mx2 = k
                if mx2 > mx1:
                    mx1, mx2 = mx2, mx1
                continue
            if scores[k] > scores[mx1]:
                mx2 = mx1
                mx1 = k
                continue
            if scores[k] < scores[mx1] and scores[k] > scores[mx2]:
                mx2 = k

        angle_min = min(mx1, mx2)
        angle_max = max(mx1, mx2)
        print("")
        print(angle_min, angle_max, "\n")

    mx = -1
    for k in mem:
       if mx == -1:
           mx = k
           continue

       if mem[mx] < mem[k]:
           mx = k

    return mx

def findBestAngleBin(image_file, lang):
    imgCv = cv2.imread(image_file)
    low = -1
    high = 1
    mem = {}
    i = 0
    while high >= low and i < 5:
        i += 1
        #print(low, high)
        mid = (high+low)/2
        if mid not in mem:
            mem[mid] = getScore(imgCv, mid, lang)
        if high not in mem:
            mem[high] = getScore(imgCv, high, lang)
        if low not in mem:
            mem[low] = getScore(imgCv, low, lang)

        if mem[mid] > mem[low] and mem[mid] > mem[high]:
            if mem[low] > mem[high]:
                high = mid
            else:
                low = mid
        elif mem[low] > mem[mid] and mem[low] > mem[high]:
            high = mid
        else:
            low = mid

    mx = -1

    for k in mem:
        if mx == -1:
            mx = k
            continue

        if mem[k] > mem[mx]:
            mx = k

    #print(mem)
    return mx

def findAnglesForAll(lang):
    log_file = "./images/anglesBin" + lang + ".txt"
    log_fl = open(log_file, "w+")
    cnt = 0
    for root, subfolder, files in os.walk("./images"):

        for f in files:
            if f.endswith('.jpg') and root.find(lang) != -1:

                print(os.path.join(root, f))
                best_angle = findBestAngleBin(os.path.join(root, f), lang)
                log_fl.write("{fl} {ang}\n".format(fl = f, ang = best_angle))
                
                cnt += 1
                print(cnt)


def buildDict(lang):
    log_file = "./images/angles.txt"
    log_fl = open(log_file, "r")
    angles = {}
    for line in log_fl:
        line = line.rstrip().split("\t")
        if line[0] in angles:
            print("Not unique")
        else:
            angles[line[0]] = float(line[1])
    return angles
def removeExt(fl):
    ind = fl.find(".")
    return fl[0:ind]


def rotateImages(lang):
    angles = buildDict(lang)
    cnt = 0
    for root, subfolder, files in os.walk("./images"):
        for f in files:
            if f.endswith('.jpg') and root.find(lang) != -1:
                cnt += 1
                print(os.path.join(root, f))
                print(cnt)
                directory = os.path.join(root, "..", "skewFixedMinArea", removeExt(f))
                if not os.path.exists(directory):
                    os.makedirs(directory)
                rotImg = rotateImage(cv2.imread(os.path.join(root, f)), angles[f])
                cv2.imwrite(os.path.join(directory, removeExt(f) + "rot.png"), rotImg)

                cppSegDir = os.path.join(directory, "cppSeg")
                if not os.path.exists(cppSegDir):
                    os.makedirs(cppSegDir)

                command = ["./j-layout", os.path.join(directory, removeExt(f) + "rot.png")]
                Popen(command, stdout = DEVNULL, stderr = DEVNULL).wait()

                os.rename(os.path.join(directory, removeExt(f) + "rot.png.blocks.txt"), os.path.join(directory, "cppSeg", removeExt(f) + "rot.png.blocks.txt"))
                os.rename(os.path.join(directory, removeExt(f) + "rot.png.lines.txt"), os.path.join(directory, "cppSeg", removeExt(f) + "rot.png.lines.txt"))
                os.rename(os.path.join(directory, removeExt(f) + "rot.png.words.txt"), os.path.join(directory, "cppSeg", removeExt(f) + "rot.png.words.txt"))
                tesSegDir = os.path.join(directory, "tesSeg")

                if not os.path.exists(tesSegDir):
                    os.makedirs(tesSegDir)

                #command = ["python", "pythonOutput.py", os.path.join(directory, removeExt(f) + "rot.png"), os.path.join(tesSegDir, f + ".blocks.txt"), "1"] 
                #Popen(command).wait()
                command = ["python", "pythonOutput.py", os.path.join(directory, removeExt(f) + "rot.png"), os.path.join(tesSegDir, f + ".lines.txt"), "2"] 
                Popen(command).wait()
                #command = ["python", "pythonOutput.py", os.path.join(directory, removeExt(f) + "rot.png"), os.path.join(tesSegDir, f + ".words.txt"), "3"] 
                #Popen(command).wait()

                

def evaluate():
    log_fl = './images/Iou.txt'
    log_fl = open(log_fl, 'w+')
    log_fl.write("File - Cpp IOU - Cpp Rot IOU - Tes IOU - Tes Rot IOU\n")
    avg_cpp = 0
    avg_cpp_rot = 0
    avg_tes = 0
    avg_tes_rot = 0
    less_cnt = 0
    cnt = 0
    angles = buildDict()
    for root, subfolder, files in os.walk("./images"):
        for f in files:
            if f.endswith('jpg'):
                angle = angles[f]
                print(os.path.join(root, f))
                x,y,_ = cv2.imread(os.path.join(root, f)).shape
                gt_fl = os.path.join(root, "..", "Segmentations", f + ".lines.txt")
                cpp_fl = os.path.join(root, "..", "skewFixed", removeExt(f), "cppSeg", removeExt(f) + "rot.png.lines.txt")
                tes_fl = os.path.join(root, "..", "skewFixed", removeExt(f), "tesSeg", f + ".lines.txt")
                
                gt_boxes = getBoxes(gt_fl)
                cpp_boxes = getBoxes(cpp_fl)
                tes_boxes = getBoxes(tes_fl)

                gt_fig = getFig(gt_boxes)
                gt_fig_rot = rotate(gt_fig, -1*angle, origin=(y/2, x/2))
                cpp_fig = getFig(cpp_boxes)
                tes_fig = getFig(tes_boxes)

                avg_cpp += getIou(cpp_fig, gt_fig)
                avg_tes += getIou(tes_fig, gt_fig)
                avg_cpp_rot += getIou(cpp_fig, gt_fig_rot)
                avg_tes_rot += getIou(tes_fig, gt_fig_rot)
                
                if getIou(cpp_fig, gt_fig) > getIou(cpp_fig, gt_fig_rot) or  getIou(tes_fig, gt_fig) > getIou(tes_fig, gt_fig_rot):
                    cnt += 1
                    log_fl.write("{a} - {b} - {c} - {d} - {e}\n".format(a = f, b = getIou(cpp_fig, gt_fig), c = getIou(cpp_fig, gt_fig_rot), d = getIou(tes_fig, gt_fig), e = getIou(tes_fig, gt_fig_rot)))
                
                if getIou(cpp_fig, gt_fig) < 0.5:
                    less_cnt += 1

    avg_cpp /= 672
    print(cnt)
    print(avg_cpp, avg_cpp_rot/672)
    print(avg_tes/672, avg_tes_rot/671)


def getFig(boxes):
    fig = boxes[0]
    for i in range(1, len(boxes)):
        fig = fig.union(boxes[i])
    return fig

def getBoxes(fl_path):
    fl = open(fl_path, "r")
    boxes = []
    for line in fl:
        line = [int(x) for x in line.rstrip().split("\t")]
        boxes.append(box(line[0], line[1], line[0]+line[2], line[1]+line[3]))
    return boxes

def getIou(fig1, fig2):
    return fig1.intersection(fig2).area/fig1.union(fig2).area

def runScript():
    avg_cpp = 0
    avg_tes = 0
    avg_cpp_rot = 0
    avg_tes_rot = 0
    avg_cpp_orig = 0
    cnt = 0
    angles = buildDict()
    list_fl = "./images/lowRot.txt"
    list_fl = open(list_fl, "w+")
    diff_sc_fl = "./images/diff.txt"
    diff_sc_fl = open(diff_sc_fl, "w+")
    diff_sc_fl.write("File - New - Old\n")
    for root, subfolder, files in os.walk('./images'):
        for f in files:
            if f.endswith('.jpg'):
                print(os.path.join(root, f))
                angle = angles[f]
                x,y,_ = cv2.imread(os.path.join(root, f)).shape
                gt_fl = os.path.join(root, "..", "Segmentations", f + ".lines.txt")
                cpp_fl_orig = os.path.join(root, "..", "cppSegmentation", removeExt(f), f + ".lines.txt")
                cpp_fl = os.path.join(root, "..", "skewFixed", removeExt(f), "cppSeg", removeExt(f) + "rot.png.lines.txt")
                tes_fl = os.path.join(root, "..", "skewFixed", removeExt(f), "tesSeg", f + ".lines.txt")
                
                gt_boxes = getBoxes(gt_fl)
                cpp_orig_boxes = getBoxes(cpp_fl_orig)
                cpp_orig_fig = getFig(cpp_orig_boxes)
                cpp_boxes = getBoxes(cpp_fl)
                tes_boxes = getBoxes(tes_fl)

                gt_fig = getFig(gt_boxes)
                gt_fig_rot = rotate(gt_fig, angle, origin = (y/2, x/2))
                cpp_fig = getFig(cpp_boxes)
                tes_fig = getFig(tes_boxes)

                if getIou(cpp_fig, gt_fig) < getIou(cpp_orig_fig, gt_fig):
                    list_fl.write("{fl}\n".format(fl = f))

                avg_cpp += getIou(cpp_fig, gt_fig)
                avg_tes += getIou(tes_fig, gt_fig)
                avg_cpp_rot += getIou(cpp_fig, gt_fig_rot)
                avg_tes_rot += getIou(tes_fig, gt_fig_rot)
                avg_cpp_orig += getIou(cpp_orig_fig, gt_fig)

    print(cnt)
    print(avg_cpp_orig/6.72, avg_cpp_rot/6.72, avg_cpp/6.72)
    print(avg_tes_rot/6.72, avg_tes/6.72)


def removeSkewFold():
    for root, subfolder, files in os.walk("./images"):
        for f in files:
            if f.endswith('.jpg'):
                print(os.path.join(root, f))
                command = ["rm", "-rf", os.path.join(root, "..", "skewFixed")]
                Popen(command).wait()

def produceOuput(lang):
    cnt = 0
    for root, subfolder, files in os.walk("./images"):
        for f in files:
            if f.endswith('.jpg') and root.find(lang) != -1:
                print(os.path.join(root, f))
                cnt += 1
                print(cnt)

                directory = os.path.join(root, "..", "skewFixedMinArea", removeExt(f))
                if not os.path.exists(os.path.join(directory, "cppOut")):
                    os.makedirs(os.path.join(directory, "cppOut"))
                command = ["./show", os.path.join(root, "..", "skewFixedMinArea", removeExt(f), removeExt(f) + "rot.png"), os.path.join(directory, "cppSeg", removeExt(f) + "rot.png.lines.txt"), os.path.join(directory, "cppOut", removeExt(f) + "rot.png.lines.png")]
                Popen(command).wait()
                
                if not os.path.exists(os.path.join(directory, "tesOut")):
                    os.makedirs(os.path.join(directory, "tesOut"))
                command = ["./show", os.path.join(root, "..", "skewFixedMinArea", removeExt(f), removeExt(f) + "rot.png"), os.path.join(directory, "tesSeg", f + ".lines.txt"), os.path.join(directory, "tesOut", removeExt(f) + "rot.png.lines.png")]
                Popen(command).wait()

def mergeAngleFiles():
    out_fl = "./images/anglesBin.txt"
    out_fl = open(out_fl, "w+")
    
    langs = ["hindi", "telugu", "sanskrit"]

    for lang in langs:
        r_fl = "./images/anglesBin" + lang + ".txt"
        r_fl = open(r_fl, "r")
        for line in r_fl:
            line = line.rstrip().split()
            out_fl.write("{A}\t{B}\n".format(A = line[0], B = line[1]))

def findAngleMinArea(img_fl):
    image = cv2.imread(img_fl)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)

    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = - (90 + angle)
    else:
        angle + -angle

    return angle

def findAngleMinAreaAll(lang):
    cnt = 0
    angle_fl = "./images/angleMinArea" + lang + ".txt"
    angle_fl = open(angle_fl, "w+")
    for root, subfolder, files in os.walk('./images'):
        for f in files:
            if f.endswith('.jpg') and root.find(lang) != -1:
                cnt += 1
                print(cnt)
                angle = findAngleMinArea(os.path.join(root, f))
                angle_fl.write("{fl}\t{a}\n".format(fl = f, a = angle))

    angle_fl.close()

def find_score(arr, angle):
    data = inter.rotate(arr, angle, reshape=False, order=0)
    hist = np.sum(data, axis=1)
    score = np.sum((hist[1:] - hist[:-1]) ** 2)
    return hist, score

def findAngleHist(img_fl, lang):
    img = Image.open(img_fl)
    wd, ht = img.size
    pix = np.array(img.convert('1').getdata(), np.uint8)
    bin_img = 1 - (pix.reshape((ht, wd)) / 255.0)
    plt.imshow(bin_img, cmap='gray')
    plt.savefig('binary' + lang + '.png')

    scores = {}
    low = -1
    high = 1

    for _ in range(0, 2):
        mx1 = -1
        mx2 = -1
        for i in range(4):
            angle = random.uniform(low, high)
            hist, score = find_score(bin_img, angle)
            scores[angle] = score
            if mx1 == -1:
                mx1 = angle
                continue

            if mx2 == -1:
                if score > scores[mx1]:
                    mx2 = mx1
                    mx1 = angle
                else:
                    mx2 = angle
                continue

            if score > scores[mx1]:
                mx2 = mx1
                mx1 = angle
                continue

            if score > scores[mx2]:
                mx2 = angle

        low = min(mx1, mx2)
        high = max(mx1, mx2)

    mx = -1

    for k in scores:
        if mx == -1:
            mx = k
            continue

        if scores[k] > scores[mx]:
            mx = k

    return mx   


def findAngleHistAll(lang):
    #log_fl_path = "./images/anglesHist" + lang + ".txt"
    #log_fl = open(log_fl_path, "w+")
    #log_fl.close()
    cnt = 0
    for root, subfolder, files in os.walk("./images"):
        for f in files:
            if f.endswith('.jpg') and root.find(lang) != -1:
                cnt += 1
                angle = findAngleHist(os.path.join(root, f), lang)
                print(os.path.join(root, f), angle)
                #log_fl = open(log_fl_path, "a+")
                #log_fl.write("{fl}\t{a}\n".format(fl = f, a = angle))
                #log_fl.close()
        
                

if __name__ == "__main__":
    lang = sys.argv[1]
    produceOuput(lang)
