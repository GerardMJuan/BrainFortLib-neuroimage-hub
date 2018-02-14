import SimpleITK as sitk
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--in_img", type=str, nargs=1, required=True)
parser.add_argument("--ref_img",type=str, nargs=1, required=True)
parser.add_argument("--out_img",type=str, nargs=1, required=True)
parser.add_argument("--nearest", action="store_true", help="nearest neighbor interpolation")


args = parser.parse_args()

in_sitk = sitk.ReadImage(args.in_img[0])
ref_sitk = sitk.ReadImage(args.ref_img[0])

sz_in, sp_in, or_in, dir_in = in_sitk.GetSize(), in_sitk.GetSpacing(), in_sitk.GetOrigin(), in_sitk.GetDirection()
sz_ref, sp_ref, or_ref, dir_ref = ref_sitk.GetSize(), ref_sitk.GetSpacing(), ref_sitk.GetOrigin(), ref_sitk.GetDirection()

scale = [sp_ref[i] / sp_in[i] for i in range(len(sp_in))]

sz_out, sp_out = [int(sz_in[i]/scale[i]) for i in range(len(sz_in))], [sp_in[i] * scale[i] for i in range(len(sp_in))]

print "Orig Size ", sz_in, "\nNew Size ", sz_out
print "Orig Sp ", sp_in, "\nNew Sp ", sp_out

t = sitk.Transform(3, sitk.sitkScale)
# t.SetParameters((scale[0], scale[1], scale[2]))

interpolation = sitk.sitkLinear
if args.nearest:
    interpolation = sitk.sitkNearestNeighbor

out_sitk = sitk.Resample(in_sitk, sz_out, t, interpolation, or_in, sp_out, dir_in, 0.0, sitk.sitkFloat32)

sitk.WriteImage(out_sitk, args.out_img[0])