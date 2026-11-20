import { Buffer } from 'node:buffer';
import { createHash } from 'node:crypto';
import { canonicalJson } from '../client/trace-graph-dp.js';

const HEX = /^[a-f0-9]{64}$/;
const VERSION = /^[a-zA-Z0-9._:/+-]{1,128}$/;
const MAX_SNAPSHOT_BYTES = 1024 * 1024;
const sha256 = text => createHash('sha256').update(text).digest('hex');
const publicationDigest = ({ namespaceId, generation, inputWatermark, compilerVersion, snapshotDigest }) =>
  sha256(canonicalJson(['gamma.recipe-generation/v1', namespaceId, generation, inputWatermark, compilerVersion, snapshotDigest]));

function validateNamespace(namespaceId) {
  if (typeof namespaceId !== 'string' || !HEX.test(namespaceId)) throw new TypeError('Invalid recipe generation namespace');
}

function pinnedRecord(row) {
  if (!row) return null;
  const receipt = {
    namespaceId: row.namespace_id,
    generation: Number(row.generation),
    inputWatermark: Number(row.input_watermark),
    compilerVersion: row.compiler_version,
    snapshotDigest: row.snapshot_digest,
    generationDigest: row.generation_digest,
    publishedAt: row.published_at,
  };
  if (sha256(row.snapshot_json) !== receipt.snapshotDigest ||
      publicationDigest(receipt) !== receipt.generationDigest) {
    throw Error('Recipe generation failed integrity verification');
  }
  return { receipt, snapshot: JSON.parse(row.snapshot_json) };
}

const FIELDS = 'namespace_id, generation, input_watermark, compiler_version, snapshot_digest, generation_digest, snapshot_json, published_at';

/**
 * Internal snapshot storage, not the HTTP resolver or a compiler. The supplied
 * namespace is derived by the authenticated caller. A future compactor must
 * prove its snapshot came from the ordered input through the claimed watermark.
 */
export function createRecipeGenerationStore(store) {
  async function readGeneration(namespaceId, generation) {
    validateNamespace(namespaceId);
    if (!Number.isSafeInteger(generation) || generation < 1) throw new TypeError('Invalid recipe generation');
    return pinnedRecord(await store.get(
      `SELECT ${FIELDS} FROM recipe_graph_generations WHERE namespace_id = ? AND generation = ?`,
      [namespaceId, generation],
    ));
  }

  async function readHead(namespaceId) {
    validateNamespace(namespaceId);
    return pinnedRecord(await store.get(
      `SELECT ${FIELDS} FROM recipe_graph_generations WHERE namespace_id = ? ORDER BY generation DESC LIMIT 1`,
      [namespaceId],
    ));
  }

  async function publish({ namespaceId, expectedGeneration, inputWatermark, compilerVersion, snapshot }) {
    validateNamespace(namespaceId);
    if (!Number.isSafeInteger(expectedGeneration) || expectedGeneration < 0 ||
        expectedGeneration === Number.MAX_SAFE_INTEGER ||
        !Number.isSafeInteger(inputWatermark) || inputWatermark < 1 ||
        typeof compilerVersion !== 'string' || !VERSION.test(compilerVersion) ||
        snapshot === null || typeof snapshot !== 'object' || Array.isArray(snapshot)) {
      throw new TypeError('Invalid recipe generation publication');
    }
    const snapshotJson = canonicalJson(snapshot);
    if (Buffer.byteLength(snapshotJson) > MAX_SNAPSHOT_BYTES) throw new RangeError('Recipe snapshot exceeds byte limit');
    JSON.parse(snapshotJson); // Reject non-JSON before writing immutable bytes.
    const snapshotDigest = sha256(snapshotJson);
    const generation = expectedGeneration + 1;
    const digest = publicationDigest({ namespaceId, generation, inputWatermark, compilerVersion, snapshotDigest });

    // The head and its bytes are the same immutable row. CAS, watermark checks
    // and publication run in one statement on both SQLite and D1.
    await store.run(
      `INSERT INTO recipe_graph_generations (${FIELDS})
       SELECT ?, ?, ?, ?, ?, ?, ?, ?
       WHERE ? = COALESCE((
         SELECT generation FROM recipe_graph_generations
         WHERE namespace_id = ? ORDER BY generation DESC LIMIT 1
       ), 0)
       AND ? > COALESCE((
         SELECT input_watermark FROM recipe_graph_generations
         WHERE namespace_id = ? ORDER BY generation DESC LIMIT 1
       ), 0)
       AND EXISTS (
         SELECT 1 FROM recipe_trace_acceptance WHERE namespace_id = ? AND acceptance_seq = ?
       )
       ON CONFLICT (namespace_id, generation) DO NOTHING`,
      [namespaceId, generation, inputWatermark, compilerVersion, snapshotDigest, digest,
        snapshotJson, new Date().toISOString(), expectedGeneration, namespaceId, inputWatermark,
        namespaceId, namespaceId, inputWatermark],
    );
    const pinned = await readGeneration(namespaceId, generation);
    // Allow an exact retry to get its original record, even if the head
    // subsequently moved. Its receipt describes a generation, never 'latest'.
    if (pinned?.receipt.generationDigest === digest) return pinned.receipt;
    throw Object.assign(Error('Recipe publication base or input watermark changed'), {
      status: 409, code: 'recipe-generation-conflict',
    });
  }

  return { publish, readGeneration, readHead };
}
