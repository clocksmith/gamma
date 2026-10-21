// Private stdio worker: model execution belongs to Doppler, recognition to Gamma.
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';

console.log = console.error; // stdout is exclusively the response protocol.
console.info = console.error;
const config = JSON.parse(await readFile(process.argv[2], 'utf8'));
const root = pathToFileURL(`${config.root}/`);
const { installNodeFileFetchShim } = await import(new URL('src/tooling/node-file-fetch.js', root));
installNodeFileFetchShim();
const localFetch = globalThis.fetch;
globalThis.fetch = (input, options) => {
  const url = typeof input === 'string' ? input : input?.url ?? input?.href;
  if (!String(url).startsWith('file:')) throw new Error('Gamma Doppler worker forbids network fetches');
  return localFetch(input, options);
};
const { load } = await import(new URL('src/client/doppler-api.js', root));
const models = new Map();
const hash = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');

async function modelFor(operation) {
  if (models.has(operation)) return models.get(operation);
  const spec = config[operation];
  if (!spec) throw new Error(`No ${operation} model configured`);
  const bytes = await readFile(`${spec.path}/manifest.json`);
  if (createHash('sha256').update(bytes).digest('hex') !== spec.manifest_sha256) {
    throw new Error('Model manifest changed');
  }
  const model = await load({ url: pathToFileURL(spec.path).href }, {
    cache: false, isolatedLoader: true, onProgress() {},
    runtimeConfig: spec.runtime_config ?? {},
  });
  models.set(operation, model);
  return model;
}

async function execute(request) {
  const started = performance.now();
  if (!['embedding', 'rerank'].includes(request.operation)) throw new Error('Unknown operation');
  const model = await modelFor(request.operation);
  const loaded = performance.now();
  let output;
  if (request.operation === 'embedding') {
    if (!Array.isArray(request.texts) || !request.texts.length || request.texts.length > 32
        || request.texts.some(t => typeof t !== 'string' || !t.trim())) {
      throw new Error('Embedding requires 1–32 nonempty texts');
    }
    const rows = [];
    for (const text of request.texts) {
      const tokens = model.advanced.tokenizeText(text);
      // Match Gamma's existing encoder's right truncation, without re-tokenizing.
      const inputIds = tokens.slice(0, config.max_tokens);
      const result = await model.embedWithEvidence(text, { inputIds });
      if (!inputIds.length || result.tokens.length !== inputIds.length
          || inputIds.some((token, index) => result.tokens[index] !== token)) {
        throw new Error('Doppler executed different embedding tokens than requested');
      }
      rows.push({
        embedding: Array.from(result.embedding), tokens: result.tokens.length,
        truncated: tokens.length > config.max_tokens,
        backend: result.backendIdentity,
      });
    }
    output = { texts: request.texts, rows };
  } else {
    if (typeof request.query !== 'string' || !request.query.trim()
        || !Array.isArray(request.documents) || !request.documents.length
        || request.documents.length > 10
        || request.documents.some(d => typeof d !== 'string' || !d.trim())) {
      throw new Error('Reranking requires a query and 1–10 nonempty documents');
    }
    const result = await model.rerankWithEvidence(request.query, request.documents);
    output = { query: result.query, ranking: result.ranking, backend: result.backendIdentity };
  }
  return {
    output, input_sha256: hash(request),
    load_ms: loaded - started, execution_ms: performance.now() - loaded,
  };
}

try {
  // Sequential execution retains models and avoids cross-request runtime races.
  for await (const line of createInterface({ input: process.stdin, crlfDelay: Infinity })) {
    let request;
    try {
      request = JSON.parse(line);
      if (!Number.isSafeInteger(request.id)) throw new Error('Request id required');
      const result = await execute(request);
      process.stdout.write(JSON.stringify({ id: request.id, ok: true, result }) + '\n');
    } catch (error) {
      process.stdout.write(JSON.stringify({
        id: request?.id ?? null, ok: false, error: String(error?.stack ?? error),
      }) + '\n');
      // A failed GPU operation may have invalidated runtime state. Never reuse it.
      process.exitCode = 1;
      break;
    }
  }
} finally {
  for (const model of models.values()) await model.unload();
}
// The Node WebGPU provider may retain native handles after model cleanup.
process.exit(process.exitCode ?? 0);
