// Deploy only with a new, isolated staging D1. Never import from production.
import { createHash, createPrivateKey, timingSafeEqual } from 'node:crypto';
import { createD1RecipeStore } from '../src/recipe-service/store-d1.js';
import { createManagedRecipeEngine } from '../src/recipe-service/engine.js';
import { createManagedRecipeHttpHandler } from '../src/recipe-service/http-handler.js';
import { signRecipeGenerationManifest } from '../src/recipe-service/recipe-manifest-signer.js';
import { qualifyRecipeGenerationCorpus } from './recipe-generation-corpus.js';

export const principal = { workspaceId: 'staging-synthetic', clientId: 'fixture', role: 'member' };
export const foreign = { ...principal, workspaceId: 'staging-foreign-synthetic' };
export const scope = { origin: 'https://staging.fixture.example', template: 'signed-fixture' };
export const trace = { ...scope, submissionId: 'fixture-first', verificationId: 'verified-fixture', reviewVerified: true,
  steps: [{ beforeOutline: 'a'.repeat(64), afterOutline: 'b'.repeat(64), kind: 'click',
    locator: ['button', 'Next', 'button', ''] }] };
const sha = value => createHash('sha256').update(value).digest('hex');
const hash = /^[a-f0-9]{64}$/;
const response = (body, status = 200) => Response.json(body, { status, headers: { 'cache-control': 'private, no-store' } });

export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    if (env.GAMMA_STAGING_ONLY !== 'synthetic-recipe-qualification-v1' || !env.STAGING_DB ||
        !hash.test(env.GAMMA_STAGE_BEARER_HASH ?? '') || !hash.test(env.GAMMA_STAGE_FOREIGN_HASH ?? '') ||
        !hash.test(env.GAMMA_STAGE_SCOPE_SECRET ?? '') || !env.GAMMA_STAGE_SIGNER_PEM ||
        request.method !== 'POST' || !['/__qualification/seed', '/v1/recipe-generations/read'].includes(path)) {
      return response({ error: 'not-found' }, 404);
    }
    try {
      const store = createD1RecipeStore(env.STAGING_DB);
      const engine = createManagedRecipeEngine({ store, secret: env.GAMMA_STAGE_SCOPE_SECRET });
      if (path === '/__qualification/seed') {
        const auth = request.headers.get('authorization') ?? '';
        const expected = env.GAMMA_STAGE_BEARER_HASH;
        if (!auth.startsWith('Bearer ') || !timingSafeEqual(Buffer.from(sha(auth.slice(7))), Buffer.from(expected))) {
          return response({ error: 'not-found' }, 404);
        }
        const accepted = await engine.acceptTrace(principal, trace);
        const published = await engine.compactAcceptedWorkspace(principal, scope, {
          expectedGeneration: 0, inputWatermark: accepted.acceptanceSequence,
        });
        const corpus = await qualifyRecipeGenerationCorpus(engine);
        return response({ generation: published.generation, corpus });
      }
      const privateKey = createPrivateKey(env.GAMMA_STAGE_SIGNER_PEM);
      const generationSigner = packet => {
        const issuedAt = Date.now();
        return signRecipeGenerationManifest({ packet, privateKey, issuedAt, expiresAt: issuedAt + 60_000 });
      };
      return await createManagedRecipeHttpHandler({ engine, generationSigner, clients: [
        { ...principal, tokenHash: env.GAMMA_STAGE_BEARER_HASH },
        { ...foreign, tokenHash: env.GAMMA_STAGE_FOREIGN_HASH },
      ] })(request);
    } catch {
      return response({ error: 'staging-qualification-failed' }, 500);
    }
  },
};
