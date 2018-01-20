import json
import math
import random
import os
import sys

from PIL import Image

class Point(object):
    def __init__(self, x, y):
        self._x = x
        self._y = y

    def ToString(self):
        return json.dumps({"x": self._x, "y": self._y})

    @staticmethod
    def FromString(json_str):
        d = json.loads(json_str)
        return Point(x=d["x"], y=d["y"])

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def Distance(self, other_point):
        return math.sqrt(self.DistanceSquared(other_point))

    def DistanceSquared(self, other_point):
        del_x = self._x - other_point.x
        del_y = self._y - other_point.y
        return del_x * del_x + del_y * del_y

    def __hash__(self):
        return hash((self._x, self._y))

    def __eq__(self, other):
        return self._x == other.x and self._y == other.y


class Ellipse(object):

    def __init__(self, focus1, focus2, distance, colors=(None, None, None)):
        self._f1 = focus1
        self._f2 = focus2
        self._d = distance
        self._r = colors[0]
        self._g = colors[1]
        self._b = colors[2]
        self._active = None

    def ToString(self):
        return json.dumps({
            "f1": self._f1.ToString(),
            "f2": self._f2.ToString(),
            "d": self._d,
            "r": float("nan") if (self._r is None) else self._r,
            "g": float("nan") if (self._g is None) else self._g,
            "b": float("nan") if (self._b is None) else self._b})

    @staticmethod
    def FromString(json_str):
        d = json.loads(json_str)
        r = d["r"] if not math.isnan(d["r"]) else None
        g = d["g"] if not math.isnan(d["g"]) else None
        b = d["b"] if not math.isnan(d["b"]) else None
        return Ellipse(focus1=Point.FromString(d["f1"]),
                       focus2=Point.FromString(d["f2"]), distance=d["d"],
                       colors=(r, g, b))

    def Contains(self, point):
        if abs(self._f1.x - point.x) > self._d:
            return False
        if abs(self._f1.y - point.y) > self._d:
            return False
        if abs(self._f2.x - point.x) > self._d:
            return False
        if abs(self._f2.y - point.y) > self._d:
            return False
        d1 = self._f1.Distance(point)
        if d1 > self._d:
            return False
        d2 = self._f2.Distance(point)
        if d2 > self._d:
            return False
        return (d1 + d2) <= self._d

    def SetActive(self, height, width):
        valid = set()
        invalid = set()
        not_checked = set()
        not_checked.add(self._f1)
        not_checked.add(self._f2)
        while not_checked:
            p = not_checked.pop()
            if p.x < 0 or p.x > height or p.y < 0 or p.y > width:
                invalid.add(p)
                continue
            if self.Contains(p):
                valid.add(p)
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        new_p = Point(p.x + dx, p.y + dy)
                        if (new_p.x < 0 or new_p.x > height or
                            new_p.y < 0 or new_p.y > width):
                            invalid.add(new_p)
                            continue
                        if new_p in valid:
                            continue
                        if new_p in invalid:
                            continue
                        if new_p in not_checked:
                            continue
                        not_checked.add(new_p)
            else:
                invalid.add(p)
        self._active = valid

    def SetRGB(self, orig_pixels, approx_pixels):
        if self._active is None:
            h = max([r for r, _ in approx_pixels])
            w = max([c for _, c in approx_pixels])
            self.SetActive(h, w)
        r, g, b = 0.0, 0.0, 0.0
        orig_resid = 0
        for p in self._active:
            row, col = p.x, p.y
            del_r = orig_pixels[row, col][0] - approx_pixels[row, col][0]
            del_g = orig_pixels[row, col][1] - approx_pixels[row, col][1]
            del_b = orig_pixels[row, col][2] - approx_pixels[row, col][2]
            r += float(del_r)/len(self._active)
            g += float(del_g)/len(self._active)
            b += float(del_b)/len(self._active)
            orig_resid += abs(del_r) + abs(del_g) + abs(del_b)
        new_resid = 0
        for p in self._active:
            row, col = p.x, p.y
            del_r = orig_pixels[row, col][0] - approx_pixels[row, col][0] - r
            del_g = orig_pixels[row, col][1] - approx_pixels[row, col][1] - g
            del_b = orig_pixels[row, col][2] - approx_pixels[row, col][2] - b
            new_resid += abs(del_r) + abs(del_g) + abs(del_b)
        self._r = r
        self._g = g
        self._b = b
        # bigger values means more improvement
        return orig_resid - new_resid

    def GetColor(self):
        if self._r is None or self._g is None or self._b is None:
            raise ValueError("Color not yet set")
        return (self._r, self._g, self._b)

    def GetActives(self):
        if self._active is None:
            raise ValueError("Color not yet set")
        return self._active

    def Foci(self):
        return (self._f1, self._f2)

    def Distance(self):
        return self._d

    def MaybeOverlaps(self, other):
        o1, o2 = other.Foci()
        combo_d = self._d + other.Distance()
        return (self._f1.Distance(o1) < combo_d or
                self._f2.Distance(o1) < combo_d or
                self._f1.Distance(o2) < combo_d or
                self._f2.Distance(o2) < combo_d)


def BuildEllipse(focus1, diameter, angle, overlap):
    focus2 = Point(int(focus1.x + overlap * diameter * math.cos(angle)),
                   int(focus1.y + overlap * diameter * math.sin(angle)))
    return Ellipse(focus1, focus2, diameter)


def ClipColor(x):
    if x > 255:
        return 255
    if x < 0:
        return 0
    return int(x)


def ClipColors(rgb_tuple):
    return tuple([ClipColor(x) for x in rgb_tuple])


class Ellipsabelle(object):

    def __init__(self, filename, ellipses=None):
        if not ellipses:
            self._ellipses = []
        else:
            self._ellipses = ellipses
        self._orig_img = Image.open(filename)
        self._orig_pixels = Image.open(filename).load()
        r, g, b = 0.0, 0.0, 0.0
        num_pixels = self._orig_img.size[0] * self._orig_img.size[1]
        for row in range(self._orig_img.size[0]):
            for col in range(self._orig_img.size[1]):
                r += float(self._orig_pixels[row, col][0])/num_pixels
                g += float(self._orig_pixels[row, col][1])/num_pixels
                b += float(self._orig_pixels[row, col][2])/num_pixels
        self._approx_pixels = {}
        self._bg_color = (r, g, b)
        for row in range(self._orig_img.size[0]):
            for col in range(self._orig_img.size[1]):
                self._approx_pixels[row, col] = [r, g, b]
        for e in self._ellipses:
            self.IncrementByEllipse(e)

    def NumEllipses(self):
        return len(self._ellipses)

    def ImageSize(self):
        return self._orig_img.size

    def IncrementByEllipse(self, ellipse):
        r, g, b = ellipse.GetColor()
        for p in ellipse.GetActives():
            self._approx_pixels[p.x, p.y][0] += r
            self._approx_pixels[p.x, p.y][1] += g
            self._approx_pixels[p.x, p.y][2] += b
        self._ellipses.append(ellipse)

    def Iterate(self, max_dist, min_dist, num_candidates=20):
        candidates = []
        h, w = self.ImageSize()
        for _ in range(num_candidates):
            f1 = Point(random.randint(0, h), random.randint(0, w))
            e = BuildEllipse(
                    f1, random.random() * (max_dist - min_dist) + min_dist,
                    2 * math.pi * random.random(), random.random())
            resid = e.SetRGB(self._orig_pixels, self._approx_pixels)
            candidates.append((resid, e))
        keepers = []
        candidates.sort(key=lambda pair: pair[0], reverse=True)
        for _, ellipse in candidates:
            if any([ellipse.MaybeOverlaps(k) for k in keepers]):
                continue
            keepers.append(ellipse)
        for k in keepers:
            self.IncrementByEllipse(k)
        return True, keepers[0].Distance()

    def SaveEllipses(self, filename):
        with open(filename, 'w') as outfile:
            first_line = json.dumps({
                            "h": self._orig_img.size[0],
                            "w": self._orig_img.size[1],
                            "bg_r": self._bg_color[0],
                            "bg_g": self._bg_color[1],
                            "bg_b": self._bg_color[2]}) + "\n"
            outfile.write(first_line)
            for ell in self._ellipses:
                outfile.write(ell.ToString() + '\n')

    def SaveApproximate(self, filename):
        img = Image.new('RGB', self._orig_img.size, "black")
        pixels = img.load()
        for row in range(img.size[0]):
            for col in range(img.size[1]):
                pixels[row, col] = ClipColors(self._approx_pixels[row, col])
        img.save(filename, 'png')
