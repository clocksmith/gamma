import { Buffer } from 'node:buffer';
import { createHash } from 'node:crypto';

export const LOCAL_DOCUMENT_SURFACE_V1 = 'gamma.workspace.local-document/v1';
const DEFAULT_MAX_BYTES = 1024 * 1024;
const HARD_MAX_BYTES = 16 * 1024 * 1024;
const CHUNK_BYTES = 64 * 1024;
const ID = /^[a-zA-Z0-9._:/-]{1,128}$/;
const SHA256 = /^[a-f0-9]{64}$/;
const sha = value => createHash('sha256').update(value).digest('hex');
const identity = stat => [stat.dev, stat.ino].join(':');
const revision = stat => [stat.dev, stat.ino, stat.size, stat.mtimeNs, stat.ctimeNs].join(':');
const unknown = reason => ({ status: 'unknown', reason });

/**
 * Local, read-only provider for a FileHandle already opened by trusted caller
 * code after document selection. Borrows but never opens/closes the handle.
 * No pathname, OS permission, executor, credentials or live workspace grants.
 */
export async function bindSelectedLocalDocument({ documentId, handle, maxBytes = DEFAULT_MAX_BYTES } = {}) {
  if (typeof documentId !== 'string' || !ID.test(documentId) ||
      !handle || typeof handle.stat !== 'function' || typeof handle.read !== 'function' ||
      !Number.isSafeInteger(maxBytes) || maxBytes < 1 || maxBytes > HARD_MAX_BYTES) {
    throw new TypeError('Valid selected local document handle, identity and byte limit required');
  }
  let bound;
  try { bound = await handle.stat({ bigint: true }); }
  catch { throw Error('Selected local document is unavailable'); }
  if (!bound.isFile()) throw Error('Selected local document is not a regular file');

  const selectedIdentity = identity(bound);
  let attached = true;

  async function observe() {
    if (!attached) return unknown('selection-detached');
    try {
      const before = await handle.stat({ bigint: true });
      if (!attached) return unknown('selection-detached');
      if (!before.isFile() || identity(before) !== selectedIdentity) return unknown('selection-changed');
      if (before.size > BigInt(maxBytes)) return unknown('byte-limit-exceeded');
      const byteLength = Number(before.size);
      const initialRevision = revision(before);
      const hash = createHash('sha256');
      const chunk = Buffer.alloc(Math.min(CHUNK_BYTES, byteLength));
      for (let offset = 0; offset < byteLength;) {
        if (!attached) return unknown('selection-detached');
        const length = Math.min(chunk.length, byteLength - offset);
        const { bytesRead } = await handle.read(chunk, 0, length, offset);
        if (!attached) return unknown('selection-detached');
        if (!Number.isSafeInteger(bytesRead) || bytesRead < 1 || bytesRead > length) return unknown('document-changed');
        hash.update(chunk.subarray(0, bytesRead));
        offset += bytesRead;
      }
      const after = await handle.stat({ bigint: true });
      if (!attached) return unknown('selection-detached');
      if (!after.isFile() || revision(after) !== initialRevision) return unknown('document-changed');
      return { status: 'observed', documentId, byteLength, sha256: hash.digest('hex'), revision: sha(initialRevision) };
    } catch {
      return unknown(attached ? 'document-unavailable' : 'selection-detached');
    }
  }

  async function reconcile(expected) {
    if (!expected || expected.documentId !== documentId ||
        typeof expected.sha256 !== 'string' || !SHA256.test(expected.sha256) ||
        !Number.isSafeInteger(expected.byteLength) || expected.byteLength < 0 ||
        expected.byteLength > maxBytes) {
      return unknown('invalid-document-expectation');
    }
    if (!attached) return unknown('selection-detached');
    // A readable descriptor (even with matching bytes) cannot establish that
    // the owner-selected document still points to this object after a safe save.
    // This surface has no trusted live binding, so do not read or confirm it.
    return unknown('live-document-binding-unavailable');
  }

  return Object.freeze({
    surfaceVersion: LOCAL_DOCUMENT_SURFACE_V1,
    observe,
    reconcile,
    detach() { attached = false; },
  });
}
