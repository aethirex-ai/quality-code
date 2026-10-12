import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

let input = '';
for await (const chunk of process.stdin) {
  input += chunk;
  if (input.length > 96 * 1024 * 1024) throw new Error('oversized renderer input');
}
const req = JSON.parse(input);
const { chromium } = await import(req.module.startsWith('/') ? pathToFileURL(req.module).href : req.module);
const browser = await chromium.launch({headless:true});
try {
  if (req.op === 'check') {
    console.log(JSON.stringify({ready:true}));
  } else {
    const assets = req.assets;
    const errors = [], blocked = [];
    const types = {'.html':'text/html', '.css':'text/css', '.js':'text/javascript', '.mjs':'text/javascript',
      '.json':'application/json', '.svg':'image/svg+xml', '.png':'image/png', '.jpg':'image/jpeg',
      '.jpeg':'image/jpeg', '.gif':'image/gif', '.webp':'image/webp', '.avif':'image/avif',
      '.ico':'image/x-icon', '.woff':'font/woff', '.woff2':'font/woff2', '.ttf':'font/ttf'};
    const context = await browser.newContext({viewport:{width:req.viewport,height:900},
      deviceScaleFactor:1, serviceWorkers:'block', acceptDownloads:false});
    await context.route('**/*', async route => {
      try {
        const url = new URL(route.request().url());
        if (url.origin !== 'http://preview.local' || route.request().method() !== 'GET') throw new Error('origin/method blocked');
        const relative = decodeURIComponent(url.pathname).slice(1);
        if (!relative || relative.split('/').some(p => !p || p.startsWith('.') || p.includes(':') || p.includes('\\'))) throw new Error('path blocked');
        const contentType = types[path.extname(relative).toLowerCase()];
        if (!contentType || !Object.hasOwn(assets, relative)) throw new Error('asset unavailable');
        await route.fulfill({status:200,contentType,body:Buffer.from(assets[relative], 'base64')});
      } catch {
        if (blocked.length < 12) blocked.push(route.request().url().slice(0,180));
        await route.abort('blockedbyclient');
      }
    });
    // WebSocket transports have a separate interception API.
    await context.routeWebSocket('**/*', ws => ws.close());
    const page = await context.newPage();
    page.setDefaultTimeout(5000);
    page.on('pageerror', e => {if(errors.length<12) errors.push(e.message.slice(0,180));});
    page.on('console', m => {if(m.type()==='error' && errors.length<12) errors.push(m.text().slice(0,180));});
    const response = await page.goto('http://preview.local/' + req.page.split('/').map(encodeURIComponent).join('/'),
      {waitUntil:'load',timeout:10000});
    if (!response || !response.ok()) throw new Error('page not ready');
    await page.evaluate(async () => {await document.fonts.ready;});
    await page.waitForTimeout(100);
    const actionResults = [];
    for (const action of req.actions || []) {
      try {
        const locator = page.locator(action.selector);
        const options = {timeout:1000};
        if (action.op === 'click') await locator.click(options);
        else if (action.op === 'fill') await locator.fill(action.value,options);
        else if (action.op === 'select') await locator.selectOption(action.value,options);
        else if (action.op === 'scroll') await locator.scrollIntoViewIfNeeded(options);
        else if (action.op === 'check') await locator.check(options);
        else if (action.op === 'press') await locator.press(action.value,options);
        actionResults.push({op:action.op,ok:true});
      } catch (error) {
        actionResults.push({op:action.op,ok:false,error:error.message.slice(0,240)});
        break;
      }
    }
    const dom = await page.evaluate(() => ({title:document.title.slice(0,180),
      excerpt:(document.body?.innerText || '').slice(0,1500),
      activeElement:document.activeElement ? {tag:document.activeElement.tagName,id:document.activeElement.id.slice(0,80),
        type:(document.activeElement.getAttribute('type')||'').slice(0,80)} : null,
      width:innerWidth,documentWidth:document.documentElement.scrollWidth,
      horizontalOverflow:document.documentElement.scrollWidth>innerWidth,
      overflowingElements:Array.from(document.querySelectorAll('body *')).filter(e => {
        const r=e.getBoundingClientRect();return r.width>0 && (r.right>innerWidth+1 || r.left < -1);
      }).slice(0,10).map(e=>({tag:e.tagName,id:e.id.slice(0,80),class:e.className.toString().slice(0,80)}))}));
    // Output is a fresh random path selected exclusively by the broker.
    await page.screenshot({path:req.screenshot,animations:'disabled',fullPage:false,timeout:5000});
    console.log(JSON.stringify({screenshot:req.screenshot,page:req.page,viewport:req.viewport,height:900,
      ...dom,actionResults,errors,blockedRequests:blocked}));
    await context.close();
  }
} finally {await browser.close();}
