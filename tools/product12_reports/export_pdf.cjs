const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
const {createHash} = require('crypto');
if (process.argv.includes('--help') || process.argv.length !== 4) {
  console.log('Usage: node export_pdf.cjs <report.html> <output.pdf> (resolve playwright with NODE_PATH)');
  process.exit(process.argv.includes('--help') ? 0 : 2);
}
const {chromium} = require('playwright');

(async () => {
  const html = path.resolve(process.argv[2]);
  const out = path.dirname(html);
  const pdf = path.resolve(process.argv[3]);
  fs.mkdirSync(path.join(out, 'qa'), {recursive:true});
  fs.mkdirSync(path.dirname(pdf), {recursive:true});
  const browser = await chromium.launch({headless: true, channel: 'chrome'});
  try {
    const context = await browser.newContext({viewport: {width: 1100, height: 1400}});
    await context.route(/^https?:/, route => route.abort());
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(pathToFileURL(html).href, {waitUntil: 'load'});
    await page.emulateMedia({media: 'print'});
    await page.evaluate(async () => {await document.fonts.ready; await Promise.all([...document.images].map(im => im.decode()));});
    const layout = await page.evaluate(() => [...document.querySelectorAll('section.page')].map(el => {
      const main = el.querySelector('main');
      const foot = el.querySelector('footer').getBoundingClientRect();
      const bounds = el.getBoundingClientRect();
      const rects = [...main.querySelectorAll('*')].filter(x => x.getBoundingClientRect().width > 0).map(x => x.getBoundingClientRect());
      const contentBottom = Math.max(main.getBoundingClientRect().bottom, ...rects.map(x => x.bottom));
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      const textFragments = [];
      while (walker.nextNode()) {
        const node = walker.currentNode;
        if (node.textContent.trim() && node.parentElement.getClientRects().length) textFragments.push(node.textContent);
      }
      return {
        page: Number(el.dataset.page),
        title: el.querySelector('h1').innerText.replaceAll('\n',''),
        visibleText: el.innerText,
        textFragments,
        footerGapPx: Math.round((foot.top-contentBottom)*100)/100,
        horizontalOverflow: rects.some(x => x.left < bounds.left-1 || x.right > bounds.right+1),
        images: [...el.querySelectorAll('img')].map(im => ({src: im.getAttribute('src'), loaded: im.complete && im.naturalWidth>0}))
      };
    }));
    const report = {
      htmlSha256: createHash('sha256').update(fs.readFileSync(html)).digest('hex'),
      pages: layout.length, errors, layout,
      passed: errors.length===0 && layout.every(x => x.footerGapPx>=12 && !x.horizontalOverflow && x.images.every(im=>im.loaded))
    };
    fs.writeFileSync(path.join(out,'qa/版面检查.json'), JSON.stringify(report,null,2)+'\n');
    fs.writeFileSync(path.join(out,'qa/实际可见文字.txt'), layout.map(x=>x.visibleText).join('\n\n')+'\n');
    console.log(JSON.stringify({pages:report.pages,passed:report.passed,minFooterGapPx:Math.min(...layout.map(x=>x.footerGapPx)),issues:layout.filter(x=>x.footerGapPx<12||x.horizontalOverflow)}));
    if (!report.passed) throw Error('Adjust the reported layout before exporting.');
    await page.pdf({path:pdf,format:'A4',preferCSSPageSize:true,printBackground:true,margin:{top:0,bottom:0,left:0,right:0}});
    console.log('PDF exported');
  } finally {await browser.close();}
})().catch(e => {console.error(e.message);process.exitCode=1;});
