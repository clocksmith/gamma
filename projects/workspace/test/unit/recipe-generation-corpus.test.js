import assert from 'node:assert/strict';
import { qualifyRecipeGenerationCorpus } from '../../qualification/recipe-generation-corpus.js';
import { createManagedRecipeEngine } from '../../src/recipe-service/engine.js';
import { createSqliteRecipeStore } from '../../src/recipe-service/store-sqlite.js';

const store = createSqliteRecipeStore();
try {
  const reports = await qualifyRecipeGenerationCorpus(createManagedRecipeEngine({
    store, secret: 'local-corpus-fixture-only-32-characters',
  }));
  assert.equal(reports.length, 7);
  const observations = reports.flatMap(({ checkpoints }) => checkpoints.flatMap(({ probes }) => probes));
  assert.equal(observations.length, 16);
  assert.equal(observations.filter(row => row.status === 'match').length, 15);
  assert.equal(observations.filter(row => row.status === 'mismatch').length, 1);
  console.log('ok: 15 structural generation parity probes plus one deliberately divergent negative control');
} finally { store.close(); }
