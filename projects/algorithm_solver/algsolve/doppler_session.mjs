// Shared model operations for Gamma's Node and browser recognition paths.
// The caller supplies pinned model loading; no source/code catalogue is loaded here.
export function createRecognitionSession({ loadModel, maxTokens = 1024 }) {
  if (!Number.isSafeInteger(maxTokens) || maxTokens < 1) throw new Error('Invalid token bound');
  const models = new Map();
  let closed = false;
  let pending = Promise.resolve();

  async function execute(request) {
    if (closed) throw new Error('Recognition session closed');
    if (!['embedding', 'rerank'].includes(request.operation)) throw new Error('Unknown operation');
    const texts = request.operation === 'embedding' ? request.texts : request.documents;
    const limit = request.operation === 'embedding' ? 32 : 10;
    if (!Array.isArray(texts) || !texts.length || texts.length > limit
        || texts.some(t => typeof t !== 'string' || !t.trim())) {
      throw new Error(`Expected 1–${limit} nonempty texts`);
    }
    if (request.operation === 'rerank' && (typeof request.query !== 'string' || !request.query.trim())) {
      throw new Error('Nonempty reranking query required');
    }
    const started = performance.now();
    if (!models.has(request.operation)) models.set(request.operation, await loadModel(request.operation));
    const model = models.get(request.operation);
    const loaded = performance.now();
    let output;
    if (request.operation === 'embedding') {
      const rows = [];
      for (const text of texts) {
        const tokens = model.advanced.tokenizeText(text);
        const inputIds = tokens.slice(0, maxTokens);
        const result = await model.embedWithEvidence(text, { inputIds });
        if (!inputIds.length || result.tokens.length !== inputIds.length
            || inputIds.some((token, i) => result.tokens[i] !== token)) {
          throw new Error('Doppler executed different embedding tokens than requested');
        }
        const embedding = Array.from(result.embedding);
        const norm = Math.hypot(...embedding);
        if (embedding.length !== 1024 || embedding.some(x => !Number.isFinite(x)) || !Number.isFinite(norm) || norm === 0) {
          throw new Error('Invalid Qwen embedding vector');
        }
        rows.push({ embedding: embedding.map(x => x / norm), tokens: inputIds.length,
          truncated: tokens.length > maxTokens, backend: result.backendIdentity });
      }
      output = { texts, rows };
    } else {
      const result = await model.rerankWithEvidence(request.query, texts);
      const seen = new Set();
      if (result.query !== request.query || !Array.isArray(result.ranking) || result.ranking.length !== texts.length) {
        throw new Error('Reranker response differs from request');
      }
      for (const row of result.ranking) {
        if (!Number.isInteger(row.index) || row.index < 0 || row.index >= texts.length
            || seen.has(row.index) || row.document !== texts[row.index] || !Number.isFinite(row.score)) {
          throw new Error('Invalid or mismatched reranker score');
        }
        seen.add(row.index);
      }
      output = { query: result.query, ranking: result.ranking, backend: result.backendIdentity };
    }
    return { output, load_ms: loaded - started, execution_ms: performance.now() - loaded };
  }

  async function close() {
    closed = true;
    await pending.catch(() => {});
    const handles = [...models.values()];
    models.clear();
    const results = await Promise.allSettled(handles.map(model => model.unload()));
    const failed = results.find(r => r.status === 'rejected');
    if (failed) throw failed.reason;
  }

  return {
    request(request) {
      // Snapshot inputs before waiting; callers cannot mutate an enqueued request.
      const copy = structuredClone(request);
      const result = pending.then(() => execute(copy));
      pending = result.catch(error => { closed = true; throw error; });
      // Keep the failure observable to the caller without an unhandled rejection.
      pending.catch(() => {});
      return result;
    },
    close,
  };
}
