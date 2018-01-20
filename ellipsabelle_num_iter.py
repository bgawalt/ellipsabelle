import ellipsabelle
import sys

if __name__ == "__main__":
    # python ellipsabelle.py image_file.ext num_ellipse output_filename
    input_image_path = sys.argv[1]
    num_iter = int(sys.argv[2])
    output_filename = sys.argv[3]

    ell = ellipsabelle.Ellipsabelle(input_image_path)

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
    ell.SaveApproximate(output_filename[:-4]+".png")
