"""Page blocks extracted from the accepted report implementation; no project data."""
import html
S = {}

def esc(t):return html.escape(str(t))
def br(t):return esc(t).replace('\n','<br>')
def hblock(b):
 k=b[0]
 if k in ('p','note','insight','sub'):
  tag='h3' if k=='sub' else 'div'
  return f'<{tag} class="{k}">{br(b[1])}</{tag}>'
 if k=='quote':
  return f'<blockquote class="original"><p>{br(b[1])}</p><a class="origin-link" href="{esc(b[2])}">原文 ↗</a></blockquote>'
 if k=='fig':return f'<figure><img src="assets/{esc(b[1])}" alt="{esc(b[2])}"><figcaption>{esc(b[2])}</figcaption></figure>'
 if k=='photo':
  return f'<figure class="photo"><a href="{esc(b[3])}" class="image-link"><img src="assets/{esc(b[1])}" alt="{esc(b[2])}" style="max-height:{b[4]}mm"></a><figcaption>{esc(b[2])}</figcaption></figure>'
 if k=='photopair':return '<div class="photo-pair">'+''.join(hblock(x) for x in b[1])+'</div>'
 if k=='cards':return '<div class="cards">'+''.join(f'<div class="card"><h3>{br(a)}</h3><p>{br(t)}</p></div>' for a,t in b[1])+'</div>'
 if k=='table':return '<table class="report-table"><thead><tr>'+''.join(f'<th>{esc(x)}</th>' for x in b[1])+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<{"th" if j==0 else "td"}>{br(x)}</{"th" if j==0 else "td"}>' for j,x in enumerate(row))+'</tr>' for row in b[2])+'</tbody></table>'
 if k=='metrics':return '<div class="metrics">'+''.join(f'<div><b>{esc(n)}</b><h3>{esc(t)}</h3><p>{esc(v)}</p></div>' for n,t,v in b[1])+'</div>'
 if k=='bars':return '<div class="bars">'+''.join(f'<div><span>{esc(n)}</span><b>{v:,.2f}</b><i style="width:{v/max(value for _,value in b[1])*100:.1f}%"></i></div>' for n,v in b[1])+'</div>'
 if k=='timeline':return '<div class="timeline">'+''.join(f'<div><b>{esc(n)}</b><p>{esc(v)}</p></div>' for n,v in b[1])+'</div>'
 raise ValueError(k)
def mdblock(b):
 k=b[0]
 if k=='p':return b[1]
 if k=='note':return '*'+b[1].replace('\n','；')+'*'
 if k=='quote':return '> '+b[1].replace('\n','\n> ')+'\n\n[原文 ↗]('+b[2]+')'
 if k=='insight':return '**'+b[1]+'**'
 if k=='sub':return '### '+b[1]
 if k in ('fig','photo'):
  return f'![{b[2]}](../assets/{b[1]})\n\n{b[2]}'+(f' · [原图]({b[3]})' if k=='photo' and b[3] else '')
 if k=='photopair':return '\n\n'.join(mdblock(x) for x in b[1])
 if k=='cards':return '\n\n'.join('### '+a+'\n\n'+t.replace('\n','；') for a,t in b[1])
 if k=='table':return '| '+' | '.join(b[1])+' |\n| '+' | '.join(['---']*len(b[1]))+' |\n'+'\n'.join('| '+' | '.join(x.replace('\n','<br>') for x in row)+' |' for row in b[2])
 if k=='metrics':return '\n'.join(f'- {n}{t}；{v}' for n,t,v in b[1])
 if k=='bars':return '\n'.join(f'- {n}：{v:,.2f}元/㎡' for n,v in b[1])
 if k=='timeline':return '\n'.join(f'- {n}：{v}' for n,v in b[1])
 raise ValueError(k)
