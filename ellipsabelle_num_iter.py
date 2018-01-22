"""Bulk process a directory of PNGs into ellipse files.

python ellipsabelle_num_iter.py [png directory] [num ellipses] [ellipse dir]
"""

import ellipsabelle
import os
import random
import sys


def GetFilenames(source_dir):
    all_filenames = os.listdir(source_dir)
    random.shuffle(all_filenames)
    return [f for f in all_filenames
            if f[0] != "." and f[-4:] == ".png"]


def CalculateEllipses(filename, num_iter, output_filename):
    ell = ellipsabelle.Ellipsabelle(filename)

    h, w = ell.ImageSize()
    max_dist = (h + w)/2
    min_dist = 0

    while ell.NumEllipses() < num_iter:
        _, new_max = ell.Iterate(max_dist=max_dist, min_dist=min_dist,
                                 num_candidates=20)
        max_dist = 1.5*new_max
        min_dist = 0.5*new_max
        print ell.NumEllipses(), num_iter, max_dist
    ell.SaveEllipses(output_filename)


if __name__ == "__main__":
    # python ellipsabelle.py image_file.ext num_ellipse output_filename
    src_dir = sys.argv[1]
    n = int(sys.argv[2])
    output_prefix = sys.argv[3]

    base_num = 6
    for id_, filename in enumerate(GetFilenames(src_dir)):
        img_file = os.path.join(src_dir, filename)
        out_file = "%s%d.txt" % (output_prefix, base_num + id_)
        CalculateEllipses(img_file, n, out_file)
        print img_file
