// 从红星路已运行的原生版式抽取；仅接收当前项目内容，不包含项目事实或历史文案。
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const norm = value => String(value || '').replace(/\s+/g, '');
export async function composeProjectPages(plan, {Presentation, resolvePresentationFont, projectRoot}) {
const ps=plan.pages.map(v=>v.render_content);
const cases=Object.fromEntries(JSON.parse(await fs.readFile(plan.asset_inventory_path || path.join(projectRoot,'references/product3/assets/产物3案例截图素材库/case_asset_inventory.json'),'utf8')).map(v=>[v.asset_id,v]));
const F=resolvePresentationFont({fontFamily:'PingFang SC'}),SERIF=resolvePresentationFont({fontFamily:'Songti SC'});
const K={ink:'#143B34',paper:'#F6F3EB',muted:'#5B6C64',gold:'#B8844C',sage:'#E8EBE2',dark:'#102F29',pale:'#BBCBBF',line:'#B5C4B1'};
const pres=Presentation.create({slideSize:{width:1600,height:900}});
const mapping=[],visible=[];let s,p,m;
const clean=t=>String(t||'').replace(/\n/g,'');
function rect(role,x,y,w,h,fill='none',line='none',radius=0){
 const a=s.shapes.add({name:p.id+'-'+role,geometry:radius?'roundRect':'rect',borderRadius:radius||undefined,position:{left:x,top:y,width:w,height:h},fill,line:{fill:line,width:line==='none'?0:1}});
 m.objects.push({role,anchor_id:a.id,position:{x,y,w,h}});return a;
}
function text(role,value,x,y,w,h,size=23,color=K.ink,bold=false,opts={}){
 if(!value)return;const a=rect(role,x,y,w,h);a.text=String(value);
 a.text.style={typeface:opts.serif?SERIF:F,fontSize:size,color,bold,alignment:opts.align||'left',verticalAlignment:'top',wrap:'square',autoFit:'none',insets:{top:0,bottom:0,left:0,right:0},lineSpacing:opts.line||1.55};
 m.objects[m.objects.length-1].text=String(value);visible.push({page:p.order,role,text:String(value)});return a;
}
async function imageFile(file,x,y,w,h,role,assetId,fit='contain'){
 const bytes=await fs.readFile(file);const im=s.images.add({blob:bytes,contentType:file.endsWith('.png')?'image/png':'image/jpeg',position:{left:x,top:y,width:w,height:h},fit,alt:assetId||role});
 m.objects.push({role,anchor_id:im.id,asset_id:assetId,path:file,position:{x,y,w,h}});return im;
}
async function caseImage(id,x,y,w,h,role){
 const a=cases[id];if(!a)throw Error('未登记案例 '+id);
 const bindings=plan.pages.find(v=>v.page_id===p.id).resolved_assets || [];
 const bound=bindings.find(v=>v.asset_id===id); if(!bound)throw Error(p.id+'素材未在装配清单绑定：'+id);
 if (bound.usage!==a.effective_business_semantic)throw Error(id+'生效语义已变化，请重新核对选图并更新计划');
 if(path.resolve(bound.path)!==path.resolve(projectRoot,a.original_asset))throw Error(id+'文件与案例清单不对应');
 const bytes=await fs.readFile(bound.path); if(hash(bytes)!==bound.sha256)throw Error(id+'原图已变化，需更新生产计划');
 return imageFile(bound.path,x,y,w,h,role,id);
}
function chapter(){return p.chapter_label || (p.chapter===2?'第二章 · 项目理解':'第三章 · UE系统解决方案');}
function head(dark=false,map=false){
 const x=map?55:72,y=map?31:39;
 rect('chapter-rule',x,y+12,32,2,K.gold);
 text('chapter',chapter(),x+46,y,1410,30,map?16:18,dark?'#B8CBC0':K.muted,false,{line:1.2});
 text('title',p.title,x,map?70:77,1600-x*2,62,map?(p.title.length>28?37:39):(p.title.length>28?40:44),dark?K.paper:K.ink,true,{line:1.3});
 text('subtitle',p.sub,x,map?136:140,map?1490:1410,78,map?22:23,dark?K.pale:K.muted,false,{line:1.3});
}
function foot(dark=false,map=false){
 if(map){
  rect('map-footer-bg',30,831,1540,40,'#F6F3EB/94', 'none',3);
  text('footer',p.body.conclusion,41,840,1335,27,14,K.muted,false,{line:1.2});
  text('page_number',String(p.order).padStart(2,'0')+' / '+ps.length,1430,835,100,31,21,K.gold,false,{align:'right',line:1.2});
  rect('map-attribution-bg',1362,876,230,23,'#FFFFFF/92');
  text('map-attribution',p.map.attribution,1369,879,220,20,12,'#58625A',false,{line:1.1});return;
 }
 const f=p.footer || '';
 text('footer',f,72,854,1300,23,14,dark?'#B0C0B5':'#78867D',false,{line:1.2});
 text('page_number',String(p.order).padStart(2,'0')+' / '+ps.length,1428,845,100,34,21,K.gold,false,{align:'right',line:1.2});
}
function wrapRows(v,width,size){
 let n=1,x=0;for(const ch of clean(v)){const k=/[A-Za-z0-9 .,/()—·㎡]/.test(ch)?size*.56:size;if(x+k>width){n++;x=k;}else x+=k;}return n;
}
function mapCard(c,x,y){
 const w=322,pad=18,th=wrapRows(c.title,w-pad*2,24)*33.6;
 const paragraphs=(c.paragraphs||[]).filter(Boolean);
 const heights=paragraphs.map(v=>String(v).split('\n').reduce((n,l)=>n+wrapRows(l,w-pad*2,18),0)*34);
 const h=32+th+8+heights.reduce((a,b)=>a+b,0)+Math.max(0,heights.length-1)*10;
 rect('map-card-'+c.key,x,y,w,h,c.feature?'#153E35/95':'#FBFAF4/95','#A6B4A5/40',9);
 text('map-card-title-'+c.key,c.title,x+pad,y+16,w-pad*2,th,24,c.feature?K.paper:K.ink,true,{line:1.4});
 let yy=y+16+th+8;
 paragraphs.forEach((v,i)=>{text('map-card-body-'+c.key+'-'+i,v,x+pad,yy,w-pad*2,heights[i]+3,18,c.feature?(i===0?'#DFBB87':K.paper):K.ink,false,{line:1.55});yy+=heights[i]+10;});
 return h;
}
async function mapPage(){
 const cfg=p.map; if(!cfg || cfg.width!==1600 || cfg.height!==900)throw Error(p.id+'地图需使用当前1600×900模板对应的坐标与取景');
 await imageFile(cfg.image,0,0,1600,900,'map_base',cfg.asset_id,'cover');
 for(const q of cfg.labels || []){
  if(q.development){
   const a=s.shapes.add({name:p.id+'-development-range',geometry:'ellipse',position:{left:q.x-28,top:q.y-43,width:56,height:86},fill:'#B8844C/24',line:{fill:K.gold,width:2}});m.objects.push({role:'development_range',anchor_id:a.id,position:{x:q.x-28,y:q.y-43,w:56,h:86},boundary:q.precision||p.map.subject_display});
  }else{
   const a=s.shapes.add({name:p.id+'-point-'+q.key,geometry:'ellipse',position:{left:q.x-5,top:q.y-5,width:10,height:10},fill:q.color||K.ink,line:{fill:K.paper,width:1}});m.objects.push({role:'map_point',anchor_id:a.id,label:q.name,source:q.source,position:{x:q.x-5,y:q.y-5,w:10,h:10}});
  }
  const xx=q.x+q.dx,yy=q.y+q.dy,ww=q.label_width||Math.max(100,clean(q.name).length*20+22),hh=q.label_height||(q.development?64:42);
  const ex=Math.max(xx,Math.min(q.x,xx+ww)),ey=Math.max(yy,Math.min(q.y,yy+hh)),lc=q.development?K.gold:K.ink;
  rect('map-leader-x-'+q.key,Math.min(q.x,ex),q.y,Math.max(1.5,Math.abs(ex-q.x)),1.5,lc);
  rect('map-leader-y-'+q.key,ex,Math.min(q.y,ey),1.5,Math.max(1.5,Math.abs(ey-q.y)),lc);
  rect('map-label-bg-'+q.key,xx,yy,ww,hh,q.development?'#B8844C':'#FBFAF4',q.color||K.gold,5);
  text('map-label-'+q.key,q.name,xx+11,yy+7,ww-22,hh-10,q.font_size||(q.development?18:20),q.development?K.paper:K.ink,true,{line:1.25});
 }
 rect('map-header-shade',0,0,1600,210,{type:'gradient',gradientKind:'linear',angleDeg:90,stops:[{offset:0,color:'#F6F3EB/99'},{offset:83000,color:'#F6F3EB/98'},{offset:100000,color:'#F6F3EB/0'}]});
 head(false,true);
 for(const [side,xx] of [['left',30],['right',1248]]){let yy=233;for(const card of p.body.map_cards[side])yy+=mapCard(card,xx,yy)+14;}
 rect('map-meta-bg',380,786,835,39,'#FAF9F0/94','none',4);
 text('map-meta',p.body.map_meta,393,795,807,27,14,'#4A6253',false,{line:1.3});
 foot(false,true);
}
function deckDiagram(x,y,w,h){
 rect('diagram-bg',x,y,w,h,'#E8EBE2');
 const rows=p.body.diagram?.rows; if(!rows)throw Error(p.id+'缺少当前项目逻辑图内容');
 rows.forEach((r,i)=>{const yy=y+35+i*84;rect('deck-level-'+i,x+30,yy,w-131,68,r[2]);text('deck-name-'+i,r[0],x+47,yy+12,185,39,26,K.paper,true,{line:1.2});text('deck-use-'+i,r[1],x+220,yy+16,w-330,38,22,K.paper,false,{line:1.2});});
 text('deck-height',p.body.diagram.height_label,x+w-95,y+117,83,74,25,K.gold,true,{line:1.3});
 text('deck-limit',p.body.diagram.caption,x+30,y+h-34,w-60,25,17,K.muted,false,{line:1.2});
}
async function gallery(){
 for(let i=0;i<2;i++){
  const [id,title,caption]=p.body.pairs[i],x=72+i*743,w=713;
  rect('figure-image-bg-'+i,x,239,w,350,'#162B24');
  if(id==='DIAGRAM-DECK')deckDiagram(x,239,w,350);else await caseImage(id,x,239,w,350,'proof_image_'+(i+1));
  rect('figure-caption-bg-'+i,x,589,w,164,K.sage);
  text('image-title-'+i,title,x+20,607,w-40,40,25,K.ink,true,{line:1.4});
  text('image-caption-'+i,p.body.preserve_caption_breaks?caption:clean(caption),x+20,651,w-40,99,20,'#586D5D',false,{line:1.3});
 }
 const steps=p.body.steps;
 steps.forEach((v,i)=>{const x=72+i*(1456+25)/3;rect('step-rule-'+i,x,772,468.67,1,K.line);text('step-summary-'+i,v,x,788,468.67,47,22,K.ink,false,{line:1.3});});
}
function choiceCards(){
 const cc=p.body.cards;
 if(cc.length===4){
  cc.forEach((a,i)=>{const x=72+(i%2)*748,y=239+Math.floor(i/2)*275,w=708;
   rect('choice-bg-'+i,x,y,w,247,'#EBECE2');rect('choice-rule-'+i,x,y,w,2,K.gold);
   text('choice-number-'+i,'0'+(i+1),x+24,y+22,80,80,60,'#90A89A',false,{serif:true,line:1.1});
   text('card-title-'+i,clean(a[0]),x+126,y+22,w-150,82,30,K.ink,true,{line:1.3});
   text('card-body-'+i,a[1],x+126,y+122,w-150,105,23,'#5D6F63',false,{line:1.4});});
  text('conclusion',p.body.conclusion,72,777,1456,55,25,K.ink,false,{align:'center',line:1.4});return;
 }
 const w=(1456-48)/3;
 cc.forEach((a,i)=>{const x=72+i*(w+24);rect('choice-bg-'+i,x,239,w,493,'#EBECE2');rect('choice-rule-'+i,x,239,w,2,K.gold);
  text('choice-number-'+i,'0'+(i+1),x+24,263,w-48,78,60,'#90A89A',false,{serif:true,line:1.1});
  text('card-title-'+i,clean(a[0]),x+24,365,w-48,140,30,K.ink,true,{line:1.4});
  text('card-body-'+i,a[1],x+24,522,w-48,183,23,'#5D6F63',false,{line:1.6});});
 text('conclusion',p.body.conclusion,72,764,1456,68,25,K.ink,false,{align:'center',line:1.4});
}
function sequence(){
 if(p.body.cards.length===4){
  p.body.cards.forEach((a,i)=>{const y=242+i*148;rect('sequence-line-'+i,72,y,1456,1,'#607C6B');
   text('sequence-number-'+i,'0'+(i+1),72,y+18,100,77,48,'#C39761',false,{serif:true,line:1.2});
   text('card-title-'+i,a[0],182,y+23,320,85,30,K.paper,true,{line:1.4});
   text('card-body-'+i,clean(a[1]),522,y+18,1006,78,26,K.paper,false,{line:1.4});
   text('row-note-'+i,p.body.row_notes[i],522,y+105,1006,32,20,K.pale,false,{line:1.3});});return;
 }
 p.body.cards.forEach((a,i)=>{const y=252+i*171;rect('sequence-line-'+i,72,y,1456,1,'#607C6B');
  text('sequence-number-'+i,'0'+(i+1),72,y+24,100,90,57,'#C39761',false,{serif:true,line:1.2});
  text('card-title-'+i,a[0],182,y+35,320,88,32,K.paper,true,{line:1.4});
  text('card-body-'+i,clean(a[1]),522,y+28,1006,85,28,K.paper,false,{line:1.3});
  text('row-note-'+i,p.body.row_notes[i],522,y+125,1006,33,22,K.pale,false,{line:1.3});});
}
function claims(){
 const benefits=p.body.benefits;
 if(p.body.cards.length===4){
  p.body.cards.forEach((a,i)=>{const x=72+(i%2)*748,y=246+Math.floor(i/2)*300,w=708;
   rect('claim-rule-'+i,x,y,w,1,'#6E8978');
   text('claim-number-'+i,'0'+(i+1),x,y+16,87,87,60,'#C09965',false,{serif:true,line:1.1});
   text('card-title-'+i,clean(a[0]),x+108,y+15,w-128,84,32,K.paper,true,{serif:true,line:1.3});
   text('claim-benefit-'+i,benefits[i],x+108,y+108,w-128,37,23,'#D9BB8E',false,{line:1.4});
   text('card-body-'+i,a[1],x+108,y+162,w-128,106,23,K.pale,false,{line:1.45});});return;
 }
 p.body.cards.forEach((a,i)=>{const x=72+i*(1456+40)/3,w=458.67;rect('claim-rule-'+i,x,250,w,1,'#6E8978');
  text('claim-number-'+i,'0'+(i+1),x,269,w,91,75,'#C09965',false,{serif:true,line:1.1});
  text('card-title-'+i,clean(a[0]),x,369,w-30,181,36,K.paper,true,{serif:true,line:1.5});
  text('claim-benefit-'+i,benefits[i],x,559,w-30,45,23,'#D9BB8E',false,{line:1.4});
  text('card-body-'+i,a[1],x,617,w-30,184,22,K.pale,false,{line:1.7});});
}
function scope(){
 p.body.levels.forEach((a,i)=>{const x=72+i*(1456+13)/7,w=(1456-78)/7;rect('scope-bg-'+i,x,239,w,184,'#E7EBDF');rect('scope-rule-'+i,x,239,w,2,K.gold);text('scope-title-'+i,a[0],x+18,265,w-36,43,29,K.ink,true,{line:1.3});text('scope-copy-'+i,a[1],x+18,334,w-36,83,21,'#62715C',false,{line:1.6});});
 text('scope-project',p.body.scope_heading,72,457,1456,46,27,K.ink,true,{line:1.3});
 p.body.included.forEach((v,i)=>{const x=72+(i%4)*367,y=514+Math.floor(i/4)*81;rect('scope-item-bg-'+i,x,y,355,65,'#183F32');text('scope-item-'+i,v,x+24,y+16,307,38,25,'#E8EBDE',false,{line:1.3});});
 text('conclusion',p.body.conclusion,72,701,1456,110,23,'#5E715E',false,{line:1.7});
}
function ai(){
 rect('ai-ui',72,239,690,551,'#E9ECDF','none',9);
 text('ai-label',p.body.ai_ui.label,106,270,622,37,19,'#617865',false,{line:1.4});
 text('ai-question',p.body.ai_ui.question,106,328,622,122,36,K.ink,true,{serif:true,line:1.5});
 const prompts=p.body.ai_ui.prompts;
 prompts.forEach((v,i)=>{const y=471+i*95;rect('ai-pick-bg-'+i,106,y,622,78,i===0?'#214E3D':'#E9ECDF','#ADBFAA',6);text('ai-pick-'+i,v,130,y+20,574,46,25,i===0?K.paper:K.ink,false,{line:1.3});});
 const xx=838;
 p.body.ai_ui.flows.forEach((v,i)=>{const y=262+i*87;text('ai-flow-number-'+i,'0'+(i+1),xx,y,58,54,32,'#C69A62',false,{serif:true,line:1.3});text('ai-flow-'+i,v,xx+73,y,615,54,30,K.paper,false,{line:1.4});rect('ai-flow-line-'+i,xx,y+64,690,1,'#637E6A');});
 text('conclusion',p.body.conclusion,838,574,690,187,24,'#C0D0BD',false,{line:1.8});
 text('note',p.body.note,838,773,690,55,17,'#B0C0B5',false,{line:1.5});
}
async function family(){
 const pairs=p.body.pairs,slots=plan.pages.find(v=>v.page_id===p.id).case_slots || [];
 if(!Array.isArray(pairs)||pairs.length<2||pairs.length>4||pairs.length!==slots.length||pairs.some((v,i)=>v[0]!==slots[i].asset_id))throw Error(p.id+'人物图片须逐一装入已裁定版位；当前家庭卡片支持2至4个版位');
 const gap=24,w=(1456-gap*(pairs.length-1))/pairs.length;
 for(let i=0;i<pairs.length;i++){
  const [id,title,caption]=pairs[i],x=72+i*(w+gap);
  await caseImage(id,x,239,w,300,'portrait_image_'+(i+1));
  rect('family-caption-bg-'+i,x,539,w,265,K.sage);
  text('image-title-'+i,title,x+20,557,w-40,68,28,K.ink,true,{line:1.3});
  text('image-caption-'+i,caption,x+20,641,w-40,144,22,'#586D5D',false,{line:1.45});
 }
}
async function cover(){
 if(p.body.cover_image)await imageFile(p.body.cover_image,925,0,675,900,'cover_map',p.body.cover_image_id,'cover');
 rect('cover-fade',0,0,1600,900,{type:'gradient',gradientKind:'linear',angleDeg:0,stops:[{offset:0,color:K.dark},{offset:48000,color:K.dark},{offset:100000,color:'#102F29/64'}]});
 text('project-name',p.body.project_heading,85,72,1430,51,22,'#D1DDD2',false,{line:1.3});
 text('cover-title',p.body.cover_title_lines?.[0] || p.title,85,211,1340,115,69,K.paper,true,{serif:true,line:1.45});
 text('cover-title-emphasis',p.body.cover_title_lines?.[1] || '',85,320,1430,115,69,'#DDBB88',true,{serif:true,line:1.45});
 rect('cover-rule',89,451,82,3,K.gold);
 text('subtitle',p.sub,89,491,1260,202,29,'#CAD6CA',false,{line:1.8});
 text('cover-note',p.body.note,89,771,1400,45,21,'#C3CFC4',false,{line:1.4});
 foot(true,false);
}
function closing(){
 rect('closing-rule',72,51,32,2,K.gold);text('chapter',p.body.project_heading,118,39,1410,32,18,'#B8CBC0',false,{line:1.3});
 text('title',p.title,83,194,1402,267,63,K.paper,true,{serif:true,line:1.55});
 text('closing-sub',p.sub,87,505,1400,81,29,'#D5B88B',false,{line:1.75});
 const cc=p.body.closing_cards;
 cc.forEach((a,i)=>{const x=87+i*(1426+30)/3,w=(1426-60)/3;rect('closing-line-'+i,x,641,w,1,'#657F6C');text('card-title-'+i,a[0],x,667,w,46,26,'#CEDBCA',false,{line:1.3});text('card-body-'+i,a[1],x,728,w,94,22,K.pale,false,{line:1.5});});foot(true,false);
}

for(let index=0;index<ps.length;index++){
 p=ps[index];const pp=plan.pages[index];
 if(!p || p.id!==pp.page_id)throw Error('页面内容与装配清单身份不一致');
 if(!['cover','map','gallery','deck_gallery','anchor','sequence','overview','scope','ai','close','choices','family'].includes(p.layout))throw Error('未支持的版式：'+p.layout+'；按现有模板补充实现，不得回退历史文案');
 if(pp.semantic_id==='P3-COMPETITION-MAP' && pp.visual_structure?.includes('全屏') && p.layout!=='map')throw Error(p.id+'已指定全屏空间比较，不得换成小地图或表格');
 if(pp.semantic_id==='P3-FAMILY-SEGMENT' && (!['family','gallery'].includes(p.layout) || JSON.stringify((p.body.pairs||[]).map(v=>v[0]))!==JSON.stringify((pp.case_slots||[]).map(v=>v.asset_id))))throw Error(p.id+'实际人物版位与已选版位不一致');
 if((p.layout==='gallery'||p.layout==='deck_gallery')&&(p.body.pairs?.length!==2 || (p.body.steps||[]).some(v=>typeof v!=='string')))throw Error(p.id+'双图模板需两处画面及当前项目的短句');
 s=pres.slides.add();const dark=['cover','anchor','ai','close','sequence'].includes(p.layout)||p.theme==='dark';s.background.fill=dark?K.dark:K.paper;
 m={page_id:p.id,order:index+1,objects:[]};mapping.push(m);
 if(p.layout==='cover')await cover();
 else if(p.layout==='map')await mapPage();
 else if(p.layout==='close')closing();
 else{
  head(dark);
  if(p.layout==='choices'){
   const w=(1456-32)/3;p.body.cards.forEach((v,i)=>{const x=72+i*(w+16);rect('voice-bg-'+i,x,239,w,575,'#FFFEF9');rect('voice-rule-'+i,x,239,w,3,i%2?'#608876':'#BD9765');text('voice-title-'+i,v[0],x+21,270,w-42,62,27,K.ink,true,{line:1.4});text('voice-copy-'+i,v[1],x+21,354,w-42,242,23,'#364C42',false,{line:1.6});if(v[2])text('quote-'+i,v[2],x+21,650,w-42,117,23,K.gold,true,{line:1.6});});
  }else if(['gallery','deck_gallery'].includes(p.layout))await gallery();
  else if(p.layout==='family')await family();
  else if(p.layout==='anchor')claims();
  else if(p.layout==='sequence')sequence();
  else if(p.layout==='overview')choiceCards();
  else if(p.layout==='scope')scope();
  else if(p.layout==='ai')ai();
  foot(dark);
 }
 const copy=visible.filter(v=>v.page===p.order && v.role!=='page_number');
 // Whitespace changes are layout-only. Wording and punctuation must remain identical.
 if(norm(copy.map(v=>v.text).join(''))!==norm(pp.visible_copy))throw Error(p.id+'实际装载文字与已编辑页面文案不一致；请更新内容输入，不能从备注补正文');
 for(const obj of m.objects.filter(v=>v.asset_id)){
  const ref=(pp.resolved_assets||[]).find(v=>v.asset_id===obj.asset_id);
  if(!ref || hash(await fs.readFile(obj.path))!==ref.sha256)throw Error(p.id+'图片未绑定或文件已变化：'+obj.asset_id);
 }
 s.speakerNotes.textFrame.setText([pp.responsibility,pp.speaking_action,pp.transition,'视觉参照：'+pp.visual_reference,...m.objects.filter(v=>v.asset_id).map(v=>'素材：'+v.asset_id)].filter(Boolean).join('\n'));
}
return {presentation:pres, authored_pages:mapping, visible};
}
