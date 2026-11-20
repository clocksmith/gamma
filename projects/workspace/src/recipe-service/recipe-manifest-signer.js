import { Buffer } from 'node:buffer';
import { createPublicKey, sign } from 'node:crypto';
import { canonicalJson } from '../client/trace-graph-dp.js';
import { MAX_RECIPE_SNAPSHOT_BYTES, sha256 } from '../client/recipe-generation-format.js';
import { encodeRecipeManifest, recipeManifestKeyId, RECIPE_MANIFEST_V1 } from '../client/signed-recipe-manifest.js';

/**
 * Sign metadata for a locally trusted immutable generation read. Key
 * provisioning and authorization are deliberately out of scope. Never use
 * this helper to bless a caller-provided graph at an HTTP boundary.
 */
export function signRecipeGenerationManifest({ packet, privateKey, issuedAt, expiresAt } = {}) {
  if (privateKey?.type !== 'private' || privateKey.asymmetricKeyType !== 'ed25519') {
    throw new TypeError('Recipe publisher requires an injected Ed25519 private KeyObject');
  }
  const { receipt, snapshot } = packet ?? {};
  if (!receipt || snapshot?.version !== 3) throw TypeError('Expected immutable workspace recipe generation');
  const snapshotJson = canonicalJson(snapshot);
  if (Buffer.byteLength(snapshotJson) > MAX_RECIPE_SNAPSHOT_BYTES ||
      sha256(snapshotJson) !== receipt.snapshotDigest) {
    throw Error('Stored recipe snapshot failed integrity check');
  }
  const manifest = {
    format: RECIPE_MANIFEST_V1,
    algorithm: 'Ed25519',
    keyId: recipeManifestKeyId(createPublicKey(privateKey)),
    namespaceId: receipt.namespaceId,
    generation: receipt.generation,
    inputWatermark: receipt.inputWatermark,
    compilerVersion: receipt.compilerVersion,
    snapshotDigest: receipt.snapshotDigest,
    generationDigest: receipt.generationDigest,
    limits: { ...snapshot.limits },
    replanPenalty: snapshot.replanPenalty,
    issuedAt,
    expiresAt,
  };
  const signature = sign(null, encodeRecipeManifest(manifest), privateKey).toString('hex');
  return { manifest, signature };
}
