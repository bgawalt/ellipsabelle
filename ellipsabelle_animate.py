import ellipsabelle
import json
import os
import sys

from PIL import Image


def GetFilenames(source_dir):
    return [f for f in os.listdir(source_dir)
            if f[0] != "." and f[-4:] == ".txt"]


def SaveAnimation(ellipse_filename, gif_filename):
    with open(ellipse_filename, "r") as infile:
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
            img = Image.new('RGB', (height, width), "black")
            img_pixels = img.load()
            for r, c in pix:
                img_pixels[r, c] = ellipsabelle.ClipColors(pix[r, c])
            im_seq.append(img)
            target += len(im_seq)
    img = Image.new('RGB', (height, width), "black")
    img_pixels = img.load()
    for r, c in pix:
        img_pixels[r, c] = ellipsabelle.ClipColors(pix[r, c])
    im_seq.append(img)
    target += len(im_seq)
    img_base.save(gif_filename, save_all=True, append_images=im_seq,
                  optimize=True)

# Follow up with:
# convert iz1_ellipse.gif -layers OptimizePlus unposted/iz1.gif

if __name__ == "__main__":
    ellipse_dir = sys.argv[1]
    gif_dir = sys.argv[2]

    for f in GetFilenames(ellipse_dir):
        print f
        SaveAnimation(os.path.join(ellipse_dir, f),
                      os.path.join(gif_dir, f)[:-4] + ".gif")
