// Managed recipe graph engine: PII-free sub-recipe authoring, cross-template composition,
// quorum-gated trace ingestion, whole-graph detour compression and empirical Bellman DP serving.
import { createHash, createHmac } from 'node:crypto';
import {
  analyzeTraceGraph,
  canonicalJson,
  compressTraceRecords,
  reduceTraceGraph,
  solveRecipeDp,
} from '../client/trace-graph-dp.js';

const VERSION = 3;
const HASH_RE = /^[a-f0-9]{64}$/;
const UUID_RE = /^[a-zA-Z0-9._:-]{6,128}$/;
const IDENT_RE = /^[a-zA-Z0-9._:/-]{1,128}$/;
const KINDS = new Set(['fill', 'select', 'click']);
const FORBIDDEN_INPUT_TYPES = new Set(['submit', 'image', 'file', 'password', 'hidden']);
const ALLOWED_STEP_KEYS = new Set([
  'beforeOutline',
  'afterOutline',
  'kind',
  'locator',
  'slot',
  'beforeSlots',
  'beforeClicks',
  'elapsedMs',
  'outcome',
]);
const DEFAULT_LIMITS = Object.freeze({ maxNodes: 256, maxEdges: 512, maxSteps: 32 });
const DEFAULT_REPLAN_PENALTY = 1000;

function serviceError(status, code, message) {
  return Object.assign(Error(message), { status, code });
}

function sha256Hex(text) {
  return createHash('sha256').update(text).digest('hex');
}

function hmacHex(key, text) {
  return createHmac('sha256', key).update(text).digest('hex');
}

function dagHash(dagKey, value) {
  return hmacHex(dagKey, canonicalJson(value));
}

function validateOrigin(origin) {
  if (typeof origin !== 'string' || !origin.trim() || origin.length > 256) {
    throw serviceError(400, 'invalid-origin', 'Explicit http(s) origin is required');
  }
  let parsed;
  try { parsed = new URL(origin); }
  catch { throw serviceError(400, 'invalid-origin', 'Malformed origin URL'); }
  if (!['http:', 'https:'].includes(parsed.protocol) || parsed.origin !== origin) {
    throw serviceError(400, 'non-origin-url-rejected', 'Origin must exclude paths, queries, fragments and credentials');
  }
  return parsed.origin;
}

function validateIdentifier(value, field) {
  if (typeof value !== 'string' || !IDENT_RE.test(value)) {
    throw serviceError(400, `invalid-${field}`, `Invalid ${field} identifier`);
  }
  return value;
}

function validateScope(scope) {
  if (scope !== 'workspace' && scope !== 'catalog') {
    throw serviceError(400, 'invalid-scope', 'Scope must be workspace or catalog');
  }
  return scope;
}

function validateLimits(limits = DEFAULT_LIMITS) {
  if (!limits || typeof limits !== 'object' || Array.isArray(limits)
    || Object.keys(limits).sort().join() !== 'maxEdges,maxNodes,maxSteps'
    || Object.values(limits).some(v => !Number.isSafeInteger(v) || v < 1 || v > 8192)) {
    throw serviceError(400, 'invalid-limits', 'Limits require bounded positive maxNodes, maxEdges and maxSteps');
  }
  return { maxNodes: limits.maxNodes, maxEdges: limits.maxEdges, maxSteps: limits.maxSteps };
}

function validateLocator(locator) {
  if (!Array.isArray(locator) || locator.length !== 4
    || locator.some(part => typeof part !== 'string' || part.length > 256)) {
    throw serviceError(400, 'invalid-locator', 'Locator must be a 4-string structural tuple [role, label, tag, inputType]');
  }
  const [, label, , inputType] = locator;
  if (!label.trim()) {
    throw serviceError(400, 'unnamed-target-rejected', 'Structural locator requires a non-empty label');
  }
  if (FORBIDDEN_INPUT_TYPES.has(inputType.toLowerCase())) {
    throw serviceError(400, 'forbidden-target-rejected', `Input type ${inputType} cannot be stored in recipes`);
  }
  return locator;
}

function validateRawStep(step, index) {
  if (!step || typeof step !== 'object' || Array.isArray(step)) {
    throw serviceError(400, 'invalid-step', `Step ${index} must be an object`);
  }
  for (const key of Object.keys(step)) {
    if (!ALLOWED_STEP_KEYS.has(key)) {
      throw serviceError(400, 'pii-or-unknown-field-rejected',
        `Step ${index} contains disallowed field "${key}"; raw values, selectors and URLs are forbidden`);
    }
  }
  if (!HASH_RE.test(step.beforeOutline) || !HASH_RE.test(step.afterOutline)) {
    throw serviceError(400, 'invalid-outline-hash', `Step ${index} requires 64-hex beforeOutline and afterOutline`);
  }
  if (!KINDS.has(step.kind)) {
    throw serviceError(400, 'invalid-step-kind', `Step ${index} kind must be fill, select or click`);
  }
  const locator = validateLocator(step.locator);
  let slot = null;
  if (step.kind === 'click') {
    if (step.slot !== undefined && step.slot !== null) {
      throw serviceError(400, 'invalid-click-slot', `Click step ${index} must not declare a slot`);
    }
  } else {
    slot = validateIdentifier(step.slot, 'slot');
  }
  const beforeSlots = step.beforeSlots === undefined ? null : step.beforeSlots;
  if (beforeSlots !== null && (!Array.isArray(beforeSlots) || beforeSlots.some(s => typeof s !== 'string' || !IDENT_RE.test(s)))) {
    throw serviceError(400, 'invalid-before-slots', `Step ${index} beforeSlots must be slot identifiers`);
  }
  const beforeClicks = step.beforeClicks ?? null;
  if (beforeClicks !== null && (!Number.isSafeInteger(beforeClicks) || beforeClicks < 0 || beforeClicks > 64)) {
    throw serviceError(400, 'invalid-before-clicks', `Step ${index} beforeClicks must be a non-negative integer`);
  }
  const elapsedMs = step.elapsedMs ?? 0;
  if (typeof elapsedMs !== 'number' || !Number.isFinite(elapsedMs) || elapsedMs < 0 || elapsedMs > 300000) {
    throw serviceError(400, 'invalid-elapsed-ms', `Step ${index} elapsedMs out of bounds`);
  }
  const outcome = step.outcome ?? 'completed';
  if (outcome !== 'completed' && outcome !== 'miss') {
    throw serviceError(400, 'invalid-step-outcome', `Step ${index} outcome must be completed or miss`);
  }
  return {
    beforeOutline: step.beforeOutline,
    afterOutline: step.afterOutline,
    kind: step.kind,
    locator,
    slot,
    beforeSlots: beforeSlots ? [...new Set(beforeSlots)].sort() : null,
    beforeClicks,
    elapsedMs,
    outcome,
  };
}

function computeStateNodeId(dagKey, { template, origin, readScope = null, outlineHash, slotNames, sameOutlineClicks }) {
  const sortedSlotHashes = [...new Set(slotNames.map(slot => dagHash(dagKey, ['slot', slot])))].sort();
  const baseScope = [template, origin, readScope];
  const stateKey = ['state-v3', sortedSlotHashes, sameOutlineClicks];
  return {
    nodeId: dagHash(dagKey, [baseScope, stateKey, outlineHash]),
    sortedSlots: [...new Set(slotNames)].sort(),
  };
}

/** Materialize structural transitions into TraceDag v3 records and contract any intra-trace loops. */
function materializeSteps(dagKey, { template, origin, readScope = null }, validatedSteps) {
  let currentSlots = validatedSteps[0]?.beforeSlots ?? [];
  let currentClicks = validatedSteps[0]?.beforeClicks ?? 0;
  const rawRecords = [];

  for (let i = 0; i < validatedSteps.length; i++) {
    const s = validatedSteps[i];
    if (i > 0 && validatedSteps[i - 1].afterOutline !== s.beforeOutline) {
      throw serviceError(400, 'disconnected-trace-steps', `Step ${i} beforeOutline does not match prior afterOutline`);
    }
    const beforeSlots = s.beforeSlots ?? currentSlots;
    const beforeClicks = s.beforeClicks ?? currentClicks;
    const beforeNode = computeStateNodeId(dagKey, {
      template, origin, readScope, outlineHash: s.beforeOutline,
      slotNames: beforeSlots, sameOutlineClicks: beforeClicks,
    });

    let afterSlots;
    let afterClicks;
    if (s.afterOutline !== s.beforeOutline) {
      afterSlots = [];
      afterClicks = 0;
    } else if (s.kind === 'click') {
      afterSlots = beforeNode.sortedSlots;
      afterClicks = beforeClicks + 1;
    } else {
      afterSlots = [...new Set([...beforeNode.sortedSlots, s.slot])].sort();
      afterClicks = beforeClicks;
    }
    const afterNode = computeStateNodeId(dagKey, {
      template, origin, readScope, outlineHash: s.afterOutline,
      slotNames: afterSlots, sameOutlineClicks: afterClicks,
    });

    const stepObj = {
      kind: s.kind,
      locator: dagHash(dagKey, ['locator', s.locator]),
      slot: s.kind === 'click' ? null : dagHash(dagKey, ['slot', s.slot]),
    };

    rawRecords.push({
      id: beforeNode.nodeId,
      depth: i,
      step: stepObj,
      next: afterNode.nodeId,
      meta: {
        beforeOutline: s.beforeOutline,
        beforeSlots: beforeNode.sortedSlots,
        beforeClicks,
        afterOutline: s.afterOutline,
        afterSlots: afterNode.sortedSlots,
        afterClicks,
        kind: s.kind,
        locator: s.locator,
        slot: s.slot,
        elapsedMs: s.elapsedMs,
        outcome: s.outcome,
      },
    });
    currentSlots = afterNode.sortedSlots;
    currentClicks = afterClicks;
  }

  const last = rawRecords.at(-1);
  const terminal = last.meta.outcome === 'completed'
    ? { id: last.next, depth: rawRecords.length }
    : null;
  const compressed = compressTraceRecords(rawRecords, terminal);
  return { records: compressed.records, terminal: compressed.terminal, contractedSteps: compressed.contractedSteps };
}

function empiricalEdgeWeight(edgeRow, replanPenalty = DEFAULT_REPLAN_PENALTY) {
  const attempts = Math.max(1, Number(edgeRow.attempts ?? 1));
  const completions = Math.min(attempts, Math.max(0, Number(edgeRow.completions ?? 1)));
  const avgMs = Math.max(0, Number(edgeRow.total_cost_ms ?? 0)) / attempts;
  const latencyTieBreaker = 1e-3 * Math.min(1, avgMs / 10000);
  const missRate = (attempts - completions) / attempts;
  return Number((1 + latencyTieBreaker + missRate * replanPenalty).toFixed(6));
}

export function createManagedRecipeEngine({
  store,
  secret,
  catalogQuorum = 2,
  replanPenalty = DEFAULT_REPLAN_PENALTY,
}) {
  if (!store) throw Error('Recipe store adapter is required');
  if (typeof secret !== 'string' || secret.length < 32) {
    throw Error('Managed recipe engine requires a >=32-character secret');
  }
  if (!Number.isSafeInteger(catalogQuorum) || catalogQuorum < 1) {
    throw Error('catalogQuorum must be a positive integer');
  }

  function resolveNamespaceMeta(principal, { scope, origin, template, readScope = null }) {
    const validScope = validateScope(scope);
    const validOrigin = validateOrigin(origin);
    const validTemplate = validateIdentifier(template, 'template');
    const normalizedReadScope = readScope === null || readScope === undefined
      ? null
      : validateIdentifier(readScope, 'readScope');
    const workspaceOwner = validScope === 'catalog' ? 'shared-catalog' : principal.workspaceId;
    const namespaceId = sha256Hex(canonicalJson([
      'fawn-recipe-ns-v1',
      validScope,
      workspaceOwner,
      validOrigin,
      validTemplate,
      normalizedReadScope,
    ]));
    const dagKey = hmacHex(secret, canonicalJson(['fawn-recipe-key-v1', namespaceId]));
    return {
      namespaceId,
      scope: validScope,
      workspaceOwner,
      origin: validOrigin,
      template: validTemplate,
      readScope: normalizedReadScope,
      dagKey,
    };
  }

  function signEnvelope(payload) {
    return hmacHex(secret, canonicalJson(['fawn-recipe-envelope-v1', payload]));
  }

  async function ensureNamespaceRow(meta, now) {
    const existing = await store.get(
      'SELECT namespace_id, revision, dag_key FROM recipe_namespaces WHERE namespace_id = ?',
      [meta.namespaceId],
    );
    if (existing) return Number(existing.revision);
    await store.run(
      `INSERT INTO recipe_namespaces
        (namespace_id, scope_kind, workspace_id, origin, template, read_scope, dag_key, revision, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)`,
      [meta.namespaceId, meta.scope, meta.workspaceOwner, meta.origin, meta.template, meta.readScope, meta.dagKey, now],
    );
    return 0;
  }

  async function loadGraphAndReduce(meta, limits = DEFAULT_LIMITS, { promotedOnly = false, persistReduction = false } = {}) {
    const nodeRows = await store.all(
      'SELECT * FROM recipe_nodes WHERE namespace_id = ?',
      [meta.namespaceId],
    );
    const edgeRows = await store.all(
      promotedOnly
        ? 'SELECT * FROM recipe_edges WHERE namespace_id = ? AND promoted = 1'
        : 'SELECT * FROM recipe_edges WHERE namespace_id = ?',
      [meta.namespaceId],
    );

    const candidateNodes = new Map();
    for (const row of nodeRows) {
      candidateNodes.set(row.node_id, {
        depth: Number(row.depth ?? 0),
        edges: [],
        repairs: [],
        terminal: Boolean(row.is_terminal),
      });
    }
    const edgeByKey = new Map();
    for (const row of edgeRows) {
      if (!candidateNodes.has(row.from_node) || !candidateNodes.has(row.to_node)) continue;
      const step = {
        kind: row.step_kind,
        locator: dagHash(meta.dagKey, ['locator', JSON.parse(row.locator_json)]),
        slot: row.step_kind === 'click' ? null : dagHash(meta.dagKey, ['slot', row.slot_name]),
      };
      const weight = empiricalEdgeWeight(row, replanPenalty);
      candidateNodes.get(row.from_node).edges.push({
        next: row.to_node,
        step,
        weight,
      });
      edgeByKey.set(`${row.from_node}->${row.to_node}:${canonicalJson(step)}`, row.edge_key);
    }

    if (candidateNodes.size === 0) {
      return {
        nodes: new Map(),
        stats: { deadNodesRemoved: 0, deadEdgesRemoved: 0, detourEdgesRemoved: 0, detourNodesRemoved: 0 },
      };
    }

    const reduced = reduceTraceGraph(candidateNodes, limits, {
      pruneDeadEnds: true,
      pruneDetours: true,
    });
    const inDeg = new Map([...reduced.nodes.keys()].map(id => [id, 0]));
    for (const node of reduced.nodes.values()) {
      for (const edge of node.edges) inDeg.set(edge.next, (inDeg.get(edge.next) ?? 0) + 1);
      for (const next of node.repairs ?? []) inDeg.set(next, (inDeg.get(next) ?? 0) + 1);
    }
    for (const [id, node] of [...reduced.nodes.entries()]) {
      if ((inDeg.get(id) ?? 0) === 0 && node.edges.length === 0 && (node.repairs?.length ?? 0) === 0) {
        reduced.nodes.delete(id);
      }
    }

    if (persistReduction && !promotedOnly) {
      const survivingNodeIds = new Set(reduced.nodes.keys());
      const survivingEdgeKeys = new Set();
      for (const [id, node] of reduced.nodes) {
        for (const edge of node.edges) {
          const k = edgeByKey.get(`${id}->${edge.next}:${canonicalJson(edge.step)}`);
          if (k) survivingEdgeKeys.add(k);
        }
      }
      const cleanup = [];
      for (const row of nodeRows) {
        if (!survivingNodeIds.has(row.node_id)) {
          cleanup.push({
            sql: 'DELETE FROM recipe_nodes WHERE namespace_id = ? AND node_id = ?',
            params: [meta.namespaceId, row.node_id],
          });
        } else {
          const rNode = reduced.nodes.get(row.node_id);
          cleanup.push({
            sql: 'UPDATE recipe_nodes SET depth = ?, is_terminal = ? WHERE namespace_id = ? AND node_id = ?',
            params: [rNode.depth, rNode.terminal ? 1 : 0, meta.namespaceId, row.node_id],
          });
        }
      }
      for (const row of edgeRows) {
        if (!survivingEdgeKeys.has(row.edge_key)) {
          cleanup.push({
            sql: 'DELETE FROM recipe_edges WHERE namespace_id = ? AND edge_key = ?',
            params: [meta.namespaceId, row.edge_key],
          });
        }
      }
      if (cleanup.length) await store.batch(cleanup);
    }

    return reduced;
  }

  async function upsertMaterializedRecords(meta, materialized, {
    authorHash,
    forcePromote = false,
    clearIntermediateTerminals = new Set(),
    runReduction = true,
    limits = DEFAULT_LIMITS,
    now = new Date().toISOString(),
  }) {
    await ensureNamespaceRow(meta, now);
    const statements = [];

    for (const record of materialized.records) {
      const m = record.meta;
      const beforeTerminal = clearIntermediateTerminals.has(record.id) ? 0 : 0;
      const afterIsTerminal = materialized.terminal?.id === record.next ? 1 : 0;

      statements.push({
        sql: `INSERT INTO recipe_nodes
                (namespace_id, node_id, outline_hash, outline_slots_json, same_outline_clicks, depth, is_terminal)
              VALUES (?, ?, ?, ?, ?, ?, ?)
              ON CONFLICT(namespace_id, node_id) DO UPDATE SET
                is_terminal = CASE
                  WHEN ? = 1 THEN 0
                  ELSE MAX(recipe_nodes.is_terminal, excluded.is_terminal)
                END`,
        params: [
          meta.namespaceId,
          record.id,
          m.beforeOutline,
          canonicalJson(m.beforeSlots),
          m.beforeClicks,
          record.depth,
          beforeTerminal,
          clearIntermediateTerminals.has(record.id) ? 1 : 0,
        ],
      });

      statements.push({
        sql: `INSERT INTO recipe_nodes
                (namespace_id, node_id, outline_hash, outline_slots_json, same_outline_clicks, depth, is_terminal)
              VALUES (?, ?, ?, ?, ?, ?, ?)
              ON CONFLICT(namespace_id, node_id) DO UPDATE SET
                is_terminal = CASE
                  WHEN ? = 1 THEN 0
                  ELSE MAX(recipe_nodes.is_terminal, excluded.is_terminal)
                END`,
        params: [
          meta.namespaceId,
          record.next,
          m.afterOutline,
          canonicalJson(m.afterSlots),
          m.afterClicks,
          record.depth + 1,
          afterIsTerminal,
          clearIntermediateTerminals.has(record.next) ? 1 : 0,
        ],
      });

      const edgeKey = sha256Hex(canonicalJson([
        record.id,
        record.next,
        m.kind,
        m.locator,
        m.slot,
      ]));

      statements.push({
        sql: `INSERT OR IGNORE INTO recipe_edge_authors
                (namespace_id, edge_key, author_hash, created_at)
              VALUES (?, ?, ?, ?)`,
        params: [meta.namespaceId, edgeKey, authorHash, now],
      });

      const isCompleted = m.outcome === 'completed' ? 1 : 0;
      const immediatePromote = meta.scope === 'workspace' || forcePromote || catalogQuorum <= 1 ? 1 : 0;
      statements.push({
        sql: `INSERT INTO recipe_edges (
                namespace_id, edge_key, from_node, to_node,
                before_outline, before_slots_json, before_clicks,
                after_outline, after_slots_json, after_clicks,
                step_kind, locator_json, slot_name,
                attempts, completions, total_cost_ms, author_count, promoted, updated_at
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 1, ?, ?)
              ON CONFLICT(namespace_id, edge_key) DO UPDATE SET
                attempts = recipe_edges.attempts + 1,
                completions = recipe_edges.completions + ?,
                total_cost_ms = recipe_edges.total_cost_ms + ?,
                promoted = MAX(recipe_edges.promoted, ?),
                updated_at = excluded.updated_at`,
        params: [
          meta.namespaceId, edgeKey, record.id, record.next,
          m.beforeOutline, canonicalJson(m.beforeSlots), m.beforeClicks,
          m.afterOutline, canonicalJson(m.afterSlots), m.afterClicks,
          m.kind, canonicalJson(m.locator), m.slot,
          isCompleted, m.elapsedMs, immediatePromote, now,
          isCompleted, m.elapsedMs, immediatePromote,
        ],
      });

      // Recompute distinct author_count and quorum promotion cleanly.
      statements.push({
        sql: `UPDATE recipe_edges
              SET author_count = (
                    SELECT COUNT(*) FROM recipe_edge_authors
                    WHERE namespace_id = ? AND edge_key = ?
                  ),
                  promoted = CASE
                    WHEN promoted = 1 THEN 1
                    WHEN completions >= ? AND (
                      SELECT COUNT(*) FROM recipe_edge_authors
                      WHERE namespace_id = ? AND edge_key = ?
                    ) >= ? THEN 1
                    ELSE 0
                  END
              WHERE namespace_id = ? AND edge_key = ?`,
        params: [
          meta.namespaceId, edgeKey,
          catalogQuorum, meta.namespaceId, edgeKey, catalogQuorum,
          meta.namespaceId, edgeKey,
        ],
      });
    }

    await store.batch(statements);
    if (!runReduction) {
      return { revision: 0, reduced: null };
    }
    const reduced = await loadGraphAndReduce(meta, limits, {
      promotedOnly: false,
      persistReduction: true,
    });
    await store.run(
      'UPDATE recipe_namespaces SET revision = revision + 1, updated_at = ? WHERE namespace_id = ?',
      [now, meta.namespaceId],
    );
    const nsRow = await store.get(
      'SELECT revision FROM recipe_namespaces WHERE namespace_id = ?',
      [meta.namespaceId],
    );
    return {
      revision: Number(nsRow?.revision ?? 1),
      reduced,
    };
  }

  return {
    signEnvelope,
    async registerSubrecipe(principal, body) {
      if (!body || typeof body !== 'object' || Array.isArray(body)) {
        throw serviceError(400, 'invalid-body', 'JSON object required');
      }
      const scope = validateScope(body.scope ?? 'workspace');
      if (scope === 'catalog' && principal.role !== 'publisher') {
        throw serviceError(403, 'publisher-role-required', 'Catalog sub-recipe authoring requires publisher role');
      }
      const origin = validateOrigin(body.origin);
      const name = validateIdentifier(body.name, 'name');
      if (!Array.isArray(body.steps) || body.steps.length < 1 || body.steps.length > 64) {
        throw serviceError(400, 'invalid-steps', 'Sub-recipe requires 1..64 structural steps');
      }
      const steps = body.steps.map((step, index) => validateRawStep(step, index));
      if (steps.some(step => step.outcome !== 'completed')) {
        throw serviceError(400, 'invalid-subrecipe-outcome', 'Authored sub-recipe steps must have completed outcomes');
      }
      // Dry-run materialization + acyclicity check before saving.
      const tempKey = hmacHex(secret, canonicalJson(['subrecipe-validate', origin, name]));
      const materialized = materializeSteps(tempKey, { template: name, origin, readScope: null }, steps);
      const workspaceOwner = scope === 'catalog' ? 'shared-catalog' : principal.workspaceId;
      const subrecipeId = sha256Hex(canonicalJson(['fawn-subrecipe-v1', scope, workspaceOwner, origin, name]));
      const now = new Date().toISOString();
      const existing = await store.get(
        'SELECT revision FROM recipe_subrecipes WHERE subrecipe_id = ?',
        [subrecipeId],
      );
      const nextRevision = existing ? Number(existing.revision) + 1 : 1;
      await store.run(
        `INSERT INTO recipe_subrecipes
          (subrecipe_id, scope_kind, workspace_id, origin, name, entry_outline, exit_outline, steps_json, revision, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
         ON CONFLICT(subrecipe_id) DO UPDATE SET
           entry_outline = excluded.entry_outline,
           exit_outline = excluded.exit_outline,
           steps_json = excluded.steps_json,
           revision = excluded.revision,
           updated_at = excluded.updated_at`,
        [
          subrecipeId, scope, workspaceOwner, origin, name,
          steps[0].beforeOutline, steps.at(-1).afterOutline,
          canonicalJson(steps), nextRevision, now,
        ],
      );
      return {
        subrecipeId,
        scope,
        origin,
        name,
        revision: nextRevision,
        entryOutline: steps[0].beforeOutline,
        exitOutline: steps.at(-1).afterOutline,
        stepCount: materialized.records.length,
        contractedSteps: materialized.contractedSteps,
      };
    },

    async listSubrecipes(principal, { scope = 'workspace', origin }) {
      const validScope = validateScope(scope);
      const validOrigin = validateOrigin(origin);
      const workspaceOwner = validScope === 'catalog' ? 'shared-catalog' : principal.workspaceId;
      const rows = await store.all(
        `SELECT subrecipe_id, scope_kind, origin, name, entry_outline, exit_outline, revision, updated_at
         FROM recipe_subrecipes
         WHERE scope_kind = ? AND workspace_id = ? AND origin = ?
         ORDER BY name ASC`,
        [validScope, workspaceOwner, validOrigin],
      );
      return {
        scope: validScope,
        origin: validOrigin,
        subrecipes: rows.map(row => ({
          subrecipeId: row.subrecipe_id,
          name: row.name,
          entryOutline: row.entry_outline,
          exitOutline: row.exit_outline,
          revision: Number(row.revision),
          updatedAt: row.updated_at,
        })),
      };
    },

    async ingestTrace(principal, body) {
      if (!body || typeof body !== 'object' || Array.isArray(body)) {
        throw serviceError(400, 'invalid-body', 'JSON object required');
      }
      const submissionId = typeof body.submissionId === 'string' && UUID_RE.test(body.submissionId)
        ? body.submissionId
        : null;
      if (!submissionId) {
        throw serviceError(400, 'invalid-submission-id', 'Bounded submissionId is required for idempotent ingestion');
      }
      const prior = await store.get(
        'SELECT response_json FROM recipe_submissions WHERE submission_id = ?',
        [submissionId],
      );
      if (prior) return JSON.parse(prior.response_json);

      const verificationId = validateIdentifier(body.verificationId, 'verificationId');
      if (body.reviewVerified !== true) {
        throw serviceError(400, 'unverified-trace-rejected', 'Only independently reviewVerified traces may be ingested');
      }
      const limits = validateLimits(body.limits ?? DEFAULT_LIMITS);
      const meta = resolveNamespaceMeta(principal, {
        scope: body.scope ?? 'workspace',
        origin: body.origin,
        template: body.template,
        readScope: body.readScope ?? null,
      });
      if (!Array.isArray(body.steps) || body.steps.length < 1 || body.steps.length > limits.maxSteps) {
        throw serviceError(400, 'invalid-steps', `Trace steps must contain 1..${limits.maxSteps} transitions`);
      }
      const steps = body.steps.map((step, index) => validateRawStep(step, index));
      const materialized = materializeSteps(meta.dagKey, meta, steps);
      const authorHash = sha256Hex(canonicalJson(['author-v1', principal.workspaceId, principal.clientId]));
      const now = new Date().toISOString();
      const { revision, reduced } = await upsertMaterializedRecords(meta, materialized, {
        authorHash,
        forcePromote: principal.role === 'publisher',
        limits,
        now,
      });

      const stats = analyzeTraceGraph(reduced.nodes, limits);
      const response = {
        submissionId,
        namespaceId: meta.namespaceId,
        scope: meta.scope,
        origin: meta.origin,
        template: meta.template,
        revision,
        contractedSteps: materialized.contractedSteps,
        reduction: reduced.stats,
        compressionStats: stats,
      };
      await store.run(
        `INSERT INTO recipe_submissions (submission_id, namespace_id, client_id, verification_id, response_json, created_at)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [submissionId, meta.namespaceId, principal.clientId, verificationId, JSON.stringify(response), now],
      );
      return response;
    },

    async composeRecipe(principal, body) {
      if (!body || typeof body !== 'object' || Array.isArray(body)) {
        throw serviceError(400, 'invalid-body', 'JSON object required');
      }
      const scope = validateScope(body.scope ?? 'workspace');
      if (scope === 'catalog' && principal.role !== 'publisher') {
        throw serviceError(403, 'publisher-role-required', 'Composing catalog recipes requires publisher role');
      }
      const limits = validateLimits(body.limits ?? DEFAULT_LIMITS);
      const meta = resolveNamespaceMeta(principal, {
        scope,
        origin: body.origin,
        template: body.targetTemplate,
        readScope: body.readScope ?? null,
      });
      if (!Array.isArray(body.subrecipes) || body.subrecipes.length < 1 || body.subrecipes.length > 32) {
        throw serviceError(400, 'invalid-subrecipe-list', 'subrecipes must name 1..32 registered sub-recipes');
      }
      const subrecipeNames = body.subrecipes.map(name => validateIdentifier(name, 'subrecipe'));
      const workspaceOwner = scope === 'catalog' ? 'shared-catalog' : principal.workspaceId;

      const segments = [];
      for (const name of subrecipeNames) {
        let row = await store.get(
          `SELECT steps_json FROM recipe_subrecipes
           WHERE scope_kind = ? AND workspace_id = ? AND origin = ? AND name = ?`,
          [scope, workspaceOwner, meta.origin, name],
        );
        if (!row && scope === 'workspace') {
          // Allow workspace compositions to pull promoted shared-catalog building blocks too.
          row = await store.get(
            `SELECT steps_json FROM recipe_subrecipes
             WHERE scope_kind = 'catalog' AND workspace_id = 'shared-catalog' AND origin = ? AND name = ?`,
            [meta.origin, name],
          );
        }
        if (!row) {
          throw serviceError(404, 'subrecipe-not-found', `Sub-recipe "${name}" not found for ${meta.origin}`);
        }
        segments.push(JSON.parse(row.steps_json));
      }

      // Materialize each sub-recipe under targetTemplate's dagKey and clear intermediate handoff terminals.
      const materializedSegments = segments.map(steps => materializeSteps(meta.dagKey, meta, steps));
      const nonTerminalSources = new Set();
      for (let i = 1; i < materializedSegments.length; i++) {
        for (const record of materializedSegments[i].records) {
          nonTerminalSources.add(record.id);
        }
      }
      const authorHash = sha256Hex(canonicalJson(['composer-v1', principal.workspaceId, principal.clientId]));
      const now = new Date().toISOString();
      let latestResult = null;
      for (let i = 0; i < materializedSegments.length; i++) {
        const seg = materializedSegments[i];
        const handoffCleared = new Set();
        if (seg.terminal && nonTerminalSources.has(seg.terminal.id)) {
          handoffCleared.add(seg.terminal.id);
        }
        const effectiveSeg = handoffCleared.size
          ? { ...seg, terminal: null }
          : seg;
        latestResult = await upsertMaterializedRecords(meta, effectiveSeg, {
          authorHash,
          forcePromote: true,
          clearIntermediateTerminals: handoffCleared,
          runReduction: i === materializedSegments.length - 1,
          limits,
          now,
        });
      }

      const finalReduced = await loadGraphAndReduce(meta, limits, {
        promotedOnly: scope === 'catalog',
        persistReduction: true,
      });
      const stats = analyzeTraceGraph(finalReduced.nodes, limits);
      return {
        namespaceId: meta.namespaceId,
        scope: meta.scope,
        origin: meta.origin,
        template: meta.template,
        revision: latestResult?.revision ?? 1,
        composedSubrecipes: subrecipeNames,
        reduction: finalReduced.stats,
        compressionStats: stats,
      };
    },

    async resolveRecipe(principal, body) {
      if (!body || typeof body !== 'object' || Array.isArray(body)) {
        throw serviceError(400, 'invalid-body', 'JSON object required');
      }
      const limits = validateLimits(body.limits ?? DEFAULT_LIMITS);
      const meta = resolveNamespaceMeta(principal, {
        scope: body.scope ?? 'workspace',
        origin: body.origin,
        template: body.template,
        readScope: body.readScope ?? null,
      });
      const availableSlotNames = body.availableSlots === undefined
        ? null
        : body.availableSlots;
      if (availableSlotNames !== null && (!Array.isArray(availableSlotNames)
        || availableSlotNames.some(s => typeof s !== 'string' || !IDENT_RE.test(s)))) {
        throw serviceError(400, 'invalid-available-slots', 'availableSlots must be an array of slot identifiers');
      }
      const currentOutline = body.currentOutline ?? null;
      if (currentOutline !== null && !HASH_RE.test(currentOutline)) {
        throw serviceError(400, 'invalid-current-outline', 'currentOutline must be a 64-hex structural hash');
      }

      const nsRow = await store.get(
        'SELECT revision FROM recipe_namespaces WHERE namespace_id = ?',
        [meta.namespaceId],
      );
      const revision = Number(nsRow?.revision ?? 0);
      const { nodes: reducedNodes, stats: reduction } = await loadGraphAndReduce(meta, limits, {
        promotedOnly: meta.scope === 'catalog',
        persistReduction: false,
      });

      const availableSlotHashes = availableSlotNames === null
        ? null
        : new Set(availableSlotNames.map(slot => dagHash(meta.dagKey, ['slot', slot])));

      const dp = reducedNodes.size > 0
        ? solveRecipeDp(reducedNodes, limits, { availableSlots: availableSlotHashes, replanPenalty })
        : { values: new Map(), policy: new Map() };
      const compressionStats = reducedNodes.size > 0
        ? analyzeTraceGraph(reducedNodes, limits)
        : {
          nodeCount: 0, edgeCount: 0, repairBridgeCount: 0, terminalCount: 0,
          sharedMergeNodes: 0, confluentDiamonds: 0, maxDepth: 0, optimalRootCosts: {},
        };

      let entryNodeId = null;
      let entryOptimalCost = null;
      if (currentOutline) {
        const entry = computeStateNodeId(meta.dagKey, {
          template: meta.template,
          origin: meta.origin,
          readScope: meta.readScope,
          outlineHash: currentOutline,
          slotNames: body.currentFilledSlots ?? [],
          sameOutlineClicks: 0,
        });
        if (reducedNodes.has(entry.nodeId)) {
          entryNodeId = entry.nodeId;
          const val = dp.values.get(entry.nodeId);
          entryOptimalCost = Number.isFinite(val) ? val : null;
        }
      }

      const dag = {
        version: VERSION,
        key: meta.dagKey,
        limits,
        nodes: [...reducedNodes.entries()],
      };
      const dagDigest = sha256Hex(canonicalJson(dag));
      const signature = signEnvelope({
        namespaceId: meta.namespaceId,
        scope: meta.scope,
        origin: meta.origin,
        template: meta.template,
        revision,
        dagDigest,
      });

      return {
        namespaceId: meta.namespaceId,
        scope: meta.scope,
        origin: meta.origin,
        template: meta.template,
        revision,
        dag,
        dagDigest,
        signature,
        reduction,
        compressionStats,
        entryLookup: currentOutline ? { currentOutline, entryNodeId, entryOptimalCost } : null,
      };
    },
  };
}
