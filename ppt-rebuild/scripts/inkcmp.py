#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compare a rendered slide against the source screenshot.

- global MAE / share of pixels over 30 levels
- per-block ink bounding boxes (source vs render) and their deltas
- optional diff map

usage:
  python inkcmp.py source.png render.png [--blocks blocks.json] [--out diff.png] [--thr 200]

blocks.json:
  [{"name":"title","box":[x0,y0,x1,y1],"mode":"dark","thr":120},
   {"name":"card1 text","box":[150,200,330,470],"mode":"light"}]
  mode: dark (ink darker than thr) | light (white text) | orange (brand orange)
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image


def load(path):
    return np.asarray(Image.open(path).convert('RGB')).astype(float)


def mask_for(sub, mode, thr, explicit):
    if mode == 'dark':
        lum = 0.299 * sub[:, :, 0] + 0.587 * sub[:, :, 1] + 0.114 * sub[:, :, 2]
        return lum < explicit
    if mode == 'light':
        return sub.min(axis=2) > explicit
    if mode == 'orange':
        r, g, b = sub[:, :, 0], sub[:, :, 1], sub[:, :, 2]
        return (r > 200) & (g > 50) & (g < 160) & (b < 110)
    raise ValueError(mode)


def bbox(a, box, mode, thr):
    x0, y0, x1, y1 = [int(v) for v in box]
    sub = a[y0:y1, x0:x1]
    if sub.size == 0:
        return None
    m = mask_for(sub, mode, thr, thr)
    ys, xs = np.where(m)
    if len(xs) == 0:
        return None
    return [x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()), y0 + int(ys.max())]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('ren')
    ap.add_argument('--blocks', default='')
    ap.add_argument('--out', default='')
    ap.add_argument('--thr', type=int, default=200)
    a = ap.parse_args()

    s = load(a.src)
    r = load(a.ren)
    if s.shape != r.shape:
        raise SystemExit('size mismatch: %s vs %s' % (s.shape, r.shape))

    d = np.abs(s - r).mean(axis=2)
    print('size %dx%d  MAE %.2f  >30 %.2f%%' % (s.shape[1], s.shape[0],
                                                d.mean(), (d > 30).mean() * 100))

    if a.blocks:
        blocks = json.load(open(a.blocks, encoding='utf-8'))
        worst = 0
        for b in blocks:
            mode = b.get('mode', 'light')
            thr = b.get('thr', a.thr)
            bs = bbox(s, b['box'], mode, thr)
            br = bbox(r, b['box'], mode, thr)
            name = b.get('name', '?')
            if not bs or not br:
                print('%-14s missing (src=%s ren=%s)' % (name, bs, br))
                continue
            dx, dy = br[0] - bs[0], br[1] - bs[1]
            dw = (br[2] - br[0]) - (bs[2] - bs[0])
            dh = (br[3] - br[1]) - (bs[3] - bs[1])
            worst = max(worst, abs(dx), abs(dy))
            print('%-14s d=(%+d,%+d) dw=%+d dh=%+d' % (name, dx, dy, dw, dh))
        print('worst offset: %d px' % worst)

    if a.out:
        Image.fromarray(np.clip(d * 4, 0, 255).astype(np.uint8)).save(a.out)
        print('diff ->', a.out)


if __name__ == '__main__':
    main()
