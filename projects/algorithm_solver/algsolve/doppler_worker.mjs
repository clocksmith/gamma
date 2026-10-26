// Private stdio worker: model execution belongs to Doppler, recognition to Gamma.
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';
import { createRecognitionSession } from './doppler_session.mjs';

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
const hash = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');

async function modelFor(operation) {
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
  return model;
}

const session = createRecognitionSession({ loadModel: modelFor, maxTokens: config.max_tokens });

try {
  // Sequential execution retains models and avoids cross-request runtime races.
  for await (const line of createInterface({ input: process.stdin, crlfDelay: Infinity })) {
    let request;
    try {
      request = JSON.parse(line);
      if (!Number.isSafeInteger(request.id)) throw new Error('Request id required');
      const result = await session.request(request);
      result.input_sha256 = hash(request);
      result.execution_surface = { kind: 'node', version: process.version };
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
  await session.close();
}
// The Node WebGPU provider may retain native handles after model cleanup.
process.exit(process.exitCode ?? 0);
