#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""pptx -> PDF -> PNG at a target size.

Direct `render --input x.pptx` on this machine scales the page ~1.5x (a kit quirk),
so we always convert to PDF first and rasterise the PDF.

The design canvas is often not exactly 16:9 (e.g. 1022x578 = 1.768), so pass the
exact source size with --size; otherwise the PNG is resized by width only.

Renderer resolution order:
  1. --node/--cli args
  2. DSH_NODE / DSH_KIT env vars
  3. <user home>\\deepseek\\resources\\app.asar.unpacked\\... (default DSH install)
  4. plain `soffice --headless --convert-to pdf` (needs LibreOffice on PATH)

usage:
  python render.py deck.pptx outdir --size 1022x578
  python render.py deck.pptx outdir --width 1617 --dpi 168
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))


def find_kit():
    node = os.environ.get('DSH_NODE', '')
    cli = os.environ.get('DSH_KIT', '')
    if node and cli and os.path.exists(node) and os.path.exists(cli):
        return node, cli
    home = os.path.expanduser('~')
    node = node or os.path.join(home, r'deepseek\resources\runtime\primary-runtime\dependencies\node\bin\node.exe')
    cli = cli or os.path.join(home, r'deepseek\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js')
    if os.path.exists(node) and os.path.exists(cli):
        return node, cli
    return None, None


def kit_to_pdf(pptx, pdf):
    node, cli = find_kit()
    if not node:
        return False
    p = subprocess.run([node, cli, 'convert', '--input', pptx, '--output', pdf],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit(p.stderr.strip() or p.stdout.strip() or 'kit convert failed')
    return True


def soffice_to_pdf(pptx, pdf):
    exe = os.environ.get('DSH_SOFFICE') or shutil.which('soffice') or shutil.which('libreoffice')
    if not exe:
        return False
    outdir = os.path.dirname(pdf)
    p = subprocess.run([exe, '--headless', '--convert-to', 'pdf', '--outdir', outdir, pptx],
                       capture_output=True, text=True)
    produced = os.path.join(outdir, os.path.splitext(os.path.basename(pptx))[0] + '.pdf')
    if p.returncode != 0 or not os.path.exists(produced):
        raise SystemExit(p.stderr.strip() or 'soffice convert failed')
    os.replace(produced, pdf)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pptx')
    ap.add_argument('outdir')
    ap.add_argument('--size', default='', help='WxH of the design canvas, e.g. 1022x578')
    ap.add_argument('--width', type=int, default=0)
    ap.add_argument('--dpi', type=int, default=192)
    ap.add_argument('--page', type=int, default=1)
    ap.add_argument('--node', default='')
    ap.add_argument('--cli', default='')
    a = ap.parse_args()

    if a.node:
        os.environ['DSH_NODE'] = a.node
    if a.cli:
        os.environ['DSH_KIT'] = a.cli

    os.makedirs(a.outdir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='pptrender-')
    pdf = os.path.join(tmp, 'deck.pdf')
    shots = os.path.join(tmp, 'shots')

    node, cli = find_kit()
    if node:
        kit_to_pdf(a.pptx, pdf)
        subprocess.run([node, cli, 'render', '--input', pdf, '--output-dir', shots,
                        '--pages', str(a.page), '--dpi', str(a.dpi)],
                       check=True, capture_output=True, text=True)
        src = os.path.join(shots, 'page-%04d.png' % a.page)
    else:
        if not soffice_to_pdf(a.pptx, pdf):
            raise SystemExit('no renderer: install LibreOffice (soffice on PATH) '
                             'or point DSH_NODE / DSH_KIT at the bundled kit')
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise SystemExit('PDF rasterising needs PyMuPDF: pip install pymupdf '
                             '(or use the DSH bundled renderer)')
        doc = fitz.open(pdf)
        page = doc[a.page - 1]
        zoom = a.dpi / 72.0
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        src = os.path.join(tmp, 'page.png')
        pix.save(src)

    im = Image.open(src).convert('RGB')
    if a.size:
        w, h = [int(v) for v in a.size.lower().split('x')]
        im = im.resize((w, h), Image.LANCZOS)
    elif a.width:
        h = round(im.height * a.width / im.width)
        im = im.resize((a.width, h), Image.LANCZOS)
    out = os.path.join(a.outdir, 'page-%04d.png' % a.page)
    im.save(out)
    print(json.dumps({'ok': True, 'png': out, 'size': list(im.size)}))


if __name__ == '__main__':
    main()
