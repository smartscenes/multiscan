import struct
import sys
from plyfile import PlyData, PlyElement
import numpy as np


class OutputManager:
    def __init__(self):
        self.file = None
    
    def myprint(self, content):
        if self.file:
            print(content, file=self.file)
        else:
            print(content)

    def open(self, file):
        self.file = open(file, 'w')

    def close(self):
        if self.file:
            self.file.close()


output = OutputManager()


def read_ply(file_path, verbose=False):
    plydata = PlyData.read(file_path)
    # print summary information
    output.myprint("="*10 + "Summary" + "="*10)
    for i,element in enumerate(plydata.elements):
        output.myprint("Element {}:{}, length{}".format(i, element.name, element.count))
        output.myprint("properties: {}".format(element.properties))
        output.myprint("-"*20)

    if verbose:
        output.myprint("="*10 + "Data" + "="*10)
        for i,element in enumerate(plydata.elements):
            output.myprint("Element {}:{}, length{}".format(i, element.name, element.count))
            output.myprint("-"*20)
            for v in element.data:
                # print(v[0], v[1], v[2], v[3])
                output.myprint(v)
            output.myprint("-"*20)
    return plydata


def compare_ply(ply_a, ply_b):
    # check elements and its names
    output.myprint("="*10 + "Diff" + "="*10)
    if len(ply_a) != len(ply_b) or \
        not all([ply_a.elements[i].name == ply_b.elements[i].name for i in range(len(ply_a))]):
        output.myprint(
            "Elements doesn't match\n a:{}\n b:{}\n".format([element.name for element in ply_a.elements], 
                                                              [element.name for element in ply_b.elements]))
        return
    output.myprint("*"*20)
    # check properties
    for i in range(len(ply_a)):
        if ply_a.elements[i].properties != ply_b.elements[i].properties:
            output.myprint(
                "Element{} property deosn't match\n, a:{}\n, b:{}\n".format(
                    ply_a.elements[i].name, ply_a.elements[i].properties,ply_b.elements[i].properties))
            return
    output.myprint("*"*20)
    # check actual data:
    for i in range(len(ply_a)):
        if ply_a.elements[i].count != ply_b.elements[i].count:
            output.myprint(
                "Element{} data length deosn't match\n, a:{}\n, b:{}\n".format(
                    ply_a.elements[i].name, len(ply_a.elements[i].data), len(ply_b.elements[i].data)))
        # print(min(ply_a.elements[i].count, ply_b.elements[i].count))
        output.myprint("-"*10 + ply_a.elements[i].name + "-"*10)
        for j in range(min(ply_a.elements[i].count, ply_b.elements[i].count)):
            if not all([np.isclose((ply_a.elements[i].data[j][k]),  ply_b.elements[i].data[j][k]) for k in range(len(ply_a.elements[i].data[j]))]):
                    output.myprint(">"*20 + "\n" + "{}".format(ply_a.elements[i].data[j]) + "\n" + "<"*20 + "\n" + "{}".format(ply_b.elements[i].data[j]))
        output.myprint("-"*20)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Process imu byte data.')
    parser.add_argument('file_path', type=str, 
                    help='path to the imu file')
    parser.add_argument('-v', '--verbose', action='store_true', 
                    help='print file content line by line')
    parser.add_argument('-c', '--cmp', type=str, 
                    help='ply file to compare against')
    parser.add_argument('-r', '--report', type=str, 
                    help='redict report information')
    
    args = parser.parse_args()

    if args.report:
        output.open(args.report)
    ply = read_ply(args.file_path, verbose=args.verbose)

    if args.cmp:
        cmp_ply = read_ply(args.cmp, verbose=False)
        compare_ply(ply, cmp_ply)

    output.close()
