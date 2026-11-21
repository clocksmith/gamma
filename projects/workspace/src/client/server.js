// Loopback human-control surface. Browser pipe credentials never cross this API.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { randomBytes, timingSafeEqual } from 'node:crypto';

const ASSETS = new Map([['/', ['index.html', 'text/html']], ['/app.js', ['app.js', 'text/javascript']], ['/style.css', ['style.css', 'text/css']]]);
const equal = (a, b) => typeof a === 'string' && a.length === b.length && timingSafeEqual(Buffer.from(a), Buffer.from(b));
async function body(req, maximum) {
  const chunks = []; let size = 0;
  for await (const chunk of req) {
    size += chunk.length; if (size > maximum) throw Error('Request exceeds the configured byte limit'); chunks.push(chunk);
  }
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}
export async function startWorkspaceServer({ controller, config, port = config.port, nativePicker = null }) {
  const bootstrap = randomBytes(32).toString('base64url'), sessions = new Set();
  let origin;
  const nativeOperations = new Set();
  const server = createServer(async (req, res) => {
    const send = (status, value) => { res.writeHead(status, { 'content-type': 'application/json' }); res.end(JSON.stringify(value)); };
    res.setHeader('cache-control', 'no-store'); res.setHeader('referrer-policy', 'no-referrer');
    res.setHeader('x-content-type-options', 'nosniff');
    res.setHeader('content-security-policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");
    try {
      if (req.headers.host !== new URL(origin).host) return send(403, { error: 'Unexpected host' });
      const url = new URL(req.url, origin);
      if (req.method === 'GET' && ASSETS.has(url.pathname)) {
        const [file, type] = ASSETS.get(url.pathname);
        const bytes = await readFile(new URL(`../../ui/${file}`, import.meta.url));
        res.writeHead(200, { 'content-type': `${type}; charset=utf-8` }); res.end(bytes); return;
      }
      if (req.method === 'POST' && req.headers.origin !== origin) return send(403, { error: 'Same-origin requests are required' });
      if (req.method === 'POST' && url.pathname === '/api/session') {
        const value = await body(req, config.maxBodyBytes);
        if (!equal(value.token, bootstrap)) return send(401, { error: 'Open the login link printed by the local service' });
        const session = randomBytes(32).toString('base64url'); sessions.add(session);
        res.setHeader('set-cookie', `blitzen_session=${session}; HttpOnly; SameSite=Strict; Path=/`);
        return send(200, { ready: true });
      }
      const session = req.headers.cookie?.split(';').map(value => value.trim()).find(value => value.startsWith('blitzen_session='))?.slice('blitzen_session='.length);
      if (!sessions.has(session)) return send(401, { error: 'Open the login link printed by the local service' });
      if (nativePicker && req.method === 'POST' && url.pathname === '/api/native-document') {
        const input = await body(req, config.maxBodyBytes);
        if (!input || Array.isArray(input) || typeof input !== 'object' || Object.keys(input).length) {
          return send(400, { error: 'Document selection takes no input' });
        }
        const operation = new AbortController();
        nativeOperations.add(operation);
        const abort = () => operation.abort();
        res.once('close', abort);
        try { return send(200, await nativePicker({ signal: operation.signal })); }
        finally { res.removeListener('close', abort); nativeOperations.delete(operation); }
      }
      if (req.method === 'GET' && url.pathname === '/api/status') {
        return send(200, { ...await controller.status(url.searchParams.get('project')), ...(nativePicker ? { nativeDocumentPicker: true } : {}) });
      }
      if (req.method !== 'POST' || url.pathname !== '/api/command') return send(404, { error: 'Unknown workspace route' });
      const { operation, projectId, input = {} } = await body(req, config.maxBodyBytes);
      const operations = {
        create: () => controller.create(input), navigate: () => controller.navigate(projectId, input),
        openPage: () => controller.service.openPage(controller.admin(projectId)),
        focusPage: () => controller.service.focusPage({ ...controller.admin(projectId), pageId: input.pageId }),
        selectRegion: () => controller.service.selectRegion({ ...controller.admin(projectId), pageId: input.pageId }),
        capture: () => controller.capture(projectId, input), record: () => controller.record(projectId, input),
        repositoryRead: () => controller.readRepository(projectId, input),
        checkSources: () => controller.checkSources(projectId, input),
        runWorkflow: async () => {
          const { runId, done } = await controller.runPersonalWorkflow(projectId, input);
          done.catch(() => {});
          return { runId };
        },
        delegate: () => controller.delegate(projectId, input), takeOver: () => controller.takeOver(projectId),
        note: () => controller.humanNote(projectId, input.text), handoff: () => controller.handoff(projectId, input),
        revoke: () => controller.revoke(projectId, input), check: () => controller.check(projectId, input),
        decide: async () => {
          await controller.check(projectId, input);
          const action = await controller.service.action({ ...controller.owner(projectId), actionId: input.actionId });
          if (action.isUncertain && action.reconciliation?.result !== 'human-review-requested') {
            await controller.service.reconcile({ ...controller.owner(projectId), actionId: input.actionId, method: 'human-review' });
          }
          return controller.service.decideHumanReview({ ...controller.admin(projectId), actionId: input.actionId, decision: input.decision, note: input.note });
        }
      };
      if (!Object.hasOwn(operations, operation)) return send(400, { error: 'Unknown workspace command' });
      send(200, await operations[operation]());
    } catch (error) { send(400, { error: error.message, code: error.code ?? null }); }
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(port, config.host, resolve); });
  origin = `http://${config.host}:${server.address().port}`;
  return { origin, loginUrl: `${origin}/#${bootstrap}`, server,
    close: () => new Promise((resolve, reject) => { for (const operation of nativeOperations) operation.abort(); server.close(error => error ? reject(error) : resolve()); server.closeIdleConnections(); }) };
}
