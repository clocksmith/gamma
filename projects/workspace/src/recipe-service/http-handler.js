// Web-standard HTTP handler for Fawn Managed Recipe Service (Cloudflare Workers & Cloud Run).
import { createHash, timingSafeEqual } from 'node:crypto';

const HASH_RE = /^[a-f0-9]{64}$/;
const DEFAULT_MAX_BODY_BYTES = 1024 * 1024;

function sha256Bytes(value) {
  return createHash('sha256').update(value).digest();
}

function jsonResponse(status, payload) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff',
    },
  });
}

function authenticateBearer(request, principals) {
  const header = request.headers.get('authorization') ?? '';
  const match = /^Bearer ([^\s]{32,256})$/.exec(header);
  if (!match) return null;
  const candidateHash = sha256Bytes(match[1]);
  for (const principal of principals) {
    const expected = Buffer.from(principal.tokenHash, 'hex');
    if (expected.length === candidateHash.length && timingSafeEqual(candidateHash, expected)) {
      return principal;
    }
  }
  return null;
}

async function readBoundedJson(request, maxBodyBytes) {
  const contentType = request.headers.get('content-type') ?? '';
  if (!contentType.toLowerCase().includes('application/json')) {
    throw Object.assign(Error('application/json content-type required'), { status: 415, code: 'json-required' });
  }
  const reader = request.body?.getReader();
  if (!reader) {
    throw Object.assign(Error('Request body required'), { status: 400, code: 'empty-body' });
  }
  const chunks = [];
  let total = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > maxBodyBytes) {
      await reader.cancel();
      throw Object.assign(Error('Request exceeds maximum byte budget'), { status: 413, code: 'request-too-large' });
    }
    chunks.push(value);
  }
  const merged = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    merged.set(chunk, offset);
    offset += chunk.byteLength;
  }
  try {
    return JSON.parse(new TextDecoder().decode(merged));
  } catch {
    throw Object.assign(Error('Invalid JSON payload'), { status: 400, code: 'invalid-json' });
  }
}

export function normalizePrincipals(clients) {
  if (!Array.isArray(clients) || !clients.length) {
    throw Error('At least one authenticated client credential is required');
  }
  return clients.map(client => {
    if (!client || typeof client.clientId !== 'string' || !client.clientId.trim()
      || typeof client.workspaceId !== 'string' || !client.workspaceId.trim()
      || !HASH_RE.test(client.tokenHash)
      || (client.role !== undefined && client.role !== 'member' && client.role !== 'publisher')) {
      throw Error('Each client requires clientId, workspaceId, 64-hex tokenHash and optional role (member|publisher)');
    }
    return Object.freeze({
      clientId: client.clientId,
      workspaceId: client.workspaceId,
      tokenHash: client.tokenHash,
      role: client.role ?? 'member',
    });
  });
}

export function createManagedRecipeHttpHandler({
  engine,
  clients,
  maxBodyBytes = DEFAULT_MAX_BODY_BYTES,
}) {
  if (!engine) throw Error('Managed recipe engine is required');
  const principals = normalizePrincipals(clients);

  return async function handleRequest(request) {
    try {
      if (request.headers.get('origin')) {
        return jsonResponse(403, { error: 'browser-origin-denied' });
      }
      const principal = authenticateBearer(request, principals);
      if (!principal) {
        return jsonResponse(401, { error: 'unauthorized' });
      }

      const url = new URL(request.url);
      const { pathname, searchParams } = url;

      if (request.method === 'GET' && pathname === '/health') {
        return jsonResponse(200, {
          ready: true,
          service: 'fawn-managed-recipes',
          dagVersion: 3,
        });
      }

      if (request.method === 'POST' && pathname === '/v1/subrecipes') {
        const body = await readBoundedJson(request, maxBodyBytes);
        return jsonResponse(200, await engine.registerSubrecipe(principal, body));
      }

      if (request.method === 'GET' && pathname === '/v1/subrecipes') {
        const scope = searchParams.get('scope') ?? 'workspace';
        const origin = searchParams.get('origin') ?? '';
        return jsonResponse(200, await engine.listSubrecipes(principal, { scope, origin }));
      }

      if (request.method === 'POST' && pathname === '/v1/traces') {
        const body = await readBoundedJson(request, maxBodyBytes);
        return jsonResponse(200, await engine.ingestTrace(principal, body));
      }

      if (request.method === 'POST' && pathname === '/v1/recipes/compose') {
        const body = await readBoundedJson(request, maxBodyBytes);
        return jsonResponse(200, await engine.composeRecipe(principal, body));
      }

      if (request.method === 'POST' && pathname === '/v1/recipes/resolve') {
        const body = await readBoundedJson(request, maxBodyBytes);
        return jsonResponse(200, await engine.resolveRecipe(principal, body));
      }

      return jsonResponse(404, { error: 'not-found' });
    } catch (error) {
      const status = Number.isSafeInteger(error.status) ? error.status : 500;
      const code = error.code ?? 'internal-error';
      const message = status < 500 ? error.message : 'Internal recipe service error';
      return jsonResponse(status, { error: code, message });
    }
  };
}
