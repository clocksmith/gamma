// Local generated-document check. No game server, provider, or deployment calls.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createServer} from 'node:http';
import {mkdir, readFile, rm, writeFile} from 'node:fs/promises';
import {resolve, extname, sep} from 'node:path';
import {once} from 'node:events';

const project = resolve(import.meta.dirname, '../../..');
const output = import.meta.dirname;
const site = resolve(project, 'dist/site');
const profile = resolve(project, 'dist/authoring-reader-chrome');
await mkdir(profile, {recursive:true});
const server = createServer(async (req, res) => {
  if(process.env.READER_DEBUG) console.log('HTTP', req.url);
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const path = resolve(site, `.${pathname.endsWith('/') ? `${pathname}index.html` : pathname}`);
  if (!path.startsWith(site + sep)) { res.writeHead(403).end(); return; }
  try {
    const data = await readFile(path);
    res.setHeader('Content-Type', ({'.html':'text/html', '.css':'text/css', '.js':'text/javascript'})[extname(path)] || 'application/octet-stream');
    res.end(data);
  } catch { res.writeHead(404).end('Missing generated file'); }
});
server.listen(0, '127.0.0.1');
await once(server, 'listening');
const origin = `http://127.0.0.1:${server.address().port}`;
const chrome = spawn('/usr/bin/google-chrome', ['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--no-proxy-server','--disable-extensions','--disable-background-networking','--disable-features=NetworkServiceSandbox','--no-zygote','--no-first-run','--no-default-browser-check','--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'], {stdio:['ignore','ignore','pipe']});
chrome.stderr.on('data', data => {if(process.env.READER_DEBUG) process.stderr.write(data);});
let socket;
const pending = new Map();
const exceptions = [];
const observations = [];
const delay = ms => new Promise(r => setTimeout(r, ms));
let sequence = 0;
function send(method, params = {}) {
  const id = ++sequence;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {pending.delete(id); reject(new Error(`CDP timeout: ${method}`));}, 15000);
    pending.set(id, {resolve, reject, timer});
    socket.send(JSON.stringify({id, method, params}));
  });
}
async function evaluate(expression) {
  const reply = await send('Runtime.evaluate', {expression, returnByValue:true, awaitPromise:true});
  if (reply.exceptionDetails) throw new Error(JSON.stringify(reply.exceptionDetails));
  return reply.result.value;
}
try {
  let port;
  for (let n=0; n<150; n++) {
    try {port = (await readFile(resolve(profile,'DevToolsActivePort'),'utf8')).split('\n')[0]; break;} catch {await delay(100);}
  }
  assert.ok(port, 'Chrome exposes a debugging port');
  const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`,{method:'PUT'})).json();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await once(socket, 'open');
  socket.addEventListener('message', event => {
    const data = JSON.parse(event.data);
    if(process.env.READER_DEBUG) console.log('CDP', data.id || data.method, data.error || (data.method?.startsWith('Network.') ? JSON.stringify(data.params) : ''));
    if (data.method === 'Runtime.exceptionThrown') exceptions.push(data.params);
    if (!data.id) return;
    const call = pending.get(data.id);
    if (!call) return;
    clearTimeout(call.timer); pending.delete(data.id);
    data.error ? call.reject(new Error(JSON.stringify(data.error))) : call.resolve(data.result);
  });
  console.log('Chrome version', (await send('Browser.getVersion')).product);
  await send('Network.enable');
  await send('Page.enable');
  await send('Runtime.enable');
  for (const width of [1440, 390]) {
    await send('Emulation.setDeviceMetricsOverride', {width, height:900, deviceScaleFactor:1, mobile:false});
    for (const slug of ['index','core-rules','map-reference','component-reference','component-inventory','card-reference','design-decisions']) {
      const url = `${origin}/docs/${slug}.html`;
      console.log(`reader-browser: ${slug} at ${width}px; HTTP ${(await fetch(url)).status}`);
      const html = await (await fetch(url)).text();
      const {frameTree} = await send('Page.getFrameTree');
      // An explicit base supplies the generated reader URL for link checks.
      // This fixture avoids the environment's stalled Chrome network navigation.
      await send('Page.setDocumentContent', {frameId:frameTree.frame.id,
        html:html.replace('<head>', `<head><base href="${url}">`)});
      const page = await evaluate(`(() => {
        const main = document.querySelector('main');
        const text = main?.innerText || '';
        const links = [...document.querySelectorAll('a[href]')].map(a=>a.href).filter(h=>new URL(h).pathname.startsWith('/docs/'));
        const headings = [...main.querySelectorAll('h1,h2,h3,h4')].map(h=>({level:h.tagName,text:h.innerText,id:h.id}));
        const missingAnchors = [...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(decodeURIComponent(a.hash.slice(1)))).map(a=>a.hash);
        return {title:document.title, width:innerWidth, documentWidth:document.documentElement.scrollWidth,
          hasUnresolvedReference:text.includes('$'+'{'), hasMarker:text.includes('<!--'),
          headings, missingAnchors, links, textLength:text.length};
      })()`);
      assert.ok(page.textLength > 200, `reader content ${slug}`);
      assert.equal(page.hasUnresolvedReference, false, `${slug} resolved references`);
      assert.equal(page.hasMarker, false, `${slug} hides author markers`);
      assert.deepEqual(page.missingAnchors, [], `${slug} ToC anchors resolve`);
      assert.ok(page.documentWidth <= width + 1, `${slug} fits ${width}px: ${page.documentWidth}`);
      for (const link of new Set(page.links)) {
        const response = await fetch(link);
        assert.equal(response.status, 200, `linked reader ${new URL(link).pathname}`);
      }
      observations.push({slug, ...page, links:[...new Set(page.links)].map(link=>new URL(link).pathname)});
      if (slug === 'map-reference') {
        await evaluate("document.getElementById('district-effects').scrollIntoView()");
        const capture = await send('Page.captureScreenshot', {format:'png'});
        await writeFile(resolve(output, `map-${width}.png`), Buffer.from(capture.data,'base64'));
      }
      if (slug === 'core-rules') {
        await evaluate("document.querySelector('main a[href=\"/docs/map-reference.html\"]').focus()");
        assert.equal(await evaluate("document.activeElement.getAttribute('href')"), '/docs/map-reference.html');

      }
    }
  }
  assert.deepEqual(exceptions, [], 'no browser runtime exceptions');
  const version = await send('Browser.getVersion');
  await writeFile(resolve(output,'browser.json'), JSON.stringify({capturedAt:new Date().toISOString(),browser:version.product,mode:'local headless Chrome; Page.setDocumentContent with generated HTML and a fixture base URL',viewportWidths:[1440,390],crossReferenceFocus:true,navigationVerified:false,navigationLimitation:'Direct Chrome loopback navigation stalled before a response; local HTTP links were checked independently with fetch',exceptions,observations},null,2)+'\n');
  console.log(`reader-browser: passed ${observations.length} page/viewport checks, local HTTP links and cross-reference focus; ${version.product}`);
} finally {
  socket?.close();
  chrome.kill('SIGTERM');
  await Promise.race([once(chrome,'exit'),delay(4000)]);
  if (chrome.exitCode === null && chrome.signalCode === null) chrome.kill('SIGKILL');
  server.closeAllConnections();
  await new Promise(r=>server.close(r));
  await rm(profile,{recursive:true,force:true});
}
