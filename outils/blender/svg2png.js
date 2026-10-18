// rasterise les SVG en PNG transparents : node svg2png.js <dossier_svg> <dossier_png> <famille> <taille>
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
(async()=>{const [src,dst,fam,T]=process.argv.slice(2);const t=+T;fs.mkdirSync(dst,{recursive:true});
const b=await chromium.launch();const p=await b.newPage({viewport:{width:t,height:t}});
const map={k:'k',q:'q',r:'r',b:'b',n:'n',p:'p'};
for(const col of ['w','b'])for(const k of 'kqrbnp'){
  const svg=fs.readFileSync(path.join(src,`${fam}_${col}${k}.svg`),'utf8').replace('<svg ',`<svg width="${t}" height="${t}" `);
  await p.setContent(`<html><body style="margin:0;background:transparent">${svg}</body></html>`);
  await p.screenshot({path:path.join(dst,k+(col==='b'?'b':'')+'.png'),omitBackground:true,clip:{x:0,y:0,width:t,height:t}});}
await b.close();console.log('OK',fam)})();
