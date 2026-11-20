import { Buffer } from 'node:buffer';
import { canonicalJson } from './trace-graph-dp.js';
import { TraceDag } from './trace-dag.js';
import { MAX_RECIPE_SNAPSHOT_BYTES, recipePublicationDigest, sha256 } from './recipe-generation-format.js';

const HASH = /^[a-f0-9]{64}$/;
const VERSION = /^[a-zA-Z0-9._:/+-]{1,128}$/;
const HASH_PLACEHOLDER = '0'.repeat(64);
const exactKeys = (value, keys) => value !== null && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).sort().join(',') === keys;
const digest = value => typeof value === 'string' && HASH.test(value);
const integer = (value, min, max = Number.MAX_SAFE_INTEGER) =>
  Number.isSafeInteger(value) && value >= min && value <= max;
const validLimits = limits => exactKeys(limits, 'maxEdges,maxNodes,maxSteps')
  && Object.values(limits).every(value => integer(value, 1, 8192));
const validVersion = value => typeof value === 'string' && VERSION.test(value);
const validPenalty = value => typeof value === 'number' && Number.isFinite(value) && value >= 0;
const pinError = (code, message) => Object.assign(Error(message), { code });

function cacheKey(pin) {
  if (!pin || !digest(pin.namespaceId) || !integer(pin.generation, 1) ||
      !digest(pin.generationDigest) || !validVersion(pin.compilerVersion) ||
      !validLimits(pin.limits) || !validPenalty(pin.replanPenalty) ||
      !integer(pin.minimumGeneration ?? 0, 0)) {
    throw pinError('invalid-generation-pin', 'A trusted generation and route policy pin are required');
  }
  if (pin.generation < (pin.minimumGeneration ?? 0)) {
    throw pinError('stale-generation-pin', 'Pinned recipe generation is below the required freshness floor');
  }
  return canonicalJson([pin.namespaceId, pin.generation, pin.generationDigest,
    pin.compilerVersion, pin.limits, pin.replanPenalty]);
}

function serializeValidated(packet, pin) {
  cacheKey(pin);
  if (!exactKeys(packet, 'receipt,snapshot')) {
    throw pinError('invalid-generation-packet', 'Invalid pinned recipe generation packet');
  }
  const { receipt, snapshot } = packet;
  if (!exactKeys(receipt, 'compilerVersion,generation,generationDigest,inputWatermark,namespaceId,publishedAt,snapshotDigest') ||
      receipt.namespaceId !== pin.namespaceId || receipt.generation !== pin.generation ||
      receipt.compilerVersion !== pin.compilerVersion || receipt.generationDigest !== pin.generationDigest ||
      !integer(receipt.inputWatermark, 1) || !digest(receipt.snapshotDigest) ||
      typeof receipt.publishedAt !== 'string' || receipt.publishedAt.length > 64 ||
      !Number.isFinite(Date.parse(receipt.publishedAt))) {
    throw pinError('generation-pin-mismatch', 'Recipe generation does not match the local pin');
  }
  if (!exactKeys(snapshot, 'inputDigest,limits,nodes,reduction,replanPenalty,version') ||
      snapshot.version !== 3 || !digest(snapshot.inputDigest) ||
      canonicalJson(snapshot.limits) !== canonicalJson(pin.limits) ||
      snapshot.replanPenalty !== pin.replanPenalty || !Array.isArray(snapshot.nodes) ||
      snapshot.nodes.length > pin.limits.maxNodes ||
      !exactKeys(snapshot.reduction, 'deadEdgesRemoved,deadNodesRemoved,detourEdgesRemoved,detourNodesRemoved') ||
      !Object.values(snapshot.reduction).every(value => integer(value, 0))) {
    throw pinError('generation-policy-mismatch', 'Recipe generation has an incompatible graph or route policy');
  }
  const snapshotJson = canonicalJson(snapshot);
  if (Buffer.byteLength(snapshotJson) > MAX_RECIPE_SNAPSHOT_BYTES) {
    throw pinError('generation-snapshot-too-large', 'Recipe generation snapshot exceeds the byte limit');
  }
  if (sha256(snapshotJson) !== receipt.snapshotDigest || recipePublicationDigest(receipt) !== receipt.generationDigest) {
    throw pinError('generation-digest-mismatch', 'Recipe generation metadata or content digest differs');
  }
  // Reuse the production structural validator without exporting its replay
  // object or the real namespace key. The placeholder never leaves validation.
  TraceDag.restore({ version: 3, key: HASH_PLACEHOLDER, limits: pin.limits, nodes: snapshot.nodes }, pin.limits);
  return canonicalJson({ receipt, snapshot });
}

/**
 * Validate data against an independent pin already trusted by the caller.
 * The unkeyed digest is integrity checking, not publisher authentication.
 * Returns detached JSON data only: no DAG replay object, key, or authority.
 */
export function validatePinnedRecipeGeneration(packet, pin) {
  return JSON.parse(serializeValidated(packet, pin));
}

export class PinnedRecipeGenerationCache {
  #entries = new Map();
  #bytes = 0;
  #maxEntries;
  #maxBytes;

  constructor({ maxEntries = 16, maxBytes = 4 * MAX_RECIPE_SNAPSHOT_BYTES } = {}) {
    if (!integer(maxEntries, 1, 1024) || !integer(maxBytes, 1, 64 * MAX_RECIPE_SNAPSHOT_BYTES)) {
      throw new TypeError('Invalid recipe cache bounds');
    }
    this.#maxEntries = maxEntries;
    this.#maxBytes = maxBytes;
  }

  get size() { return this.#entries.size; }
  get bytes() { return this.#bytes; }

  get(pin) {
    const key = cacheKey(pin);
    const stored = this.#entries.get(key);
    if (!stored) return null;
    this.#entries.delete(key);
    this.#entries.set(key, stored);
    return JSON.parse(stored.json);
  }

  put(packet, pin) {
    const key = cacheKey(pin);
    const json = serializeValidated(packet, pin);
    const bytes = Buffer.byteLength(key) + Buffer.byteLength(json);
    if (bytes > this.#maxBytes) return false;
    const previous = this.#entries.get(key);
    if (previous) {
      this.#bytes -= previous.bytes;
      this.#entries.delete(key);
    }
    while (this.#entries.size >= this.#maxEntries || this.#bytes + bytes > this.#maxBytes) {
      const oldest = this.#entries.keys().next().value;
      this.#bytes -= this.#entries.get(oldest).bytes;
      this.#entries.delete(oldest);
    }
    this.#entries.set(key, { json, bytes });
    this.#bytes += bytes;
    return true;
  }
}
