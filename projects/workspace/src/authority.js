// Fawn workspace — caller credentials
//
// Credentials are random secrets returned once; the journal stores only their hashes.

import { createHash, randomBytes, timingSafeEqual } from 'node:crypto';

const CREDENTIAL_ENCODING = 'base64url';

function issueCredential(secretBytes) {
  const credential = randomBytes(secretBytes).toString(CREDENTIAL_ENCODING);
  return { credential, credentialHash: hashCredential(credential) };
}

function hashCredential(credential) {
  return createHash('sha256').update(String(credential)).digest('hex');
}

function credentialMatches(credential, credentialHash) {
  if (typeof credential !== 'string' || typeof credentialHash !== 'string') return false;
  const presented = Buffer.from(hashCredential(credential), 'hex');
  const stored = Buffer.from(credentialHash, 'hex');
  return presented.length === stored.length && timingSafeEqual(presented, stored);
}

/**
 * Find which owner generation a credential was issued for, or null.
 * @param {Map<number, string>} hashesByGeneration
 */
function generationForCredential(credential, hashesByGeneration) {
  for (const [generation, credentialHash] of hashesByGeneration) {
    if (credentialMatches(credential, credentialHash)) return generation;
  }
  return null;
}

export { credentialMatches, generationForCredential, hashCredential, issueCredential };
