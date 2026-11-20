// Cloudflare Worker entrypoint for Fawn Managed Recipe Service (backed by Cloudflare D1).
import { createD1RecipeStore } from './store-d1.js';
import { createManagedRecipeEngine } from './engine.js';
import { createManagedRecipeHttpHandler } from './http-handler.js';

let cachedKey = null;
let cachedHandler = null;

function getHandler(env) {
  const secret = env.FAWN_RECIPE_SECRET;
  const clientsRaw = env.FAWN_RECIPE_CLIENTS_JSON;
  const quorum = env.FAWN_CATALOG_QUORUM ? Number(env.FAWN_CATALOG_QUORUM) : 2;
  if (typeof secret !== 'string' || secret.length < 32) {
    throw Error('FAWN_RECIPE_SECRET secret (>=32 chars) must be configured');
  }
  if (typeof clientsRaw !== 'string' || !clientsRaw.trim()) {
    throw Error('FAWN_RECIPE_CLIENTS_JSON secret must be configured');
  }
  const cacheIdentity = `${secret.length}:${quorum}:${clientsRaw}`;
  if (cachedHandler && cachedKey === cacheIdentity) return cachedHandler;
  const clients = JSON.parse(clientsRaw);
  const store = createD1RecipeStore(env.DB);
  const engine = createManagedRecipeEngine({ store, secret, catalogQuorum: quorum });
  cachedHandler = createManagedRecipeHttpHandler({ engine, clients });
  cachedKey = cacheIdentity;
  return cachedHandler;
}

export default {
  async fetch(request, env) {
    const handler = getHandler(env);
    return handler(request);
  },
};
