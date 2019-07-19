import os
import sys


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

def ht(line):
    return line[3]

def dist(line1, line2):
    if line1[1] > line2[1]:
        line1, line2 = line2, line1

    low_ln1 = line1[1] + line1[3]
    if low_ln1 <= line2[1] + line2[3] and low_ln1 >= line2[1]:
        return 0

    return abs(low_ln1 - line2[1])


def mergeLines(lines):
    avg_ht = getAvgHeight(lines)
    print(avg_ht)
    threshold = 0.6
    threshold_dist = 0.09
    newLines = []
    lines.sort(key = lambda v: v[1])
    for i in range(len(lines)):
        if ht(lines[i]) > threshold*avg_ht:
            newLines.append(lines[i])
        else:
            prev = -1
            nxt = -1
            if i-1 >= 0:
                prev = lines[i-1]
            else:
                newLines.append(lines[i])
                continue
            if nxt == -1:
                if dist(prev, lines[i]) < threshold_dist*avg_ht:
                    newLines[-1][3] = lines[i][1] + lines[i][3] - newLines[-1][1]
                else:
                    newLines.append(lines[i])
                continue

            if dist(prev, lines[i]) < dist(lines[i], nxt) and dist(prev, lines[i]) < threshold_dist*avg_ht:
                newLines[-1][3] = lines[i][1] + lines[i][3] - newLines[-1][1]
                continue
            elif dist(nxt, lines[i]) < dist(lines[i], prev) and dist(nxt, lines[i]) < threshold_dist*avg_ht:
                lines[i+1][3] = lines[i+1][1] + lines[i+1][3] - lines[i][1]
                lines[i+1][1] = lines[i][1]
                continue

            newLines.append(lines[i])

    isChanged = (len(newLines) != len(lines))
    return newLines, isChanged

if __name__ == '__main__':
    lines = getLines(sys.argv[1])
    log_fl = "./images/linChanged.txt"
    log_fl = open(log_fl, "a+")
    newLines, changed = mergeLines(lines)
    if changed:
        log_fl.write("{a}\n".format(a = sys.argv[1]))
    new_fl = sys.argv[2]
    new_fl = open(new_fl, "w+")
    for line in newLines:
        new_fl.write("{a}\t{b}\t{c}\t{d}\n".format(a = line[0], b = line[1], c = line[2], d = line[3]))

    print(len(newLines), len(lines))
