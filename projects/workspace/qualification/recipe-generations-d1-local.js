// Run with a locally installed Miniflare v4: node qualification/recipe-generations-d1-local.js /absolute/path/to/node_modules/miniflare
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const modulePath = process.argv[2];
if (!modulePath?.startsWith('/')) throw new Error('Provide the absolute path to a local Miniflare v4 installation');
const { Miniflare } = createRequire(import.meta.url)(modulePath);
const modulesRoot = fileURLToPath(new URL('../', import.meta.url));
const scriptPath = fileURLToPath(new URL('./recipe-generations-d1-worker.js', import.meta.url));
const runtime = new Miniflare({ host: '127.0.0.1', port: 0, modules: true, modulesRoot, scriptPath,
  modulesRules: [{ type: 'ESModule', include: ['**/*.js'] }],
  compatibilityDate: '2026-07-21', compatibilityFlags: ['nodejs_compat'],
  d1Databases: { DB: 'gamma-recipe-qualification-ephemeral' }, d1Persist: false,
});
try {
  const response = await fetch(new URL('/check', await runtime.ready), {
    method: 'POST', redirect: 'manual', signal: AbortSignal.timeout(10_000),
  });
  const body = await response.text();
  if (!response.ok) throw new Error(`Local D1 qualification failed: ${response.status} ${body}`);
  console.log(body);
} finally { await runtime.dispose(); }
