// Owner-local monotonic state. Protects against remote rollback, not an owner
// deleting/restoring the database or an attacker controlling the local account.
import { closeSync, constants, fstatSync, lstatSync, mkdirSync, openSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { privateStat } from './private-json-file.js';
import { canonicalJson } from './trace-graph-dp.js';

const DIGEST = /^[a-f0-9]{64}$/;
const fail = (code, message) => Object.assign(Error(message), { code });
function scopeKey(pin) {
  if (!pin || !DIGEST.test(pin.namespaceId ?? '') || !DIGEST.test(pin.generationDigest ?? '') ||
      !Number.isSafeInteger(pin.generation) || pin.generation < 1 ||
      typeof pin.compilerVersion !== 'string' || !pin.limits || !Number.isFinite(pin.replanPenalty)) {
    throw new TypeError('Verified recipe generation pin required');
  }
  // A publisher key rotation must not reset a floor for unchanged route policy.
  return canonicalJson([pin.namespaceId, pin.compilerVersion, pin.limits, pin.replanPenalty]);
}

export class RecipeReplayFloor {
  #db;
  #advance;
  #read;

  constructor(path) {
    const file = resolve(path);
    const directory = dirname(file);
    mkdirSync(directory, { recursive: true, mode: 0o700 });
    privateStat(lstatSync(directory), true);
    const fd = openSync(file, constants.O_CREAT | constants.O_RDWR | constants.O_NOFOLLOW, 0o600);
    try { privateStat(fstatSync(fd)); } finally { closeSync(fd); }
    this.#db = new DatabaseSync(file);
    try {
      this.#db.exec(`
        PRAGMA busy_timeout = 1000;
        PRAGMA synchronous = FULL;
        CREATE TABLE IF NOT EXISTS recipe_replay_floor (
          scope TEXT PRIMARY KEY, generation INTEGER NOT NULL, digest TEXT NOT NULL
        ) STRICT;
      `);
      this.#advance = this.#db.prepare(`
        INSERT INTO recipe_replay_floor(scope, generation, digest) VALUES (?, ?, ?)
        ON CONFLICT(scope) DO UPDATE SET generation = excluded.generation, digest = excluded.digest
        WHERE excluded.generation > recipe_replay_floor.generation
           OR (excluded.generation = recipe_replay_floor.generation AND excluded.digest = recipe_replay_floor.digest)
      `);
      this.#read = this.#db.prepare('SELECT generation, digest FROM recipe_replay_floor WHERE scope = ?');
    } catch (error) { this.#db.close(); throw error; }
  }

  /** Only call after publisher, exact request, policy and snapshot all verified. */
  advance(pin) {
    const scope = scopeKey(pin);
    if (this.#advance.run(scope, pin.generation, pin.generationDigest).changes !== 1) {
      throw fail('recipe-replay-refused', 'Recipe generation would roll back or conflict with the durable pin');
    }
  }

  /** Cached data cannot roll back the floor advanced by another store handle. */
  assertCurrent(pin) {
    const row = this.#read.get(scopeKey(pin));
    if (!row || pin.generation !== row.generation || pin.generationDigest !== row.digest) {
      throw fail('recipe-replay-refused', 'Cached recipe generation does not match the durable pin');
    }
  }

  close() { this.#db.close(); }
}
