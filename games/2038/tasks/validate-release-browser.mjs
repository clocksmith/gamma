import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { extname, isAbsolute, relative, resolve } from "node:path";
import { tmpdir } from "node:os";
import { loadGameIdentity, projectRoot } from "../lab/versioning/game-identity.js";

const args = process.argv.slice(2);
const argument = (name) => {
  const index = args.indexOf(name);
  if (index === -1) return undefined;
  if (!args[index + 1] || args[index + 1].startsWith("--")) {
    throw new Error(`${name} requires a value.`);
  }
  return args[index + 1];
};
for (let index = 0; index < args.length; index += 2) {
  assert.ok(["--output", "--origin"].includes(args[index]), `Unknown argument: ${args[index]}`);
}
const outputArgument = argument("--output");
assert.ok(outputArgument, "Use --output with a directory outside the source worktree.");
const output = resolve(outputArgument);
const deployedOrigin = argument("--origin");
const within = (root, target) => {
  const path = relative(root, target);
  return path === "" || (!path.startsWith("..") && !isAbsolute(path));
};
assert.ok(!within(projectRoot, output), "Write validation outputs outside the project until validation completes.");
await mkdir(output, { recursive: true });
const identity = await loadGameIdentity();
assert.equal(identity.provenance.sourceDirty, false, "Browser receipts require a clean source commit.");
const report = {
  schemaVersion: 1,
  evidenceType: "browser-walkthrough-and-browser-engine-regressions",
  startedAt: new Date().toISOString(),
  identity,
  limits: [
    "The boundary suite runs the actual regression tests and shipped engine modules in Chrome using browser adapters for Node test/assert/file loading.",
    "Desktop/mobile UI checks use the shipped UI; the boundary fixtures are not four end-to-end UI setup sequences.",
    "This is not a human playtest, a balance claim, or physical-kit qualification."
  ],
  requests: [],
  browserErrors: [],
  ui: []
};
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");

// Only the test harness is adapted. Public runtime modules are served byte-for-byte.
const browserAssert = `
const fail = (message) => { throw new Error(message || 'Assertion failed'); };
function equalValue(a,b) {
  if (Object.is(a,b)) return true;
  if (!a || !b || typeof a !== 'object' || typeof b !== 'object') return false;
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  if (a instanceof Date || b instanceof Date) return a instanceof Date && b instanceof Date && +a === +b;
  const ka=Reflect.ownKeys(a), kb=Reflect.ownKeys(b);
  return ka.length===kb.length && ka.every(k=>Object.hasOwn(b,k)&&equalValue(a[k],b[k]));
}
function assert(value,message) { if (!value) fail(message); }
export const ok=assert;
export const equal=(a,b,m)=>{if(!Object.is(a,b))fail(m||JSON.stringify({actual:a,expected:b}));};
export const strictEqual=equal;
export const notEqual=(a,b,m)=>{if(Object.is(a,b))fail(m||'Values unexpectedly equal');};
export const notStrictEqual=notEqual;
export const deepEqual=(a,b,m)=>{if(!equalValue(a,b))fail(m||JSON.stringify({actual:a,expected:b}));};
export const deepStrictEqual=deepEqual;
export const notDeepEqual=(a,b,m)=>{if(equalValue(a,b))fail(m||'Values unexpectedly deeply equal');};
export const notDeepStrictEqual=notDeepEqual;
export const match=(value,regexp,message)=>{if(!regexp.test(value))fail(message||String(value)+' does not match '+regexp);};
export const doesNotMatch=(value,regexp,message)=>{if(regexp.test(value))fail(message||'Unexpected match');};
function checkError(error,expected) {
  if (!expected) return;
  if (expected instanceof RegExp) return match(String(error),expected);
  if (typeof expected==='function') return assert(error instanceof expected || expected(error)===true);
  for(const [key,value] of Object.entries(expected)) {
    if(value instanceof RegExp)match(String(error[key]),value);else deepEqual(error[key],value);
  }
}
export const throws=(fn,expected)=>{let error;try{fn();}catch(e){error=e;}assert(error,'Expected an exception');checkError(error,expected);};
export const rejects=async(fn,expected)=>{let error;try{await(typeof fn==='function'?fn():fn);}catch(e){error=e;}assert(error,'Expected rejection');checkError(error,expected);};
export const doesNotThrow=(fn)=>fn();
export const doesNotReject=async(fn)=>await(typeof fn==='function'?fn():fn);
Object.assign(assert,{ok,equal,strictEqual,notEqual,notStrictEqual,deepEqual,deepStrictEqual,notDeepEqual,notDeepStrictEqual,match,doesNotMatch,throws,rejects,doesNotThrow,doesNotReject,fail});
export {fail}; export default assert;
`;
const browserTest = `
export const cases=[];
export function test(name,options,fn) {
  if(typeof options==='function')fn=options;
  else if(options?.skip||options?.todo)throw new Error('Skipped browser evidence is not permitted');
  if(typeof fn!=='function')throw new Error('Missing test callback: '+name);
  cases.push({name,fn});
}
export default test;
`;
const browserFs = `
export async function readFile(path,encoding) {
  const response=await fetch(String(path));
  if(!response.ok)throw new Error('readFile '+path+': HTTP '+response.status);
  if(encoding==='utf8'||encoding==='utf-8'||encoding?.encoding)return response.text();
  const bytes=new Uint8Array(await response.arrayBuffer());
  bytes.toString=()=>new TextDecoder().decode(bytes);
  return bytes;
}
`;
const browserPath = `
export const resolve=(...parts)=>new URL(parts.filter(Boolean).join('/'),'http://browser/').pathname;
export const join=(...parts)=>parts.filter(Boolean).join('/').replaceAll(/\\/+/g,'/');
export const dirname=(path)=>path.slice(0,path.lastIndexOf('/'))||'/';
`;
const adapters = new Map([
  ["/__browser/node/assert/strict", browserAssert],
  ["/__browser/node/assert", browserAssert],
  ["/__browser/node/test", browserTest],
  ["/__browser/node/fs/promises", browserFs],
  ["/__browser/node/path", browserPath],
  ["/__browser/node/url", "export const fileURLToPath=(url)=>new URL(url).pathname;"]
]);
const runnerHtml = `<!doctype html><html><head><meta charset="utf-8"><title>Mandate release boundary checks</title></head><body><h1>Release boundary checks</h1><ol id="results"></ol><script type="module">
try {
  const {cases}=await import('/__browser/node/test');
  await import('/tests/rule-boundaries.test.mjs');
  const results=[];
  for(const entry of cases) {
    const result={name:entry.name};
    try { await entry.fn(); result.status='passed'; }
    catch(error) {result.status='failed';result.error=error.stack||String(error);}
    results.push(result);
    const item=document.createElement('li');item.textContent=result.status+': '+entry.name;document.querySelector('#results').append(item);
  }
  window.__mandateBoundaryResults=results;
} catch(error) {window.__mandateBoundaryResults=[{name:'suite loading',status:'failed',error:error.stack||String(error)}];}
</script></body></html>`;
const supplemental = new Set([
  "/tests/rule-boundaries.test.mjs",
  "/tasks/content/era-unlocks.mjs"
]);
let server;
let chrome;
let socket;
let profile;
let base;
const served = new Map();
try {
  if (deployedOrigin) {
    base = new URL(deployedOrigin).origin;
    const response = await fetch(`${base}/release-identity.json?release=${identity.game.version}`);
    assert.equal(response.status, 200, "Live release identity must be retrievable.");
    report.deployedIdentity = await response.json();
    assert.equal(report.deployedIdentity.executableVersion, identity.game.version);
    assert.equal(report.deployedIdentity.sourceCommit, identity.provenance.sourceCommit);
    assert.equal(report.deployedIdentity.sourceDirty, false);
    assert.equal(report.deployedIdentity.rulesetFingerprint, identity.game.rulesetFingerprint);
  } else {
    const publicRoot = resolve(projectRoot, "dist/firebase/public");
    server = createServer(async (request, response) => {
      try {
        const pathname = decodeURIComponent(new URL(request.url, "http://localhost").pathname);
        if (pathname === "/favicon.ico") return response.writeHead(204).end();
        if (pathname === "/__browser/runner.html") {
          response.setHeader("Content-Type", "text/html");
          return response.end(runnerHtml);
        }
        if (adapters.has(pathname)) {
          response.setHeader("Content-Type", "text/javascript");
          return response.end(adapters.get(pathname));
        }
        const isSource = supplemental.has(pathname) || pathname.startsWith("/components/");
        const root = isSource ? projectRoot : publicRoot;
        const path = resolve(root, `.${pathname === "/" ? "/index.html" : pathname}`);
        assert.ok(within(root, path), "Request outside serving root.");
        const original = await readFile(path);
        let bytes = original;
        if (pathname === "/tests/rule-boundaries.test.mjs") {
          bytes = Buffer.from(original.toString("utf8")
            .replace(/(["'])node:([^"']+)\1/g, '"/__browser/node/$2"')
            .replaceAll("import.meta.dirname", 'new URL(".", import.meta.url).pathname'));
        }
        served.set(pathname, {
          path: relative(projectRoot, path), bytes: bytes.length,
          servedSha256: hash(bytes), sourceSha256: hash(original),
          adaptedForBrowser: !bytes.equals(original)
        });
        response.setHeader("Content-Type", ({
          ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json",
          ".html": "text/html", ".css": "text/css", ".svg": "image/svg+xml", ".png": "image/png"
        })[extname(path)] || "application/octet-stream");
        response.end(bytes);
      } catch (error) {
        response.writeHead(404, { "Content-Type": "text/plain" }).end(String(error));
      }
    });
    await new Promise((resolveListen, reject) => {
      server.once("error", reject);
      server.listen(0, "127.0.0.1", resolveListen);
    });
    base = `http://127.0.0.1:${server.address().port}`;
  }
  report.origin = base;
  profile = await mkdtemp(resolve(tmpdir(), "mandate-release-chrome-"));
  const executable = process.env.CHROME_BIN || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  chrome = spawn(executable, [
    "--headless=new", "--no-first-run", "--no-default-browser-check",
    "--disable-background-networking", "--disable-component-update", "--disable-sync",
    "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank"
  ], { stdio: ["ignore", "ignore", "pipe"] });
  let launchError;
  let chromeStderr = "";
  chrome.on("error", (error) => { launchError = error; });
  chrome.stderr.on("data", (chunk) => { chromeStderr += chunk; });
  let port;
  for (let attempt = 0; attempt < 150; attempt += 1) {
    if (launchError) throw launchError;
    try { port = (await readFile(resolve(profile, "DevToolsActivePort"), "utf8")).split("\n")[0]; break; }
    catch (error) { if (error.code !== "ENOENT") throw error; }
    await new Promise((wait) => setTimeout(wait, 100));
  }
  assert.ok(port, `Chrome did not expose a debugging endpoint: ${chromeStderr}`);
  report.browser = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
  delete report.browser.webSocketDebuggerUrl;
  const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: "PUT" })).json();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((opened, reject) => { socket.onopen = opened; socket.onerror = reject; });
  let nextId = 0;
  const pending = new Map();
  socket.onmessage = ({ data }) => {
    const message = JSON.parse(data);
    if (message.id) {
      const entry = pending.get(message.id);
      if (!entry) return;
      pending.delete(message.id);
      clearTimeout(entry.timer);
      if (message.error) entry.reject(new Error(message.error.message));
      else entry.resolve(message.result);
    } else if (message.method === "Network.responseReceived") {
      const { url, status, mimeType } = message.params.response;
      if (url.startsWith(base)) report.requests.push({ url, status, mimeType });
    } else if (message.method === "Runtime.exceptionThrown") {
      report.browserErrors.push(message.params.exceptionDetails);
    }
  };
  const send = (method, params = {}) => new Promise((resolveSend, reject) => {
    const id = ++nextId;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 120000);
    pending.set(id, { resolve: resolveSend, reject, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
  const evaluate = async (expression) => {
    const value = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (value.exceptionDetails) throw new Error(JSON.stringify(value.exceptionDetails));
    return value.result.value;
  };
  const waitFor = (condition) => evaluate(`new Promise((resolve,reject)=>{const began=Date.now();const poll=()=>{try{const value=(${condition});if(value)return resolve(value);}catch(error){return reject(error);}if(Date.now()-began>30000)return reject(new Error('Browser condition timed out: '+${JSON.stringify(condition)}));setTimeout(poll,100);};poll();})`);
  const screenshot = async (name) => {
    const result = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
    await writeFile(resolve(output, name), Buffer.from(result.data, "base64"));
  };
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Network.enable");
  await send("Network.setCacheDisabled", { cacheDisabled: true });
  if (!deployedOrigin) {
    await send("Page.navigate", { url: `${base}/__browser/runner.html` });
    report.boundaries = await waitFor("window.__mandateBoundaryResults");
    await screenshot("boundary-regressions.png");
    assert.equal(report.boundaries.length, 11, "All eleven boundary regressions must load.");
    assert.ok(report.boundaries.every((entry) => entry.status === "passed"), JSON.stringify(report.boundaries));
    process.stdout.write(`browser: ${report.boundaries.length} boundary regressions passed\n`);
  }
  for (const viewport of [
    { name: "desktop", width: 1440, height: 1000, mobile: false },
    { name: "mobile", width: 390, height: 844, mobile: true }
  ]) {
    await send("Emulation.setDeviceMetricsOverride", { width: viewport.width, height: viewport.height, deviceScaleFactor: 1, mobile: viewport.mobile });
    await send("Page.navigate", { url: `${base}/web/index.html` });
    await waitFor("document.querySelector('#faction')?.options.length === 6 && document.querySelector('#start-game') && !document.querySelector('#start-game').disabled");
    const setup = await evaluate(`(()=>{const players=document.querySelector('#player-count');players.value='4';players.dispatchEvent(new Event('change',{bubbles:true}));return {factionCount:document.querySelector('#faction').options.length,playerCount:players.value,versionVisible:document.body.innerText.includes(${JSON.stringify(identity.game.version)})};})()`);
    assert.equal(setup.versionVisible, true, "The UI must show the sealed executable version.");
    await evaluate("document.querySelector('#start-game').click()");
    await waitFor("document.querySelectorAll('.decision-card').length === 6");
    const actions = await evaluate("[...document.querySelectorAll('.decision-card')].map(node=>node.innerText)");
    assert.ok(["Fund", "Research", "Build", "Organize", "Deploy", "Influence"].every((name) => actions.some((text) => text.includes(name))));
    await screenshot(`${viewport.name}-action-selection.png`);
    await evaluate("[...document.querySelectorAll('.decision-card')].find(node=>node.innerText.includes('Select Deploy')).click()");
    await waitFor("document.querySelectorAll('.decision-card').length > 0 && ![...document.querySelectorAll('.decision-card')].some(node=>node.innerText.includes('Select Fund'))");
    const speculativeSelection = await evaluate("({choices:[...document.querySelectorAll('.decision-card')].map(node=>({text:node.innerText,disabled:node.disabled})),body:document.body.innerText,exportEnabled:!document.querySelector('#export').disabled,viewportWidth:innerWidth,documentWidth:document.documentElement.scrollWidth})");
    assert.equal(speculativeSelection.exportEnabled, true);
    assert.ok(speculativeSelection.choices.some((choice) => !choice.disabled), "Speculative Deploy must leave an actionable browser decision.");
    await screenshot(`${viewport.name}-speculative-deploy.png`);
    report.ui.push({ viewport, setup, actions, speculativeSelection });
    process.stdout.write(`browser: ${viewport.name} setup, six actions, and speculative Deploy passed\n`);
  }
  assert.equal(report.requests.filter((entry) => entry.status >= 400).length, 0, "All requested game and harness resources must load.");
  assert.equal(report.browserErrors.length, 0, "No uncaught browser exceptions are permitted.");
  report.status = "passed";
} catch (error) {
  report.status = "failed";
  report.error = error.stack || String(error);
  process.exitCode = 1;
} finally {
  report.completedAt = new Date().toISOString();
  report.servedFiles = Object.fromEntries(served);
  await writeFile(resolve(output, "browser-receipt.json"), `${JSON.stringify(report, null, 2)}\n`);
  if (socket) socket.close();
  if (chrome) chrome.kill("SIGTERM");
  if (server) { server.closeAllConnections(); await new Promise((closed) => server.close(closed)); }
  if (profile) {
    await new Promise((wait) => setTimeout(wait, 400));
    await rm(profile, { recursive: true, force: true, maxRetries: 4, retryDelay: 200 });
  }
  process.stdout.write(`browser: ${report.status}; receipt ${resolve(output, "browser-receipt.json")}\n`);
  if (report.error) process.stderr.write(`${report.error}\n`);
}
