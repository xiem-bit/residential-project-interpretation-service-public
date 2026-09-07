"""Page blocks extracted from the accepted report implementation; no project data."""
import html
S = {}

def esc(t):
    return html.escape(str(t))

def br(t):
    return esc(t).replace('\n', '<br>')

def hblock(b):
    k = b[0]
    if k in ('p', 'note', 'insight', 'sub'):
        tag = 'h3' if k == 'sub' else 'div'
        return f'<{tag} class="{k}">{br(b[1])}</{tag}>'
    if k == 'quote':
        s = S[b[3]]
        attribution = f'<a class="origin-link" href="{esc(s["url"])}">{esc(b[2])} · 原文 ↗</a>' if s.get('url') else f'<span class="origin-link">{esc(b[2])}</span>'
        return f'<blockquote class="original"><p>{br(b[1])}</p>{attribution}</blockquote>'
    if k == 'path':
        return '<div class="path">' + ''.join(f'<div><h3>{br(a)}</h3><p>{br(t)}</p></div>' for a, t in b[1]) + '</div>'
    if k == 'bands':
        return '<div class="bands">' + ''.join(f'<article class="band"><div class="band-label">{esc(a)}</div><div><h3>{br(t)}</h3><p>{br(v)}</p></div></article>' for a, t, v in b[1]) + '</div>'
    if k == 'table':
        return '<table class="report-table"><thead><tr>' + ''.join(f'<th>{esc(x)}</th>' for x in b[1]) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<{"th" if j == 0 else "td"}>{br(x)}</{"th" if j == 0 else "td"}>' for j, x in enumerate(row)) + '</tr>' for row in b[2]) + '</tbody></table>'
    if k == 'profile':
        return f'<article class="profile"><h3>{br(b[1])}</h3><p>{br(b[2])}</p><div class="profile-detail"><div><b>优先保什么</b><p>{br(b[3])}</p></div><div><b>本案的机会与限制</b><p>{br(b[4])}</p></div></div></article>'
    if k == 'claim':
        return f'<article class="claim"><span class="claim-label">{esc(b[1])}</span><h3>{br(b[2])}</h3><p>{br(b[3])}</p><div class="claim-result">{br(b[4])}</div></article>'
    if k == 'area':
        return '<div class="area-chart" role="img" aria-label="项目建筑面积及配置比较">' + ''.join(f'<div class="area-row"><span>{esc(a)}</span><div><i style="width:{n / max(value for _, value, _ in b[1]) * 100:.2f}%"></i><b>{n}㎡</b><p>{esc(v)}</p></div></div>' for a, n, v in b[1]) + '</div>'
    if k == 'image':
        return f'<figure class="research-map"><img src="{esc(b[1])}" alt="{esc(b[2])}"><figcaption>{br(b[2])}</figcaption></figure>'
    raise ValueError(k)

def mdblock(b):
    k = b[0]
    if k == 'p': return b[1]
    if k == 'note': return '*' + b[1].replace('\n', '；') + '*'
    if k == 'insight': return '**' + b[1] + '**'
    if k == 'sub': return '### ' + b[1]
    if k == 'quote':
        s = S[b[3]]
        attribution = '[' + b[2] + ' · 原文 ↗](' + s['url'] + ')' if s.get('url') else '——' + b[2]
        return '> ' + b[1].replace('\n', '\n> ') + '\n\n' + attribution
    if k == 'path': return '\n'.join('- ' + a + '：' + v for a, v in b[1])
    if k == 'bands': return '\n\n'.join('### ' + a + '｜' + t + '\n\n' + v for a, t, v in b[1])
    if k == 'table': return '| ' + ' | '.join(b[1]) + ' |\n| ' + ' | '.join(['---'] * len(b[1])) + ' |\n' + '\n'.join('| ' + ' | '.join(x.replace('\n', '<br>') for x in row) + ' |' for row in b[2])
    if k == 'profile': return '### ' + b[1] + '\n\n' + b[2] + '\n\n**优先保什么：**' + b[3] + '\n\n**本案的机会与限制：**' + b[4]
    if k == 'claim': return '### ' + b[1] + '｜' + b[2] + '\n\n' + b[3] + '\n\n**' + b[4] + '**'
    if k == 'area': return '\n'.join('- ' + a + '：' + str(n) + '㎡；' + v for a, n, v in b[1])
    if k == 'image': return '![' + b[2] + '](../' + b[1] + ')'
    raise ValueError(k)
