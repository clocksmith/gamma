import { canonicalJson } from '../client/trace-graph-dp.js';

export const ACCEPTED_GRAPH_COMPILER_V1 = 'gamma.recipe-workspace-dag/v1';
const MAX_TRACES = 512;
const MAX_INPUT_BYTES = 4 * 1024 * 1024;
const MAX_INPUT_STEPS = 4096;

/**
 * Deterministically rebuild a workspace graph from a bounded prefix of the
 * immutable acceptance log. Preserve raw trace facts and existing v3
 * reduction semantics; do not write to the legacy graph or resolve API.
 */
export async function compileAcceptedGraph({
  store, meta, inputWatermark, limits, replanPenalty,
  reduceCandidateNodes, materializeSteps, empiricalEdgeWeight, sha256Hex, serviceError,
}) {
  if (meta.scope !== 'workspace') throw Error('Accepted graph compiler requires workspace scope');
  if (!Number.isSafeInteger(inputWatermark) || inputWatermark < 1 || inputWatermark > MAX_TRACES) {
    throw serviceError(400, 'invalid-compile-watermark', `Input watermark must be between 1 and ${MAX_TRACES}`);
  }

  const query = 'FROM recipe_trace_acceptance WHERE namespace_id = ? AND acceptance_seq <= ?';
  const params = [meta.namespaceId, inputWatermark];
  const bounds = await store.get(
    `SELECT COUNT(*) AS count, COALESCE(SUM(length(CAST(payload_json AS BLOB))), 0) AS bytes ${query}`, params,
  );
  if (Number(bounds.count) !== inputWatermark) {
    throw serviceError(409, 'unavailable-trace-watermark', 'Accepted log does not contain the full requested prefix');
  }
  if (Number(bounds.bytes) > MAX_INPUT_BYTES) {
    throw serviceError(413, 'compile-budget-exceeded', 'Accepted log exceeds the compiler byte budget');
  }
  // Prefix rows cannot change once accepted; later appends are out of scope.
  const rows = await store.all(
    `SELECT acceptance_seq, payload_digest, payload_json ${query} ORDER BY acceptance_seq`, params,
  );
  const nodes = new Map(), edges = new Map(), digests = [];
  let sourceSteps = 0;
  function node(id) {
    if (!nodes.has(id)) nodes.set(id, { depth: 0, edges: [], repairs: [], terminal: false });
    return nodes.get(id);
  }
  if (rows.length !== inputWatermark) throw Error('Accepted trace prefix changed during compile');

  for (const [i, row] of rows.entries()) {
    if (Number(row.acceptance_seq) !== i + 1 || sha256Hex(row.payload_json) !== row.payload_digest) {
      throw Error('Accepted trace prefix failed sequence or digest verification');
    }
    const payload = JSON.parse(row.payload_json);
    if (payload.format !== 'gamma.recipe-trace/v1' || payload.scope !== meta.scope ||
        payload.origin !== meta.origin || payload.template !== meta.template ||
        payload.readScope !== meta.readScope || !Array.isArray(payload.steps)) {
      throw Error('Accepted trace payload does not match the compiler namespace or format');
    }
    digests.push(row.payload_digest);
    sourceSteps += payload.steps.length;
    if (sourceSteps > MAX_INPUT_STEPS) {
      throw serviceError(413, 'compile-budget-exceeded', 'Accepted log exceeds the compiler step budget');
    }
    const materialized = materializeSteps(meta.dagKey, meta, payload.steps);
    for (const record of materialized.records) {
      node(record.id);
      if (materialized.terminal?.id === record.next) node(record.next).terminal = true;
      else node(record.next);
      const key = canonicalJson([record.id, record.next, record.step]);
      let edge = edges.get(key);
      if (!edge) {
        edge = { from: record.id, next: record.next, step: record.step, attempts: 0, completions: 0, total_cost_ms: 0 };
        edges.set(key, edge);
      }
      edge.attempts += 1;
      edge.completions += Number(record.meta.outcome === 'completed');
      edge.total_cost_ms += record.meta.elapsedMs;
    }
  }
  for (const edge of edges.values()) {
    node(edge.from).edges.push({ next: edge.next, step: edge.step, weight: empiricalEdgeWeight(edge, replanPenalty) });
  }
  const reduced = reduceCandidateNodes(nodes, limits);
  const reducedEdges = [...reduced.nodes.values()].reduce((sum, n) => sum + n.edges.length, 0);
  if (reduced.nodes.size > limits.maxNodes || reducedEdges > limits.maxEdges) {
    throw serviceError(413, 'compile-budget-exceeded', 'Reduced graph exceeds the pinned limits');
  }
  // No key, mutable table state, receipt timestamp, or runtime permission is
  // embedded in a snapshot. It is a derived artifact from pinned source input.
  return {
    version: 3,
    inputDigest: sha256Hex(canonicalJson(digests)),
    limits,
    replanPenalty,
    nodes: [...reduced.nodes],
    reduction: reduced.stats,
  };
}
