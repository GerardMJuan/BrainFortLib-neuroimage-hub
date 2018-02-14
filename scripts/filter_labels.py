import argparse
import os
import SimpleITK as sitk
import numpy as np
from fnmatch import fnmatch

parser = argparse.ArgumentParser()
parser.add_argument("--in_dir", type=str, nargs=1, required=True, help='input directory')
parser.add_argument("--in_suffix", type=str, nargs=1, required=True, help='suffix of input label files')
parser.add_argument("--out_dir", type=str, nargs=1, required=True, help='output directory')
parser.add_argument("--out_suffix", type=str, nargs=1, required=True, help='suffix of output filtered files')
parser.add_argument("--include", type=int, nargs='+', action="append", help="label id or list ids (if list, group using 1st id)")

args = parser.parse_args()


files_list = os.listdir(args.in_dir[0])
in_files_list = [f for f in files_list if fnmatch(f, '*' + args.in_suffix[0])]
assert in_files_list, "List of input labels is empty"

out_files_list = [f.split(args.in_suffix[0])[0] + args.out_suffix[0] for f in in_files_list]


for in_file, out_file in zip(in_files_list, out_files_list):

    print "Processing {}".format(in_file)

    in_sitk = sitk.ReadImage(os.path.join(args.in_dir[0], in_file))

    in0 = sitk.GetArrayFromImage(in_sitk)

    out0 = np.zeros(in0.shape, dtype=in0.dtype)

    for labels in args.include:
        for label in labels:
            out0[np.where(in0 == label)] = labels[0]

    out_sitk = sitk.GetImageFromArray(out0)
    out_sitk.CopyInformation(in_sitk)
    sitk.WriteImage(out_sitk, os.path.join(args.out_dir[0], out_file))


