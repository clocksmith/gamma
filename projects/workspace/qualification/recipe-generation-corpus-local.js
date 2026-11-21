import { qualifyRecipeGenerationCorpus } from './recipe-generation-corpus.js';
import { createManagedRecipeEngine } from '../src/recipe-service/engine.js';
import { createSqliteRecipeStore } from '../src/recipe-service/store-sqlite.js';

const store = createSqliteRecipeStore();
try {
  const results = await qualifyRecipeGenerationCorpus(createManagedRecipeEngine({
    store, secret: 'local-corpus-fixture-only-32-characters',
  }));
  console.log(JSON.stringify({ qualification: 'recipe-generation-corpus/v1', storage: 'local-sqlite', results }));
} finally { store.close(); }
