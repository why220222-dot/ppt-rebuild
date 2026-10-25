#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Preflight: will this machine reproduce the same result?

checks python deps, the renderer (DSH kit or LibreOffice+PyMuPDF), fonts used by the
prompt, and prints a short JSON report. Run this first after installing the skill.

usage:
  python doctor.py
"""
import glob
import importlib.util
import json
import os
import shutil
import sys


def has(mod):
    return importlib.util.find_spec(mod) is not None


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


def has_font(name):
    windir = os.environ.get('WINDIR', r'C:\Windows')
    for f in glob.glob(os.path.join(windir, 'Fonts', '*')):
        try:
            from PIL import ImageFont
            ft = ImageFont.truetype(f, 12)
            if name.lower() in (ft.getname()[0] or '').lower():
                return f
        except Exception:
            continue
    return ''


def main():
    rep = {'python': sys.version.split()[0], 'deps': {}, 'renderer': {}, 'fonts': {}}
    for m in ('PIL', 'numpy'):
        rep['deps'][m] = has(m)

    node, cli = find_kit()
    rep['renderer']['dsh_kit'] = bool(node)
    if node:
        rep['renderer']['node'] = node
        rep['renderer']['cli'] = cli
    rep['renderer']['soffice'] = shutil.which('soffice') or shutil.which('libreoffice') or ''
    rep['renderer']['pymupdf'] = has('fitz')

    for f in ('Microsoft YaHei', 'Microsoft YaHei Light', 'Arial', '华文行楷', 'STXingkai'):
        rep['fonts'][f] = has_font(f)

    ok = all(rep['deps'].values()) and (rep['renderer']['dsh_kit'] or (rep['renderer']['soffice'] and rep['renderer']['pymupdf']))
    if not rep['renderer']['dsh_kit'] and rep['renderer']['soffice'] and not rep['renderer']['pymupdf']:
        rep['hint'] = 'soffice 在，但缺 PyMuPDF：pip install pymupdf'
    if not rep['fonts'].get('Microsoft YaHei'):
        rep['hint'] = '缺少微软雅黑：字体替代会让字号/字距需要重新标定'
    if not (rep['fonts'].get('华文行楷') or rep['fonts'].get('STXingkai')):
        rep.setdefault('hint', '缺少华文行楷：书法标题需换同类字体并重测墨迹度量')
    rep['ok'] = bool(ok)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main()
