// Local browser check. No providers, bridge, or deployment calls.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createServer} from 'node:http';
import {mkdir, readFile, rm, writeFile} from 'node:fs/promises';
import {resolve, extname, sep} from 'node:path';
import {once} from 'node:events';
import {createRequire} from 'node:module';
const {parse} = createRequire(import.meta.url)('internal/deps/acorn/acorn/dist/acorn');
const fixtureMode = process.argv.includes('--fixture');

const project = resolve(import.meta.dirname, '../../..');
const output = import.meta.dirname;
const site = resolve(project, 'dist/site');
const profile = resolve(project, 'dist/sole-rules-check/browser-profile');
await mkdir(profile, {recursive:true});
const server = createServer(async (req, res) => {
  if(process.env.READER_DEBUG) console.log('HTTP', req.url);
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const path = pathname === '/' ? resolve(site, 'index.html')
    : pathname.startsWith('/docs/') ? resolve(site, `.${pathname}`)
    : resolve(project, `.${pathname}`);
  if (!path.startsWith(project + sep)) { res.writeHead(403).end(); return; }
  try {
    const data = await readFile(path);
    res.setHeader('Content-Type', ({'.html':'text/html', '.css':'text/css', '.js':'text/javascript'})[extname(path)] || 'application/octet-stream');
    res.end(data);
  } catch { res.writeHead(404).end('Missing generated file'); }
});
server.listen(0, '127.0.0.1');
await once(server, 'listening');
const origin = `http://127.0.0.1:${server.address().port}`;
const chrome = spawn('/usr/bin/google-chrome', ['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--no-proxy-server','--disable-extensions','--disable-background-networking','--disable-features=NetworkServiceSandbox','--single-process','--no-zygote','--no-first-run','--no-default-browser-check','--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'], {stdio:['ignore','ignore','pipe']});
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
  if (fixtureMode) {
    const modules = {};
    async function loadModule(path) {
      if (modules[path]) return;
      const source = await readFile(resolve(project, `.${path}`), 'utf8');
      const imports = parse(source, {ecmaVersion:'latest',sourceType:'module'}).body
        .filter(node => ['ImportDeclaration','ExportNamedDeclaration','ExportAllDeclaration'].includes(node.type) && node.source)
        .map(node => ({start:node.source.start,end:node.source.end,path:new URL(node.source.value, `${origin}${path}`).pathname}));
      modules[path] = {source, imports};
      for (const dependency of imports) await loadModule(dependency.path);
    }
    await loadModule('/web/app.js');
    const payloads = {};
    for (const file of ['factions','game-config','player-strategies','ui-copy','headlines','escalations','mandates','simulation-copy']) {
      payloads[`/dist/runtime/${file}.json`] = await readFile(resolve(project, `dist/runtime/${file}.json`),'utf8');
    }
    const css = await readFile(resolve(project,'web/styles.css'),'utf8');
    const html = (await readFile(resolve(site,'index.html'),'utf8'))
      .replace(/<script[^>]*src=["']\/web\/app.js["'][^>]*><\/script>/g,'')
      .replace('<link rel="stylesheet" href="/web/styles.css">', `<style>${css}</style>`);
    const {frameTree}=await send('Page.getFrameTree');
    await send('Page.setDocumentContent',{frameId:frameTree.frame.id,html});
    await evaluate(`(async () => {
      const modules=${JSON.stringify(modules)};
      const payloads=${JSON.stringify(payloads)};
      const origin=${JSON.stringify(origin)};
      // about:blank has no session storage; this fixture supplies an empty store.
      Object.defineProperty(window,'sessionStorage',{value:{getItem:()=>null,setItem:()=>{},removeItem:()=>{}}});
      // Supply the secure-context UUID API unavailable on this about:blank fixture.
      let fixtureId=0;
      crypto.randomUUID=()=> '00000000-0000-4000-8000-'+String(++fixtureId).padStart(12,'0');
      window.fetch=async input=>{
        const path=new URL(String(input), origin).pathname;
        if(!(path in payloads))throw new Error('Unexpected fixture request: '+path);
        return new Response(payloads[path],{status:200,headers:{'Content-Type':'application/json'}});
      };
      const urls={};
      function moduleUrl(path){
        if(urls[path])return urls[path];
        const entry=modules[path];
        let source=entry.source;
        for(const dependency of [...entry.imports].reverse())
          source=source.slice(0,dependency.start)+JSON.stringify(moduleUrl(dependency.path))+source.slice(dependency.end);
        source=source.replaceAll('import.meta.url',JSON.stringify(origin+path));
        return urls[path]=URL.createObjectURL(new Blob([source],{type:'text/javascript'}));
      }
      await import(moduleUrl('/web/app.js'));
    })()`);
  } else {
    await send('Page.navigate', {url:origin});
  }

  for (let i=0;i<50;i++) {
    if(await evaluate("document.querySelector('#faction')?.options.length === 6")) break;
    await delay(100);
  }
  assert.equal(await evaluate("document.querySelector('#faction')?.options.length"),6);
  await send('Page.bringToFront');
  for (const width of [1440,390]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
    const setup = await evaluate(`(() => ({
      width:innerWidth, title:document.title,
      rulesSelector:!!document.getElementById('play-profile'),
      text:document.body.innerText,
      factionOptions:document.querySelector('#faction').options.length
    }))()`);
    assert.equal(setup.rulesSelector,false);
    assert.doesNotMatch(setup.text,/Advanced Play|Default Game|Realignment|Volatility/);
    await evaluate("document.getElementById('start-game').click()");
    for (let i=0;i<100;i++) {
      if(await evaluate("document.querySelector('#decisions button') !== null"))break;
      await delay(50);
    }
    assert.equal(await evaluate("document.querySelector('#decisions button') !== null"),true, JSON.stringify(await evaluate("({status:document.getElementById('game-status').textContent,disabled:document.getElementById('start-game').disabled,body:document.getElementById('decisions').innerText})")));
    const beforeDecision=await evaluate("document.getElementById('decision-title').textContent");
    await evaluate("document.querySelector('#decisions button').focus()");
    assert.equal(await evaluate("document.activeElement.tagName"),'BUTTON');
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,text:'\r',unmodifiedText:'\r'});
    await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});
    for(let i=0;i<60;i++) {
      if(await evaluate("document.getElementById('decision-title').textContent")!==beforeDecision)break;
      await delay(50);
    }
    assert.notEqual(await evaluate("document.getElementById('decision-title').textContent"),beforeDecision,'Enter advances the pending decision');
    const capture=await send('Page.captureScreenshot',{format:'png'});
    await writeFile(resolve(output,`game-${width}.png`),Buffer.from(capture.data,'base64'));
    observations.push({width,factionOptions:setup.factionOptions,rulesSelector:setup.rulesSelector,keyboardAdvancedDecision:true,decisionButtons:await evaluate("document.querySelectorAll('#decisions button').length")});
  }
  assert.deepEqual(exceptions,[]);
  const version=await send('Browser.getVersion');
  await writeFile(resolve(output,'browser.json'),JSON.stringify({capturedAt:new Date().toISOString(),browser:version.product,mode:fixtureMode?'generated HTML and original browser modules over Blob URLs, with local JSON fixture responses':'local headless Chrome with normal HTTP navigation',navigationVerified:!fixtureMode,navigationLimitation:fixtureMode?'Normal Chrome loopback navigation stalled; HTTP delivery is not verified by this fixture':null,exceptions,observations},null,2)+'\n');
  console.log('browser: desktop and narrow setup, game start, keyboard action, and no retired mode passed; fixture='+fixtureMode);

} finally {
  socket?.close();
  chrome.kill('SIGTERM');
  await Promise.race([once(chrome,'exit'),delay(4000)]);
  if (chrome.exitCode === null && chrome.signalCode === null) chrome.kill('SIGKILL');
  server.closeAllConnections();
  await new Promise(r=>server.close(r));
  await rm(profile,{recursive:true,force:true});
}
