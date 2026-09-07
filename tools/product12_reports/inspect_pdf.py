from pathlib import Path
import pypdfium2 as pdf
from PIL import Image,ImageDraw
import argparse
parser=argparse.ArgumentParser(description='Render and inspect an exported report')
parser.add_argument('pdf',type=Path)
parser.add_argument('input',type=Path,help='Report JSON used for render_report.py')
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
p=args.output;p.mkdir(parents=True,exist_ok=True)
d=pdf.PdfDocument(str(args.pdf));out=p/'preview';out.mkdir(exist_ok=True)
print('PDF pages',len(d))
for j in range(len(d)):
 im=d[j].render(scale=1.5).to_pil();im.save(out/f'p{j+1:02}.png')
for start in range(0,len(d),9):
 ids=range(start,min(start+9,len(d)));canvas=Image.new('RGB',(990,3*476),'#dad9d5');draw=ImageDraw.Draw(canvas)
 for k,j in enumerate(ids):
  im=Image.open(out/f'p{j+1:02}.png');im.thumbnail((316,447));x=k%3*330+7;y=k//3*476+22;canvas.paste(im,(x,y));draw.text((x,y-17),str(j+1),fill='black')
 canvas.save(out/f'contact_{start+1:02}.jpg')
texts=[d[j].get_textpage().get_text_range() for j in range(len(d))]
import json,re,unicodedata,xml.etree.ElementTree as ET
from collections import Counter
from urllib.parse import unquote
assert len(d)==len(json.loads(args.input.read_text())['pages'])
assert all(f'{i+1:02} / {len(d):02}' in t for i,t in enumerate(texts))
(p/'PDF文本.txt').write_text('\n\n'.join(texts))
layout_file = args.pdf.parents[2] / 'qa/版面检查.json'
if layout_file.is_file():
 expected = json.loads(layout_file.read_text())['layout']
 # Chrome's CJK SVG font can expose the BLUE radical glyph for the same printed 青.
 normalize = lambda s: re.sub(r'\s+', '', unicodedata.normalize('NFKC',s).replace('\u2ed8','青'))
 assert len(expected) == len(texts)
 for e,t in zip(expected,texts):
  svg_text=[]
  for image in e['images']:
   src=unquote(image['src'])
   if src.lower().endswith('.svg'):
    tree=ET.parse(layout_file.parents[1]/src)
    svg_text.extend(''.join(node.itertext()) for node in tree.iter() if node.tag.rsplit('}',1)[-1]=='text')
  actual=normalize(t)
  # PDF reading order may differ for columns; complete phrases and text counts must survive.
  fragments=e.get('textFragments',[e['visibleText']])+svg_text
  assert all(normalize(x) in actual for x in fragments), f"Page {e['page']}: visible phrase missing or changed"
  assert Counter(normalize(e['visibleText']+''.join(svg_text)))==Counter(actual), f"Page {e['page']}: extra or missing text"
print('Page footers checked; rendered all pages.')
