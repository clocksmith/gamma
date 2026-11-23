#!/usr/bin/env node
// The only way an arm session reaches the application (clocksmith/deco#88,
// same-model three-arm test), and the audit that proves a session stayed inside it.
//
// An arm session runs with no shell and no web tool. Its file tools are confined
// to an empty working directory by the model CLI. This file is the one remaining
// door: an MCP server with a single tool that forwards API v3 calls to the one
// instance under test, as one of the two test accounts, and writes every call,
// allowed or refused, to a log the session cannot reach.
//
//   discovery mode  app_request { as, method, path, body }   bounded calls and records
//   decision mode   app_get { path }                         GET only, as the approver, a few reads
//
// Started by the model CLI through --mcp-config; configured by GAMMATRON_ARM_SURFACE (JSON).
import { appendFileSync } from 'node:fs';
import { isAbsolute, relative, resolve } from 'node:path';
import readline from 'node:readline';
import { fileURLToPath } from 'node:url';
import { openProjectRequester, readState } from './provision.mjs';

export const DEFAULT_LIMITS = Object.freeze({
  discovery: Object.freeze({ requests: 400, recordsCreated: 60 }),
  decision: Object.freeze({ reads: 8 }),
  pathChars: 512,
  bodyBytes: 8192,
  responseChars: 60000,
});
const DISCOVERY_METHODS = new Set(['GET', 'POST', 'PATCH', 'DELETE']);
const ACCOUNTS = new Set(['author', 'approver']);
const CREATES_RECORD = /^\/api\/v3\/(?:projects\/[^/]+\/)?work_packages\/?(?:\?.*)?$/;

/** Returns the reason a path is refused, or null when it stays inside API v3 of the one instance. */
export function refusePath(path, limit = DEFAULT_LIMITS.pathChars) {
  if (typeof path !== 'string' || !path) return 'path must be a string';
  if (path.length > limit) return 'path is too long';
  if (/[\u0000-\u001f\u007f#]/.test(path)) return 'path holds a character that is not allowed';
  const cut = path.indexOf('?');
  const route = cut === -1 ? path : path.slice(0, cut);
  if (!route.startsWith('/api/v3/')) return 'path must start with /api/v3/';
  if (/[\\@]/.test(route)) return 'path holds a character that is not allowed';
  if (/%(?:2f|5c|2e|00|25)/i.test(route)) return 'path holds an encoded separator or dot';
  let url;
  try { url = new URL(route, 'http://instance.invalid'); } catch { return 'path does not parse'; }
  if (url.origin !== 'http://instance.invalid') return 'path leaves the instance';
  if (url.pathname !== route) return 'path is not in normal form';
  return null;
}

/**
 * `request(account, method, path, body)` performs the call. `log(entry)` receives
 * one entry per call, including refused ones. Throws nothing: a refusal is a result.
 */
export function createAppSurface({ mode, request, log = () => {}, limits = DEFAULT_LIMITS, now = () => new Date().toISOString() }) {
  if (!['discovery', 'decision'].includes(mode)) throw Error('mode must be discovery or decision');
  const counts = { requests: 0, reads: 0, recordsCreated: 0, refused: 0 };
  const refuse = (entry, reason) => {
    counts.refused += 1;
    log({ at: now(), mode, ...entry, refused: reason });
    return { ok: false, refused: reason };
  };
  const forward = async (account, method, path, body) => {
    const response = await request(account, method, path, body);
    let text = JSON.stringify(response.body ?? null);
    const truncated = text.length > limits.responseChars;
    if (truncated) text = text.slice(0, limits.responseChars);
    log({ at: now(), mode, as: account, method, path, status: response.status });
    return { ok: true, status: response.status, body: truncated ? undefined : response.body,
      ...(truncated ? { bodyText: text, truncated: true } : {}) };
  };
  const tools = mode === 'decision' ? {
    app_get: async ({ path } = {}) => {
      const entry = { as: 'approver', method: 'GET', path: typeof path === 'string' ? path.slice(0, limits.pathChars) : null };
      const reason = refusePath(path, limits.pathChars);
      if (reason) return refuse(entry, reason);
      if (counts.reads >= limits.decision.reads) return refuse(entry, `read limit of ${limits.decision.reads} reached`);
      counts.reads += 1;
      return forward('approver', 'GET', path);
    },
  } : {
    app_request: async ({ as, method, path, body } = {}) => {
      const entry = { as: typeof as === 'string' ? as.slice(0, 16) : null, method: typeof method === 'string' ? method.slice(0, 8) : null,
        path: typeof path === 'string' ? path.slice(0, limits.pathChars) : null };
      if (!ACCOUNTS.has(as)) return refuse(entry, 'as must be author or approver');
      if (!DISCOVERY_METHODS.has(method)) return refuse(entry, 'method must be GET, POST, PATCH or DELETE');
      const reason = refusePath(path, limits.pathChars);
      if (reason) return refuse(entry, reason);
      if (body !== undefined && (body === null || typeof body !== 'object' || Array.isArray(body)
          || JSON.stringify(body).length > limits.bodyBytes)) return refuse(entry, `body must be an object of at most ${limits.bodyBytes} bytes`);
      if (method === 'GET' && body !== undefined) return refuse(entry, 'a GET takes no body');
      if (counts.requests >= limits.discovery.requests) return refuse(entry, `request limit of ${limits.discovery.requests} reached`);
      const creates = method === 'POST' && CREATES_RECORD.test(path);
      if (creates && counts.recordsCreated >= limits.discovery.recordsCreated) {
        return refuse(entry, `record limit of ${limits.discovery.recordsCreated} reached`);
      }
      counts.requests += 1;
      const result = await forward(as, method, path, body);
      if (creates && result.status === 201) counts.recordsCreated += 1;
      return result;
    },
  };
  return Object.freeze({ mode, tools, counts: () => ({ ...counts }) });
}

export const TOOL_DEFINITIONS = Object.freeze({
  app_request: {
    name: 'app_request',
    description: 'Make one OpenProject API v3 call on the instance under test, as the author or the approver test account. '
      + 'This is the only way to reach the application. Returns the HTTP status and the JSON body.',
    inputSchema: { type: 'object', additionalProperties: false, required: ['as', 'method', 'path'], properties: {
      as: { type: 'string', enum: ['author', 'approver'] },
      method: { type: 'string', enum: ['GET', 'POST', 'PATCH', 'DELETE'] },
      path: { type: 'string', description: 'Starts with /api/v3/. A query string is allowed.' },
      body: { type: 'object', description: 'JSON body for POST and PATCH.' },
    } },
  },
  app_get: {
    name: 'app_get',
    description: 'Read one OpenProject API v3 resource on the instance under test, as the approver. '
      + 'Read-only, and only a few reads are allowed. Returns the HTTP status and the JSON body.',
    inputSchema: { type: 'object', additionalProperties: false, required: ['path'], properties: {
      path: { type: 'string', description: 'Starts with /api/v3/. A query string is allowed.' },
    } },
  },
});

/**
 * Minimal MCP server over newline-delimited JSON-RPC: initialize, ping, tools/list, tools/call.
 * `tools` maps a name to an async function returning an object with `ok`; `definitions` lists what the model is shown.
 */
export function createToolHandler({ tools, definitions }, write) {
  const versions = ['2025-06-18', '2025-03-26', '2024-11-05'];
  return async message => {
    const id = message?.id;
    const reply = result => { if (id !== undefined) write({ jsonrpc: '2.0', id, result }); };
    const fail = (code, text) => { if (id !== undefined) write({ jsonrpc: '2.0', id, error: { code, message: text } }); };
    const method = String(message?.method ?? '');
    const params = message?.params ?? {};
    try {
      if (method === 'initialize') {
        const requested = String(params.protocolVersion ?? '');
        return reply({ protocolVersion: versions.includes(requested) ? requested : versions[0],
          capabilities: { tools: { listChanged: false } }, serverInfo: { name: 'gammatron-arm-app', version: '1.0.0' } });
      }
      if (method === 'ping') return reply({});
      if (method === 'tools/list') return reply({ tools: definitions });
      if (method === 'tools/call') {
        const tool = Object.hasOwn(tools, params.name) ? tools[params.name] : null;
        let result;
        try {
          result = tool ? await tool(params.arguments ?? {}) : { ok: false, refused: `no such tool: ${String(params.name).slice(0, 64)}` };
        } catch (error) {
          result = { ok: false, error: String(error?.message ?? error).slice(0, 300) };
        }
        return reply({ content: [{ type: 'text', text: JSON.stringify(result) }], ...(result?.ok ? {} : { isError: true }) });
      }
      if (method.startsWith('notifications/')) return undefined;
      return fail(-32601, `Method not found: ${method}`);
    } catch (error) {
      return fail(-32603, String(error?.message ?? error).slice(0, 300));
    }
  };
}

export function createMcpHandler(surface, write) {
  return createToolHandler({ tools: surface.tools, definitions: Object.keys(surface.tools).map(name => TOOL_DEFINITIONS[name]) }, write);
}

/** Reads JSON-RPC lines from stdin and answers on stdout, one message at a time. */
export function serveStdio(handle) {
  let chain = Promise.resolve();
  readline.createInterface({ input: process.stdin, crlfDelay: Infinity }).on('line', line => {
    if (!line.trim()) return;
    let message;
    try { message = JSON.parse(line); } catch {
      process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error' } }) + '\n');
      return;
    }
    chain = chain.then(() => handle(message));
  });
}

/**
 * Reads a session's stream-json log and lists every tool call outside the
 * allowed surface: a tool not on the list, or a file tool aimed outside the
 * session's working directory. An empty `outOfSurface` is the pass condition.
 */
export function auditSessionLog(lines, { allowedTools, workDir }) {
  const allowed = new Set(allowedTools);
  const root = resolve(workDir);
  const calls = [];
  const outOfSurface = [];
  const inside = candidate => {
    const rel = relative(root, resolve(root, candidate));
    return rel === '' || (!rel.startsWith('..') && !isAbsolute(rel));
  };
  for (const line of lines) {
    let event;
    try { event = typeof line === 'string' ? JSON.parse(line) : line; } catch { continue; }
    const blocks = event?.message?.content;
    if (event?.type !== 'assistant' || !Array.isArray(blocks)) continue;
    for (const block of blocks) {
      if (block?.type !== 'tool_use') continue;
      calls.push(block.name);
      if (!allowed.has(block.name)) { outOfSurface.push({ tool: block.name, reason: 'tool not allowed' }); continue; }
      if (block.name.startsWith('mcp__')) continue;
      for (const key of ['file_path', 'path', 'notebook_path']) {
        const value = block.input?.[key];
        if (typeof value === 'string' && !inside(value)) outOfSurface.push({ tool: block.name, reason: `${key} outside the working directory` });
      }
    }
  }
  return { toolCalls: calls.length, byTool: Object.fromEntries([...new Set(calls)].map(n => [n, calls.filter(c => c === n).length])), outOfSurface };
}

async function main() {
  const config = JSON.parse(process.env.GAMMATRON_ARM_SURFACE ?? 'null');
  if (!config?.mode || !config.logFile) throw Error('GAMMATRON_ARM_SURFACE must name mode and logFile');
  const state = readState(config.stateFile);
  const surface = createAppSurface({
    mode: config.mode,
    request: openProjectRequester(state[config.side ?? 'new']),
    limits: { ...DEFAULT_LIMITS, ...(config.limits ?? {}) },
    log: entry => appendFileSync(config.logFile, JSON.stringify({ arm: config.arm ?? null, ...entry }) + '\n', { mode: 0o600 }),
  });
  serveStdio(createMcpHandler(surface, message => process.stdout.write(JSON.stringify(message) + '\n')));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
