// Node 22+ built-in SQLite storage adapter (used locally and on Google Cloud Run).
import { mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { RECIPE_SERVICE_SCHEMA_SQL } from './schema.js';

export function createSqliteRecipeStore(filename = ':memory:') {
  if (filename !== ':memory:') {
    mkdirSync(dirname(filename), { recursive: true, mode: 0o700 });
  }
  const db = new DatabaseSync(filename);
  db.exec('PRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON;');
  db.exec(RECIPE_SERVICE_SCHEMA_SQL);

  return {
    kind: 'node-sqlite',
    async ensureSchema() {},
    async get(sql, params = []) {
      const row = db.prepare(sql).get(...params);
      return row ? { ...row } : null;
    },
    async all(sql, params = []) {
      return db.prepare(sql).all(...params).map(row => ({ ...row }));
    },
    async run(sql, params = []) {
      const res = db.prepare(sql).run(...params);
      return { changes: Number(res.changes ?? 0) };
    },
    async batch(statements) {
      db.exec('BEGIN IMMEDIATE');
      try {
        for (const { sql, params = [] } of statements) {
          db.prepare(sql).run(...params);
        }
        db.exec('COMMIT');
      } catch (error) {
        try { db.exec('ROLLBACK'); } catch {}
        throw error;
      }
    },
    close() {
      db.close();
    },
  };
}
