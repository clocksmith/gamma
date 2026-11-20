import { createHash } from 'node:crypto';
import { canonicalJson } from './trace-graph-dp.js';

export const MAX_RECIPE_SNAPSHOT_BYTES = 1024 * 1024;
export const sha256 = text => createHash('sha256').update(text).digest('hex');
export const recipePublicationDigest = ({ namespaceId, generation, inputWatermark, compilerVersion, snapshotDigest }) =>
  sha256(canonicalJson(['gamma.recipe-generation/v1', namespaceId, generation, inputWatermark, compilerVersion, snapshotDigest]));
