import { randomUUID } from 'node:crypto';
import { bindSelectedLocalDocument } from './local-document.js';

export const DOCUMENT_SELECTION_BROKER_V1 = 'gamma.workspace.document-selection/v1';
const unknown = reason => ({ status: 'unknown', reason });
const exactKeys = (value, keys) => value !== null && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).sort().join(',') === keys;

async function releaseSelection(release) {
  try { await release(); return true; }
  catch { return false; } // Do not disclose local paths or underlying OS errors.
}

/**
 * Process-local capability split, not a network service. Only the trusted
 * owner UI holds owner.select; selectFile must implement an explicit OS user
 * selection and provide a read-only descriptor plus a same-process release.
 * Neither an observer nor a recipe can invoke selection, pass a path, or
 * receive the source descriptor. Tokens live only until replacement/revoke.
 */
export function createLocalDocumentBroker({ selectFile, maxBytes } = {}) {
  if (typeof selectFile !== 'function') throw new TypeError('A trusted local document selector is required');
  let active = null;
  let selecting = false;
  let closed = false;
  let epoch = 0;

  function retire(entry) {
    if (!entry) return Promise.resolve(true);
    entry.document.detach();
    return releaseSelection(entry.release);
  }

  function current(documentId) {
    return !closed && typeof documentId === 'string' && active?.documentId === documentId ? active : null;
  }

  const owner = Object.freeze({
    async select() {
      if (closed) return unknown('selection-broker-closed');
      if (selecting) return unknown('selection-in-progress');
      selecting = true;
      const selectionEpoch = epoch;
      let release = null;
      try {
        const selected = await selectFile();
        if (selected === null) return closed || epoch !== selectionEpoch
          ? unknown('selection-ended') : { status: 'cancelled' };
        release = typeof selected?.release === 'function' ? selected.release.bind(selected) : null;
        if (!exactKeys(selected, 'handle,release') || !release) return unknown('invalid-selection-result');
        if (closed || epoch !== selectionEpoch) return unknown('selection-ended');
        const documentId = randomUUID();
        const document = await bindSelectedLocalDocument({ documentId, handle: selected.handle, maxBytes });
        if (closed || epoch !== selectionEpoch) return unknown('selection-ended');

        const previous = active;
        const entry = { documentId, document, release };
        active = entry;
        release = null; // Only the active record owns release after transfer.
        const previousReleased = await retire(previous);
        if (active !== entry) return unknown('selection-ended');
        return { status: 'selected', documentId, previousReleased };
      } catch {
        return unknown('selection-unavailable');
      } finally {
        if (release) await releaseSelection(release);
        selecting = false;
      }
    },

    async revoke() {
      epoch++;
      const previous = active;
      active = null;
      return { status: 'revoked', released: await retire(previous) };
    },

    async close() {
      closed = true;
      epoch++;
      const previous = active;
      active = null;
      return { status: 'closed', released: await retire(previous) };
    },
  });

  const observer = Object.freeze({
    async observe(documentId) {
      const entry = current(documentId);
      if (!entry) return unknown('selection-unavailable');
      const result = await entry.document.observe();
      return current(documentId) === entry ? result : unknown('selection-unavailable');
    },

    async reconcile(documentId, expected) {
      const entry = current(documentId);
      if (!entry) return unknown('selection-unavailable');
      if (!exactKeys(expected, 'byteLength,sha256')) return unknown('invalid-document-expectation');
      const result = await entry.document.reconcile({ documentId,
        byteLength: expected.byteLength, sha256: expected.sha256 });
      return current(documentId) === entry ? result : unknown('selection-unavailable');
    },
  });

  return Object.freeze({ version: DOCUMENT_SELECTION_BROKER_V1, owner, observer });
}
