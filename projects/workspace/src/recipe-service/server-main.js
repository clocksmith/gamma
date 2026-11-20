#!/usr/bin/env node
// Standalone Node 22+ / Google Cloud Run HTTP server for Fawn Managed Recipe Service.
import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createSqliteRecipeStore } from './store-sqlite.js';
import { createManagedRecipeEngine } from './engine.js';
import { createManagedRecipeHttpHandler } from './http-handler.js';

export function createNodeRecipeServer({
  dbPath = ':memory:',
  secret,
  clients,
  catalogQuorum = 2,
  maxBodyBytes = 1024 * 1024,
  generationSigner = null,
}) {
  const store = createSqliteRecipeStore(dbPath);
  const engine = createManagedRecipeEngine({ store, secret, catalogQuorum });
  const handler = createManagedRecipeHttpHandler({ engine, clients, maxBodyBytes, generationSigner });

  const server = createServer(async (req, res) => {
    try {
      const host = req.headers.host ?? '127.0.0.1';
      const url = `http://${host}${req.url ?? '/'}`;
      const headers = new Headers();
      for (const [key, value] of Object.entries(req.headers)) {
        if (Array.isArray(value)) headers.set(key, value.join(', '));
        else if (typeof value === 'string') headers.set(key, value);
      }
      const hasBody = req.method !== 'GET' && req.method !== 'HEAD';
      const webReq = new Request(url, {
        method: req.method,
        headers,
        ...(hasBody ? { body: req, duplex: 'half' } : {}),
      });
      const webRes = await handler(webReq);
      const outHeaders = Object.fromEntries(webRes.headers.entries());
      res.writeHead(webRes.status, outHeaders);
      const bytes = Buffer.from(await webRes.arrayBuffer());
      res.end(bytes);
    } catch {
      res.writeHead(500, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify({ error: 'internal-error' }));
    }
  });

  return { server, store, engine };
}

function loadRuntimeConfig() {
  if (process.argv[2]) {
    return JSON.parse(readFileSync(resolve(process.argv[2]), 'utf8'));
  }
  return {
    host: process.env.HOST ?? '0.0.0.0',
    port: Number(process.env.PORT ?? 8080),
    dbPath: process.env.FAWN_RECIPE_DB_PATH ?? '/tmp/fawn-recipes/recipes.sqlite',
    secret: process.env.FAWN_RECIPE_SECRET,
    catalogQuorum: process.env.FAWN_CATALOG_QUORUM ? Number(process.env.FAWN_CATALOG_QUORUM) : 2,
    clients: JSON.parse(process.env.FAWN_RECIPE_CLIENTS_JSON ?? '[]'),
  };
}

const isEntrypoint = (() => {
  try {
    return Boolean(process.argv[1]) && realpathSync(process.argv[1]) === fileURLToPath(import.meta.url);
  } catch {
    return false;
  }
})();

if (isEntrypoint) {
  const cfg = loadRuntimeConfig();
  const host = cfg.host ?? '127.0.0.1';
  const port = Number(cfg.port ?? 8080);
  const { server, store } = createNodeRecipeServer({
    dbPath: cfg.dbPath,
    secret: cfg.secret,
    clients: cfg.clients,
    catalogQuorum: cfg.catalogQuorum ?? 2,
    maxBodyBytes: cfg.maxBodyBytes ?? 1024 * 1024,
  });
  const shutdown = () => {
    server.close(() => {
      store.close();
      process.exit(0);
    });
  };
  process.once('SIGINT', shutdown);
  process.once('SIGTERM', shutdown);
  server.listen(port, host, () => {
    console.log(JSON.stringify({
      event: 'fawn-recipe-service-ready',
      host,
      port: server.address().port,
      store: store.kind,
    }));
  });
}
