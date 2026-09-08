import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
// Supply the locally installed Playwright module and an already running local server.
const { chromium } = await import(process.env.MANDATE_PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.MANDATE_BROWSER_BASE || 'http://localhost:8139';
const output = resolve(process.env.MANDATE_BROWSER_OUTPUT || '/tmp/mandate-personal-browser-final');
await mkdir(output, { recursive:true });
const browser = await chromium.launch({channel:'chrome',headless:true});
const results=[];
try {
 for (const width of [1440,390]) {
  const page=await browser.newPage({viewport:{width,height:1000}});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto(`${base}/dist/site/gallery-baseline.html`);
  const projects=await page.locator('#projects article').count();assert.equal(projects,18);
  const tracks=await page.locator('.objective-track').count();assert.equal(tracks,6);
  for (const track of await page.locator('.objective-track').all()) {
   assert.deepEqual(await track.locator('span').allTextContents(),Array.from({length:100},(_,i)=>String(i)));
  }
  assert.equal(await page.locator('.recognition-track').count(),6);
  assert.equal(await page.locator('input[type=checkbox]').count(),0);
  await page.locator('#factions article').first().screenshot({path:resolve(output,`faction-${width}.png`)});
  await page.locator('#projects').screenshot({path:resolve(output,`projects-${width}.png`)});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  assert.equal(overflow,false);
  await page.goto(base);await page.locator('#start-game').click();await page.locator('.public-player').first().waitFor();
  assert.equal(await page.locator('.public-player').count(),4);
  assert.match(await page.locator('.public-player').first().innerText(),/Highest Trust milestone|Trust milestone/i);
  await page.screenshot({path:resolve(output,`game-${width}.png`),fullPage:true});
  assert.deepEqual(errors,[]);results.push({width,projects,tracks,objectiveSpaces:600,gamePlayers:4,overflow,errors});await page.close();
 }
 await writeFile(resolve(output,'report.json'),JSON.stringify({browser:browser.version(),base,results},null,2)+'\n');
 console.log(JSON.stringify(results));
} finally {await browser.close();}
