// Model-driven comparison spend guard: frozen request fields, bounded retries and the hard ceiling.
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { ProviderError, createClient } from '../../qualification/model-agent/anthropic-client.js';
import { SpendLedger } from '../../qualification/model-agent/spend-ledger.js';

const AGENT = Object.freeze({ model: 'claude-sonnet-5-5', maxOutputTokensPerTurn: 2048, thinking: { type: 'disabled' } });
const PRICES = Object.freeze({ input: 2, output: 10 });
const CEILING_USD = 275;
const OVERLOADED = 529;
const USAGE = Object.freeze({ input_tokens: 1000, output_tokens: 100 });

function provider(failuresBeforeSuccess) {
  const sent = [];
  let failures = failuresBeforeSuccess;
  const fetchImpl = async (url, init) => {
    sent.push(JSON.parse(init.body));
    if (failures > 0) {
      failures -= 1;
      return new Response('overloaded', { status: OVERLOADED });
    }
    return new Response(JSON.stringify({ model: AGENT.model, content: [], stop_reason: 'end_turn', usage: USAGE }), { status: 200 });
  };
  return { sent, fetchImpl };
}

const turn = { system: 'system', tools: [], messages: [{ role: 'user', content: 'task' }], purpose: 'test' };
const directory = mkdtempSync(join(tmpdir(), 'fawn-model-spend-'));

{
  const { sent, fetchImpl } = provider(2);
  const ledger = new SpendLedger({ path: join(directory, 'ledger.json'), ceilingUsd: CEILING_USD, prices: PRICES });
  await createClient({ apiKey: 'key', agent: AGENT, ledger, fetchImpl, backoffMs: 0 }).turn(turn);
  assert.equal(sent.length, 3);
  assert.deepEqual(Object.keys(sent.at(-1)).sort(), ['max_tokens', 'messages', 'model', 'system', 'thinking', 'tools']);
  assert.deepEqual(sent.at(-1).thinking, { type: 'disabled' });
  const expected = (USAGE.input_tokens * PRICES.input + USAGE.output_tokens * PRICES.output) / 1e6;
  assert.equal(ledger.spentUsd, expected);
  const reopened = new SpendLedger({ path: join(directory, 'ledger.json'), ceilingUsd: CEILING_USD, prices: PRICES });
  assert.equal(reopened.spentUsd, expected);
  assert.throws(() => new SpendLedger({ path: join(directory, 'ledger.json'), ceilingUsd: CEILING_USD + 1, prices: PRICES }));
}

{
  const { sent, fetchImpl } = provider(Infinity);
  const ledger = new SpendLedger({ path: join(directory, 'retries.json'), ceilingUsd: CEILING_USD, prices: PRICES });
  await assert.rejects(createClient({ apiKey: 'key', agent: AGENT, ledger, fetchImpl, backoffMs: 0 }).turn(turn),
    (error) => error instanceof ProviderError && error.status === OVERLOADED);
  assert.equal(sent.length, 4);
  assert.equal(ledger.spentUsd, 0);
}

{
  const { sent, fetchImpl } = provider(0);
  const ledger = new SpendLedger({ path: join(directory, 'ceiling.json'), ceilingUsd: CEILING_USD, prices: PRICES });
  ledger.charge({ input_tokens: (CEILING_USD - 0.001) * 1e6 / PRICES.input, output_tokens: 0 }, 'prior');
  await assert.rejects(createClient({ apiKey: 'key', agent: AGENT, ledger, fetchImpl, backoffMs: 0 }).turn(turn),
    (error) => error.code === 'spend-ceiling');
  assert.equal(sent.length, 0);
}

{
  const apiKey = 'sk-test-secret';
  const fetchImpl = async () => new Response(`{"error":"bad key ${apiKey}"}`, { status: 401 });
  const ledger = new SpendLedger({ path: join(directory, 'redaction.json'), ceilingUsd: CEILING_USD, prices: PRICES });
  await assert.rejects(createClient({ apiKey, agent: AGENT, ledger, fetchImpl, backoffMs: 0 }).turn(turn),
    (error) => error instanceof ProviderError && !error.message.includes(apiKey) && error.message.includes('[redacted]'));
}

console.log('ok: model-spend');
