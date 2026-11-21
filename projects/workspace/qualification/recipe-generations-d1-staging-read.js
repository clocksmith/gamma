// Read-only. Use only an authorized staging Worker already bound to an isolated
// D1 database and provisioned with the exact, sanitized fixture generation.
import { createPublicKey } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { checkRecipeGenerationSigning } from './recipe-generation-signing-check.js';

let phase = 'configuration';
try {
  const [flag, configPath] = process.argv.slice(2);
  if (flag !== '--approved-staging-read' || !configPath || process.argv.length !== 4) throw Error();
  const token = process.env.GAMMA_RECIPE_STAGING_TOKEN;
  const authorizedOrigin = process.env.GAMMA_RECIPE_STAGING_ORIGIN;
  const url = new URL(authorizedOrigin);
  if (url.protocol !== 'https:' || url.origin !== authorizedOrigin ||
      url.hostname === 'localhost' || !token || !/^[^\s]{32,256}$/.test(token)) throw Error();
  const { endpointOrigin, scope, generation, trust, publicKeyPem } = JSON.parse(readFileSync(configPath, 'utf8'));
  if (endpointOrigin !== authorizedOrigin || trust?.minimumGeneration !== generation ||
      typeof publicKeyPem !== 'string' || !publicKeyPem.startsWith('-----BEGIN PUBLIC KEY-----')) throw Error();
  const publicKey = createPublicKey(publicKeyPem);
  if (publicKey.asymmetricKeyType !== 'ed25519') throw Error();

  phase = 'signed-delivery';
  const result = await checkRecipeGenerationSigning({
    url: authorizedOrigin, token, scope, generation, trust: { ...trust, publicKey },
  });
  console.log(JSON.stringify({ qualification: 'staging-signed-generation-read/v1', ...result,
    storageBindingIndependentlyVerified: false }));
} catch {
  // Never show credentials, the URL, the pinned namespace, or a response body.
  console.error('Staging signed-generation qualification failed at ' + phase);
  process.exitCode = 1;
}
