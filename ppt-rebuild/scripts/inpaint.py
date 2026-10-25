#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Remove baked text from a photo by nearest-known-neighbour fill (keeps surrounding structure).

Two polarities:
  --mode light : white text on a photo (min channel > thr)      [default]
  --mode dark  : dark text on a light photo (luminance < thr)

usage:
  python inpaint.py bg.png --box 135,107,335,540 --out card.png
  python inpaint.py bg.png --box 26,12,222,68 --mode dark --thr 120 --out bg2.png
"""
import argparse

import numpy as np
from PIL import Image, ImageFilter


def dilate(mask, r=1):
    m = mask.copy()
    for _ in range(r):
        m2 = m.copy()
        m2[1:, :] |= m[:-1, :]; m2[:-1, :] |= m[1:, :]
        m2[:, 1:] |= m[:, :-1]; m2[:, :-1] |= m[:, 1:]
        m = m2
    return m


def bfs_fill(img, mask):
    val = img.copy()
    known = ~mask
    h, w = mask.shape
    for _ in range(300):
        if known.all():
            break
        nv = val.copy()
        newly = np.zeros((h, w), bool)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            Ks = np.zeros((h, w), bool); Vs = np.zeros_like(val)
            ys0 = max(0, dy); ys1 = h + min(0, dy); xs0 = max(0, dx); xs1 = w + min(0, dx)
            Ks[ys0:ys1, xs0:xs1] = known[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
            Vs[ys0:ys1, xs0:xs1] = val[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
            take = (~known) & Ks & (~newly)
            nv[take] = Vs[take]; newly |= take
        val[newly] = nv[newly]; known |= newly
    return val


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('png')
    ap.add_argument('--box', required=True, help='x0,y0,x1,y1')
    ap.add_argument('--out', required=True)
    ap.add_argument('--mode', choices=['light', 'dark'], default='light')
    ap.add_argument('--thr', type=int, default=0, help='205 for light, 120 for dark')
    ap.add_argument('--dilate', type=int, default=1)
    a = ap.parse_args()

    img = np.asarray(Image.open(a.png).convert('RGB')).astype(np.float32)
    x0, y0, x1, y1 = [int(v) for v in a.box.split(',')]
    sub = img[y0:y1, x0:x1]
    lum = 0.299 * sub[:, :, 0] + 0.587 * sub[:, :, 1] + 0.114 * sub[:, :, 2]
    blur = np.asarray(Image.fromarray(np.clip(sub, 0, 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(6))).astype(np.float32)
    blur_lum = 0.299 * blur[:, :, 0] + 0.587 * blur[:, :, 1] + 0.114 * blur[:, :, 2]

    if a.mode == 'light':
        thr = a.thr or 205
        mask = (sub.min(axis=2) > thr) & ((sub.min(axis=2) - blur.min(axis=2)) > 6)
    else:
        thr = a.thr or 185
        mask = (lum < thr) & ((blur_lum - lum) > 6)

    mask = dilate(mask, a.dilate)
    out = bfs_fill(sub, mask)
    soft = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32)
    out[mask] = soft[mask]
    img[y0:y1, x0:x1] = out
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(a.out)
    print('cleaned %d px ->' % int(mask.sum()), a.out)


if __name__ == '__main__':
    main()
