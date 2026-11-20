import { Buffer } from 'node:buffer';
import { verify } from 'node:crypto';
import { canonicalJson } from './trace-graph-dp.js';
import { recipePublicationDigest, sha256 } from './recipe-generation-format.js';

export const RECIPE_MANIFEST_V1 = 'gamma.recipe-publication-manifest/v1';
export const MAX_MANIFEST_VALID_MS = 24 * 60 * 60 * 1000;
const FORMAT_FIELDS = 'algorithm,compilerVersion,expiresAt,format,generation,generationDigest,inputWatermark,issuedAt,keyId,limits,namespaceId,replanPenalty,snapshotDigest';
const HEX = /^[a-f0-9]{64}$/;
const SIGNATURE = /^[a-f0-9]{128}$/;
const VERSION = /^[a-zA-Z0-9._:/+-]{1,128}$/;
const exactKeys = (value, keys) => value !== null && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).sort().join(',') === keys;
const digest = value => typeof value === 'string' && HEX.test(value);
const integer = (value, min, max = Number.MAX_SAFE_INTEGER) =>
  Number.isSafeInteger(value) && value >= min && value <= max;
const limitsValid = value => exactKeys(value, 'maxEdges,maxNodes,maxSteps')
  && Object.values(value).every(n => integer(n, 1, 8192));
const penaltyValid = value => typeof value === 'number' && Number.isFinite(value) && value >= 0;
const versionValid = value => typeof value === 'string' && VERSION.test(value);
const failure = (code, message) => Object.assign(Error(message), { code });

export function recipeManifestKeyId(publicKey) {
  if (publicKey?.type !== 'public' || publicKey.asymmetricKeyType !== 'ed25519') {
    throw new TypeError('Recipe manifest trust requires an Ed25519 public KeyObject');
  }
  return sha256(publicKey.export({ type: 'spki', format: 'der' }));
}

export function encodeRecipeManifest(manifest) {
  if (!exactKeys(manifest, FORMAT_FIELDS) || manifest.format !== RECIPE_MANIFEST_V1 ||
      manifest.algorithm !== 'Ed25519' || !digest(manifest.keyId) || !digest(manifest.namespaceId) ||
      !integer(manifest.generation, 1) || !integer(manifest.inputWatermark, 1) ||
      !versionValid(manifest.compilerVersion) || !digest(manifest.snapshotDigest) ||
      !digest(manifest.generationDigest) || !limitsValid(manifest.limits) ||
      !penaltyValid(manifest.replanPenalty) || !integer(manifest.issuedAt, 0) ||
      !integer(manifest.expiresAt, 1) || manifest.expiresAt <= manifest.issuedAt ||
      manifest.expiresAt - manifest.issuedAt > MAX_MANIFEST_VALID_MS ||
      recipePublicationDigest(manifest) !== manifest.generationDigest) {
    throw failure('invalid-recipe-manifest', 'Invalid recipe manifest fields, validity interval or publication digest');
  }
  return Buffer.from(canonicalJson(manifest), 'utf8');
}

/**
 * Verify a detached manifest with a locally configured publisher key. Policy,
 * namespace, clock and replay floor are local trust inputs, not envelope data.
 * The result is a snapshot cache pin, never an execution authorization.
 */
export function verifySignedRecipeManifest(packet, {
  publicKey, namespaceId, compilerVersion, limits, replanPenalty,
  minimumGeneration, now,
} = {}) {
  if (!digest(namespaceId) || !versionValid(compilerVersion) || !limitsValid(limits) ||
      !penaltyValid(replanPenalty) || !integer(minimumGeneration, 0) || !integer(now, 0)) {
    throw failure('invalid-recipe-trust-policy', 'Explicit namespace, route policy, clock and generation floor required');
  }
  const trustedKeyId = recipeManifestKeyId(publicKey);
  if (!exactKeys(packet, 'manifest,signature') ||
      typeof packet.signature !== 'string' || !SIGNATURE.test(packet.signature)) {
    throw failure('invalid-recipe-manifest-envelope', 'Malformed detached recipe signature envelope');
  }
  const { manifest } = packet;
  const bytes = encodeRecipeManifest(manifest);
  if (manifest.keyId !== trustedKeyId ||
      !verify(null, bytes, publicKey, Buffer.from(packet.signature, 'hex'))) {
    throw failure('recipe-signature-rejected', 'Recipe publisher key or signature did not match');
  }
  if (manifest.namespaceId !== namespaceId || manifest.compilerVersion !== compilerVersion ||
      canonicalJson(manifest.limits) !== canonicalJson(limits) || manifest.replanPenalty !== replanPenalty) {
    throw failure('recipe-manifest-scope-mismatch', 'Recipe manifest did not match the local namespace and route policy');
  }
  if (now < manifest.issuedAt || now >= manifest.expiresAt ||
      manifest.generation < minimumGeneration) {
    throw failure('stale-recipe-manifest', 'Recipe manifest is outside the validity window or local replay floor');
  }
  return {
    namespaceId,
    generation: manifest.generation,
    generationDigest: manifest.generationDigest,
    compilerVersion,
    limits: { ...limits },
    replanPenalty,
    minimumGeneration,
  };
}
