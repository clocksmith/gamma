import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRecognitionSession } from '../algsolve/doppler_session.mjs';

function fixture(overrides = {}) {
  let loads = 0, closes = 0;
  const session = createRecognitionSession({ maxTokens: 2, loadModel: async () => {
    loads++;
    return {
      advanced: { tokenizeText: () => [7, 8, 9] },
      embedWithEvidence: async (text, { inputIds }) => {
        assert.equal(typeof text, 'string');
        assert.deepEqual(inputIds, [7, 8]);
        return { tokens: inputIds, embedding: [2, ...Array(1023).fill(0)], backendIdentity: {} };
      },
      rerankWithEvidence: async (query, docs) => ({ query, ranking: docs.map((document, index) => ({ document, index, score: index })) }),
      unload: async () => { closes++; },
      ...overrides,
    };
  }});
  return { session, counts: () => [loads, closes] };
}

test('queued input snapshots, truncation, normalization and retained model switching', async () => {
  const { session, counts } = fixture();
  const input = { operation: 'embedding', texts: ['original'] };
  const first = session.request(input);
  input.texts[0] = 'mutated';
  assert.equal((await first).output.texts[0], 'original');
  await session.request({ operation: 'rerank', query: 'q', documents: ['a', 'b'] });
  const result = await session.request({ operation: 'embedding', texts: ['again'] });
  assert.equal(result.output.rows[0].truncated, true);
  assert.equal(result.output.rows[0].embedding[0], 1);
  assert.deepEqual(counts(), [2, 0]);
  await session.close();
  assert.deepEqual(counts(), [2, 2]);
  await assert.rejects(session.request(input), /closed/);
});

test('changed tokens poison the session and cleanup unloads the model', async () => {
  const { session, counts } = fixture({ embedWithEvidence: async () => ({ tokens: [7, 10] }) });
  await assert.rejects(session.request({ operation: 'embedding', texts: ['x'] }), /different.*tokens/);
  await assert.rejects(session.request({ operation: 'embedding', texts: ['x'] }));
  await session.close();
  assert.deepEqual(counts(), [1, 1]);
});

test('missing, duplicate, nonfinite or relabelled reranker results fail closed', async () => {
  for (const ranking of [[], [{ index: 0, document: 'a', score: 1 }, { index: 0, document: 'b', score: 2 }],
    [{ index: 0, document: 'a', score: NaN }, { index: 1, document: 'b', score: 2 }],
    [{ index: 0, document: 'b', score: 1 }, { index: 1, document: 'a', score: 2 }]]) {
    const { session } = fixture({ rerankWithEvidence: async query => ({ query, ranking }) });
    await assert.rejects(session.request({ operation: 'rerank', query: 'q', documents: ['a', 'b'] }));
    await session.close();
  }
});

test('invalid inputs cannot load a model', async () => {
  const { session, counts } = fixture();
  await assert.rejects(session.request({ operation: 'rerank', query: 'q', documents: [''] }));
  assert.deepEqual(counts(), [0, 0]);
  await session.close();
});
