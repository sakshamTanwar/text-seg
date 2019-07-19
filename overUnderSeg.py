import os
import sys
from shapely.geometry import box
import cv2

def getO(fig1, fig2):
    return fig1.intersection(fig2).area/fig1.union(fig2).area

def removeExt(fl):
    ind = fl.find(".")
    return fl[0:ind]

def isInside(boxI, boxO):
    boxI = list(boxI.bounds)
    boxO = list(boxO.bounds)
    return boxI[0] >= boxO[0] and boxI[1] >= boxO[1] and boxI[2] <= boxO[2] and boxI[3] <= boxO[3]

def getBoxes(fl_path):
    fl = open(fl_path, "r")
    boxes = []
    for line in fl:
        line = [int(x) for x in line.rstrip().split("\t")]
        boxes.append(box(line[0], line[1], line[0] + line[2], line[1] + line[3]))
    return boxes

def getNumOfPixels(img_path):
    img = cv2.imread(img_path)
    return img.shape[0]*img.shape[1]

def getMaxO(gt_box, s_boxes):
    maxO = 0
    for s_box in s_boxes:
        curO = getO(gt_box, s_box)
        if curO > maxO:
            maxO = curO

    return maxO

def getMaxOLamb(gt_box, s_boxes, lamb):
    maxO = 0
    for s_box in s_boxes:
        un_box = gt_box.union(s_box)
        if un_box.area > (1 + lamb) * gt_box.area:
            continue
        curO = getO(gt_box, s_box)
        if curO > maxO:
            maxO = curO
    return maxO

def getSC(gt_boxes, s_boxes, N):
    result = 0
    for gt_box in gt_boxes:
        result += gt_box.area * getMaxO(gt_box, s_boxes)
    result /= N
    return result

def getSCOv(gt_boxes, s_boxes, N, lamb):
    result = 0
    for gt_box in gt_boxes:
        result += gt_box.area * getMaxOLamb(gt_box, s_boxes, lamb)
    result /= N
    return result

def getSCUn(SC, SCOv):
    return SC - SCOv

def getSCOvRel(SC, SCOv):
    return SCOv/SC

def getSCUnRel(SC, SCUn):
    return SCUn/SC

def getSCRels(img_path, gt_fl, seg_fl, lamb):
    N = getNumOfPixels(img_path)
    gt_boxes = getBoxes(gt_fl)
    s_boxes = getBoxes(seg_fl)
    SC = getSC(gt_boxes, s_boxes, N)
    SCOv = getSCOv(gt_boxes, s_boxes, N, lamb)
    SCUn = getSCUn(SC, SCOv)
    return [getSCOvRel(SC, SCOv), getSCUnRel(SC, SCUn)]

def isVerticallySegmented(boxes):
    box_int = []
    for box in boxes:
        box_int.append(list(box.bounds))

    box_int.sort(key = lambda x: x[1])

    for i in range(1, len(box_int)):
        if box_int[i-1][3] < box_int[i][3]:
            return True

    return False

def countBoxes(box_st_1, box_st_2):
    cnt = 0
    for gt_box in box_st_1:
        numInside = 0
        insideBoxes = []
        to_print = False
        bounds_arr = list(gt_box.bounds)
        for s_box in box_st_2:
            if isInside(s_box, gt_box):
                numInside += 1
                insideBoxes.append(s_box)

        if numInside > 1 and isVerticallySegmented(insideBoxes):
            cnt += 1

    return cnt/len(box_st_1)

def buildDictForFile():
    log_fl = "./images/Manual/testing.txt"
    log_fl = open(log_fl, "r")
    filesToTest = {}
    for line in log_fl:
        line = line.rstrip()
        filesToTest[line] = True

    return filesToTest

def runForAllNew(directory, lang):
    avg_orig_tes = 0
    avg_new_tes = 0
    avg_orig_cpp = 0
    avg_new_cpp = 0
    avg_orig_tes_u = 0
    avg_new_tes_u = 0
    avg_orig_cpp_u = 0
    avg_new_cpp_u = 0
    fileForBad = "./images/Manual/badFiles.txt"
    fileForBad = open(fileForBad, "w+")

    cnt = 0
    for root, subfolder, files in os.walk(directory):
        for f in files:
            if f.endswith('.jpg') and root.find(lang) != -1:
                cnt += 1
                img_path = os.path.join(root, f)
                #if img_path not in filesToTest:
                #    continue
                gt_fl = os.path.join(root, "..", "Segmentations", f + ".lines.txt")
                seg_fl = os.path.join(root, "..", "tesserocrSegmentation", removeExt(f), f + "lines.txt") 
                seg_fixed = os.path.join(root, "..", "LineMerge", removeExt(f), "tesLines.txt")
                cpp_fl = os.path.join(root, "..", "cppSegmentation", removeExt(f), f + ".lines.txt")
                cpp_fixed = os.path.join(root, "..", "LineMerge", removeExt(f), "cppLines.txt")


                gt_boxes = getBoxes(gt_fl)
                tes_boxes = getBoxes(seg_fl)
                tes_f_boxes = getBoxes(seg_fixed)
                cpp_boxes = getBoxes(cpp_fl)
                cpp_f_boxes = getBoxes(cpp_fixed)

                avg_orig_cpp += countBoxes(gt_boxes, cpp_boxes)
                avg_new_cpp += countBoxes(gt_boxes, cpp_f_boxes)
                avg_orig_tes += countBoxes(gt_boxes, tes_boxes)
                avg_new_tes += countBoxes(gt_boxes, tes_f_boxes)

                if (countBoxes(gt_boxes, cpp_boxes) > 0 and countBoxes(gt_boxes, cpp_f_boxes) != 0) or (countBoxes(gt_boxes, tes_boxes) > 0 and countBoxes(gt_boxes, tes_f_boxes) != 0):
                    fileForBad.write("{A}\n".format(A = img_path))

                
                print(img_path)

                #avg_orig_cpp_u += countBoxes(cpp_boxes, gt_boxes)
                #avg_new_cpp_u += countBoxes(cpp_f_boxes, gt_boxes)
                #avg_orig_tes_u += countBoxes(tes_boxes, gt_boxes)
                #avg_new_tes_u += countBoxes(tes_f_boxes, gt_boxes)


    print("Over Segmentation")
    print("Cpp:-")
    print(avg_orig_cpp/cnt, avg_new_cpp/cnt)
    print("Tes:-")
    print(avg_orig_tes/cnt, avg_new_tes/cnt)
    print("Under Segmentation")
    print("Cpp:-")
    print(avg_orig_cpp_u/cnt, avg_new_cpp_u/cnt)
    print("Tes:-")
    print(avg_orig_tes_u/cnt, avg_new_tes_u/cnt)



def runForAll(directory, lamb, log_fl):
    log = open(log_fl, "w+")
    for root, subfolder, files in os.walk(directory):
        for f in files:
            if f.endswith('.jpg'):
                img_path = os.path.join(root, f)
                print(img_path)
                gt_fl = os.path.join(root, "..", "Segmentations", f + ".lines.txt")
                seg_fl = os.path.join(root, "..", "tesserocrSegmentation", removeExt(f), f + "lines.txt") 
                SCRels = getSCRels(img_path, gt_fl, seg_fl, lamb)
                log.write("{a}\t{b}\t{c}\n".format(a = img_path, b = SCRels[0], c = SCRels[1]))

    log.close()


if __name__ == '__main__':
    directory = "./images"
    lang = sys.argv[1]
    runForAllNew(directory, lang)

