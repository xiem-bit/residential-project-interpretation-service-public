#!/usr/bin/env python3
"""Render independent P1/P2 inputs with the existing accepted page blocks."""
import argparse
import importlib
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit


def source_links(text):
    """Markdown lives in source/, one level below the HTML-relative assets."""
    def relative(match):
        url = match.group(1)
        if not urlsplit(url).scheme and not url.startswith(('/', '#', '../')):
            url = '../' + url
        return '](' + url + ')'
    return re.sub(r'\]\(([^)]+)\)', relative, text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='JSON: meta, sources, pages')
    parser.add_argument('--kind', choices=('p1', 'p2'), required=True)
    parser.add_argument('--assets', type=Path, required=True, help='This report own local images')
    parser.add_argument('--output', type=Path, required=True, help='New report directory')
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    meta, pages, sources = data['meta'], data['pages'], data['sources']
    for key in ('title', 'header', 'footer', 'date'):
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            raise ValueError(f'meta.{key} must be explicit')
    if not isinstance(pages, list) or not pages:
        raise ValueError('pages must not be empty')
    blocks = importlib.import_module('blocks_' + args.kind)
    blocks.S = sources
    h, br = blocks.esc, blocks.br
    body, md, titles, index = [], ['# ' + meta['title']], [], []
    for i, page in enumerate(pages, 1):
        refs = {key: sources[key] for key in page.get('refs', [])}
        links = ' · '.join(f'<a href="{h(sources[key]["url"])}">{h(label)} ↗</a>'
                           for key, label in page.get('links', []))
        content = '\n'.join(blocks.hblock(block) for block in page['blocks'])
        body.append(f'<section class="page {h(page.get("layout", ""))}" data-page="{i}">'
                    f'<header class="running"><span>{h(meta["header"])}</span><span>{h(page["section"])}</span></header>'
                    f'<main><h1 class="page-title">{br(page["title"])}</h1><p class="page-lead">{h(page["lead"])}</p>'
                    f'{content}<div class="light-links">{links}</div></main>'
                    f'<footer class="footer"><span>{h(meta["footer"])}</span><span>{h(meta["date"])}</span>'
                    f'<b>{i:02d} / {len(pages):02d}</b></footer></section>')
        md.append(f'## {i:02d}｜{page["title"]}\n\n{page["lead"]}\n\n' +
                  '\n\n'.join(source_links(blocks.mdblock(block)) for block in page['blocks']))
        titles.extend([page['title'], page['lead']])
        for block in page['blocks']:
            if block[0] in ('sub', 'insight'):
                titles.append(block[1])
            elif block[0] in ('cards', 'path'):
                titles.extend(row[0] for row in block[1])
            elif block[0] == 'profile':
                titles.append(block[1])
            elif block[0] == 'claim':
                titles.extend([block[2], block[4]])
            elif block[0] == 'bands':
                titles.extend(row[1] for row in block[1])
        index.append({'page': i, 'title': page['title'], 'sources': refs})
    # A new directory keeps accepted reports and user edits out of the write path.
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(args.assets, args.output / 'assets')
    styles = Path(__file__).parent / 'styles'
    shutil.copyfile(styles / 'base.css', args.output / 'assets/base.css')
    shutil.copyfile(styles / (args.kind + '.css'), args.output / 'assets/report.css')
    for name in ('source', 'internal', 'qa'):
        (args.output / name).mkdir()
    shutil.copyfile(args.input, args.output / 'internal/input.json')
    (args.output / 'source/report.md').write_text('\n\n---\n\n'.join(md) + '\n')
    (args.output / 'qa/assertions.txt').write_text('\n'.join(titles) + '\n')
    (args.output / 'internal/sources-by-page.json').write_text(json.dumps(index, ensure_ascii=False, indent=2))
    (args.output / 'report.html').write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{h(meta["title"])}</title><link rel="stylesheet" href="assets/report.css"></head>'
        '<body>' + ''.join(body) + '</body></html>')
    print(json.dumps({'pages': len(pages), 'output': str(args.output.resolve())}, ensure_ascii=False))


if __name__ == '__main__':
    main()
