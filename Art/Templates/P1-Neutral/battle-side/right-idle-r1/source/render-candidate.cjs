// Render a single fixed authoring transform; never crop by alpha or refit parts.
const fs=require('node:fs'), path=require('node:path'), http=require('node:http');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
(async()=>{
 const server=http.createServer((req,res)=>{
  const pathname=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname);
  const file=path.resolve(root,'.'+pathname);
  if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
  fs.readFile(file,(err,data)=>{
   if(err){res.writeHead(404).end();return;}
   res.setHeader('Content-Type',file.endsWith('.png')?'image/png':'text/html; charset=utf-8');res.end(data);
  });
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 let browser;
 try{
  browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  const page=await browser.newPage({viewport:{width:256,height:256},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const url=`http://127.0.0.1:${server.address().port}/authoring.html`;
  await page.goto(url+'?export=1');await page.evaluate(()=>window.poseReady);
  await page.screenshot({path:path.join(root,'00.png'),omitBackground:true});
  const transform=await page.locator('#source').evaluate(i=>({matrix:getComputedStyle(i).transform,offset:[parseFloat(i.style.left),parseFloat(i.style.top)]}));
  await page.setViewportSize({width:1024,height:1024});await page.goto(url);await page.evaluate(()=>window.poseReady);
  await page.screenshot({path:path.join(root,'review.png')});
  if(errors.length)throw new Error(errors.join('\n'));
  console.log(JSON.stringify({renderedPose:[256,256],review:[1024,1024],reviewUses:'registered 00.png at 4x; not enlarged source art',transform,errors}));
 }finally{if(browser)await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
