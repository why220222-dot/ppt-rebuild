#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Crop a photo card with per-corner rounded alpha (PowerPoint cannot round a picture).

usage:
  python rounded.py img.png --box 61,378,341,626 --radii 75,0,0,0 --out card1.png
  radii order: top-left, top-right, bottom-right, bottom-left (px)
"""
import argparse

import numpy as np
from PIL import Image


def rounded_mask(w, h, radii):
    tl, tr, br, bl = radii
    yy, xx = np.mgrid[0:h, 0:w]
    m = np.ones((h, w), bool)
    corners = [
        (0, 0, tl, xx < tl, yy < tl),
        (w - 1, 0, tr, xx >= w - tr, yy < tr),
        (w - 1, h - 1, br, xx >= w - br, yy >= h - br),
        (0, h - 1, bl, xx < bl, yy >= h - bl),
    ]
    for cx, cy, r, condx, condy in corners:
        if r <= 0:
            continue
        ccx = r - 0.5 if cx == 0 else w - r - 0.5
        ccy = r - 0.5 if cy == 0 else h - r - 0.5
        dist = np.sqrt((xx - ccx) ** 2 + (yy - ccy) ** 2)
        m &= ~((condx & condy) & (dist > r - 0.5))
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('png')
    ap.add_argument('--box', required=True, help='x0,y0,x1,y1 (exclusive x1/y1)')
    ap.add_argument('--radii', required=True, help='tl,tr,br,bl')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    img = Image.open(a.png).convert('RGB')
    x0, y0, x1, y1 = [int(v) for v in a.box.split(',')]
    radii = [int(v) for v in a.radii.split(',')]
    crop = img.crop((x0, y0, x1, y1))
    w, h = crop.size
    alpha = (rounded_mask(w, h, radii) * 255).astype(np.uint8)
    rgba = crop.convert('RGBA')
    rgba.putalpha(Image.fromarray(alpha))
    rgba.save(a.out)
    print('wrote', a.out, rgba.size, 'radii', radii)


if __name__ == '__main__':
    main()
