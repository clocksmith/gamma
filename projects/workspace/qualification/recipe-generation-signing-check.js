import { ManagedRecipeClient } from '../src/client/recipe-client.js';
import { PinnedRecipeGenerationCache } from '../src/client/pinned-recipe-cache.js';

/** Verify one existing generation using out-of-band namespace, generation and
 * publisher policy. This only reads; it never seeds a DB or enables a signer. */
export async function checkRecipeGenerationSigning({ url, token, scope, generation, trust,
  fetchImpl = globalThis.fetch, clock = Date.now }) {
  if (!Number.isSafeInteger(generation) || generation < 1 || trust?.minimumGeneration !== generation) {
    throw new TypeError('Qualification requires a positive exact generation and matching replay floor');
  }
  const client = new ManagedRecipeClient({
    url, token, fetchImpl: async (target, options) => {
      const response = await fetchImpl(target, {
        ...options, redirect: 'error', signal: AbortSignal.timeout(10_000),
      });
      if (response.ok && response.headers.get('cache-control') !== 'private, no-store') {
        throw Error('Signed generation response must be private and no-store');
      }
      return response;
    },
  });
  const cache = new PinnedRecipeGenerationCache({ maxEntries: 1 });
  const { cached, pin } = await client.fetchPinnedGeneration({
    ...scope, generation, trust, cache, clock,
  });
  if (!cached || !cache.getSigned(pin, { ...trust, now: clock() })) {
    throw Error('Signed generation was not admitted by the verified cache');
  }
  return { signedHttpVerification: true, generation };
}
