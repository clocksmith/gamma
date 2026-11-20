// Cloudflare D1 storage adapter for Fawn Managed Recipe Service.
import { RECIPE_SERVICE_SCHEMA_SQL } from './schema.js';

export function createD1RecipeStore(d1) {
  if (!d1 || typeof d1.prepare !== 'function') {
    throw Error('Cloudflare D1 binding is required');
  }
  let initialized = false;
  async function ensureSchema() {
    if (initialized) return;
    const statements = RECIPE_SERVICE_SCHEMA_SQL
      .split(';')
      .map(stmt => stmt.trim())
      .filter(Boolean);
    await d1.batch(statements.map(sql => d1.prepare(sql)));
    initialized = true;
  }
  return {
    kind: 'cloudflare-d1',
    ensureSchema,
    async get(sql, params = []) {
      await ensureSchema();
      const row = await d1.prepare(sql).bind(...params).first();
      return row ? { ...row } : null;
    },
    async all(sql, params = []) {
      await ensureSchema();
      const res = await d1.prepare(sql).bind(...params).all();
      return res.results ?? [];
    },
    async run(sql, params = []) {
      await ensureSchema();
      const res = await d1.prepare(sql).bind(...params).run();
      return { changes: Number(res.meta?.changes ?? 0) };
    },
    async batch(statements) {
      await ensureSchema();
      if (!statements.length) return;
      await d1.batch(statements.map(({ sql, params = [] }) => d1.prepare(sql).bind(...params)));
    },
    close() {},
  };
}
