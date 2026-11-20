// Fawn workspace model-driven comparison — durable spend ledger with a hard ceiling.
//
// Shared by the compatibility request, the wiring smoke and the full run. Before each request
// the ledger assumes the worst case: every request byte is an input token and the full output
// allowance is used. A request that could cross the ceiling is refused, never sent.

import { closeSync, existsSync, fsyncSync, openSync, readFileSync, renameSync, writeSync } from 'node:fs';

class SpendCeilingReached extends Error {
  constructor(detail) {
    super(`spend ceiling: ${detail}`);
    this.code = 'spend-ceiling';
  }
}

class SpendLedger {
  constructor({ path, ceilingUsd, prices }) {
    this._path = path;
    this._ceiling = ceilingUsd;
    this._prices = prices;
    this._state = existsSync(path) ? JSON.parse(readFileSync(path, 'utf8')) : { ceilingUsd, prices, spentUsd: 0, requests: [] };
    if (this._state.ceilingUsd !== ceilingUsd) throw new Error('ledger ceiling differs from the frozen ceiling');
  }

  get spentUsd() {
    return this._state.spentUsd;
  }

  cost(inputTokens, outputTokens) {
    return (inputTokens * this._prices.input + outputTokens * this._prices.output) / 1e6;
  }

  reserve(requestBytes, maxOutputTokens, purpose) {
    const worst = this.cost(requestBytes, maxOutputTokens);
    if (this._state.spentUsd + worst > this._ceiling) {
      throw new SpendCeilingReached(`${purpose} could reach ${(this._state.spentUsd + worst).toFixed(2)} of ${this._ceiling}`);
    }
  }

  charge(usage, purpose) {
    const cost = this.cost(usage.input_tokens + (usage.cache_creation_input_tokens ?? 0) + (usage.cache_read_input_tokens ?? 0),
      usage.output_tokens);
    this._state.spentUsd += cost;
    this._state.requests.push({ at: new Date().toISOString(), purpose, usage, costUsd: cost });
    this._save();
    return cost;
  }

  _save() {
    const temporary = `${this._path}.tmp`;
    const fd = openSync(temporary, 'w');
    writeSync(fd, JSON.stringify(this._state, null, 2));
    fsyncSync(fd);
    closeSync(fd);
    renameSync(temporary, this._path);
  }
}

export { SpendCeilingReached, SpendLedger };
