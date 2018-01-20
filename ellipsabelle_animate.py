import ellipsabelle
import json
import sys

from PIL import Image


# Follow up with:
# convert iz1_ellipse.gif -layers OptimizePlus unposted/iz1.gif

if __name__ == "__main__":
    outfile_base = sys.argv[2]  # will have .gif appended
    with open(sys.argv[1], "r") as infile:
        lines = infile.readlines()
    bg_stats = json.loads(lines[0])
    print bg_stats
    height = int(bg_stats['h'])
    width = int(bg_stats['w'])
    bg_r, bg_g, bg_b = bg_stats['bg_r'], bg_stats['bg_g'], bg_stats['bg_b']
    pix = {}
    for hi in range(height):
        for wi in range(width):
            pix[hi, wi] = [bg_r, bg_g, bg_g]


    img_base = Image.new('RGB', (height, width), "black")
    img_pixels = img_base.load()
    for r, c in pix:
        img_pixels[r, c] = ellipsabelle.ClipColors((bg_r, bg_g, bg_b))

    target = 1
    num_saved = 0
    im_seq = []
    for num_ell, ell_str in enumerate(lines[1:]):
        ell = ellipsabelle.Ellipse.FromString(ell_str.strip())
        ell.SetActive(height, width)
        dr, dg, db = ell.GetColor()
        for p in ell.GetActives():
            r, c = p.x, p.y
            try:
                pix[r,c][0] += dr
                pix[r,c][1] += dg
                pix[r,c][2] += db
            except:
                pass
        if num_ell == target:
            print target
            img = Image.new('RGB', (height, width), "black")
            img_pixels = img.load()
            for r, c in pix:
                img_pixels[r, c] = ellipsabelle.ClipColors(pix[r, c])
            im_seq.append(img)
            target += len(im_seq)
    img_base.save(outfile_base+".gif", save_all=True, append_images=im_seq,
                  optimize=True)
