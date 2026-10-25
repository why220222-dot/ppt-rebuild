#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fit a white mask over a photo: mask opacity + the real bounds of each window (hole).

The mask is  O = P*(1-a) + 255*a.  At a card edge we do not know P, so we estimate
a from pairs just inside (P) and just outside (O) the same row:
    a = (O - P) / (255 - P)
The hole bottom is NOT the card's visual bottom: the mask often covers the lower part
of the card, so we look for the one-row jump where the vivid panel turns mask-pale.

usage:
  python maskfit.py slide.png --cards "135,107,335,574;410,107,611,574;686,107,886,574"
      [--out probe.json] [--step 60] [--edge 25]
"""
import argparse
import json
import sys

import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('png')
    ap.add_argument('--cards', required=True, help='x0,y0,x1,y1;...')
    ap.add_argument('--out', default='')
    ap.add_argument('--step', type=float, default=60.0, help='row jump that marks the hole bottom')
    ap.add_argument('--edge', type=float, default=25.0, help='column jump that marks left/right edges')
    a = ap.parse_args()

    img = np.asarray(Image.open(a.png).convert('RGB')).astype(float)
    H, W, _ = img.shape
    cards = [[int(v) for v in c.split(',')] for c in a.cards.split(';') if c.strip()]
    out = []

    for (x0, y0, x1, y1) in cards:
        rec = {'input': [x0, y0, x1, y1]}
        cx = (x0 + x1) // 2

        # hole bottom: walk down the centre line, find the big one-row jump
        col = img[:, cx, :]
        steps = []
        for y in range(max(1, y0), min(H, y1 + 40)):
            d = float(np.abs(col[y] - col[y - 1]).max())
            if d > a.step:
                steps.append((y, round(d, 1)))
        rec['row_steps'] = steps[-3:]
        if steps:
            cut = steps[-1][0]
            rec['hole_bottom'] = cut
            rec['hole_height'] = cut - y0

        # left/right edges at mid height
        cy = max(y0 + 5, min(H - 6, (y0 + min(y1, rec.get('hole_bottom', y1))) // 2))
        row = img[cy, :, :]
        for name, rng in (('left', range(max(1, x0 - 25), x0 + 25)),
                          ('right', range(min(W - 2, x1 - 25), min(W - 1, x1 + 25)))):
            best = None
            for x in rng:
                d = float(np.abs(row[x] - row[x - 1]).max())
                if best is None or d > best[0]:
                    best = (d, x)
            if best and best[0] > a.edge:
                rec[name] = best[1]
                rec[name + '_jump'] = round(best[0], 1)

        # alpha from inside/outside pairs on the left edge
        if 'left' in rec:
            xl = rec['left']
            alphas = []
            for y in range(y0 + 10, min(rec.get('hole_bottom', y1) - 10, y1), 20):
                P = img[y, xl + 4]
                O = img[y, max(0, xl - 4)]
                den = 255.0 - P
                if np.abs(den).max() < 40:
                    continue
                h = (O - P) / np.where(np.abs(den) < 1e-6, 1e-6, den)
                alphas.append(h)
            if alphas:
                rec['alpha'] = [round(float(v), 3) for v in np.median(np.array(alphas), axis=0)]
        out.append(rec)

    print(json.dumps(out, ensure_ascii=False, indent=1))
    if a.out:
        json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
