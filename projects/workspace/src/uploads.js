// Explicit administrator-selected bytes, kept outside the action journal. Agents receive IDs,
// never a filesystem path. Staged files remain available for a later browser form submission.
import { randomUUID } from 'node:crypto';
import { mkdirSync, readdirSync, readFileSync, writeFileSync, statSync, rmSync, openSync, fsyncSync, closeSync } from 'node:fs';
import { join } from 'node:path';
import { sha256Hex } from './journal.js';
import { REJECTION_CODES, workspaceError } from './errors.js';

function invalid(message) {
  throw workspaceError(REJECTION_CODES.INVALID_COMMAND, message);
}

class UploadStore {
  constructor(directory, limits) {
    this.directory = directory;
    this.limits = limits;
  }

  stage(files) {
    if (!this.limits) invalid('Uploads require service schema 5 upload limits');
    if (!Array.isArray(files) || !files.length || files.length > this.limits.maxFilesPerAction) {
      invalid('Select files within uploads.maxFilesPerAction');
    }
    const decoded = files.map(file => {
      if (!file || Object.keys(file).some(key => !['name', 'base64'].includes(key))
        || typeof file.name !== 'string' || !file.name || file.name === '.' || file.name === '..'
        || /[\x00-\x1f\x7f/\\]/.test(file.name) || Buffer.byteLength(file.name) > this.limits.maxNameBytes) invalid('Provide a plain upload filename');
      if (typeof file.base64 !== 'string' || file.base64.length > 4 * Math.ceil(this.limits.maxFileBytes / 3)
        || file.base64.length % 4 !== 0 || !/^[A-Za-z0-9+/]*={0,2}$/.test(file.base64)) invalid('Provide bounded base64 file bytes');
      const bytes = Buffer.from(file.base64, 'base64');
      if (bytes.length > this.limits.maxFileBytes || bytes.toString('base64') !== file.base64) invalid('Invalid upload bytes');
      return { name: file.name, bytes };
    });
    mkdirSync(this.directory, { recursive: true, mode: 0o700 });
    const retainedBytes = readdirSync(this.directory).reduce((sum, id) => sum
      + readdirSync(join(this.directory, id)).reduce((size, name) => size + statSync(join(this.directory, id, name)).size, 0), 0);
    if (retainedBytes + decoded.reduce((sum, file) => sum + file.bytes.length, 0) > this.limits.maxStagedBytes) {
      invalid('Upload staging budget exhausted; close browsers and retire unused staged files before adding more');
    }
    const staged = [];
    try {
      for (const { name, bytes } of decoded) {
        const fileId = randomUUID();
        const directory = join(this.directory, fileId);
        mkdirSync(directory, { mode: 0o700 });
        staged.push({ fileId, name, byteLength: bytes.length, sha256: sha256Hex(bytes) });
        const path = join(directory, name);
        writeFileSync(path, bytes, { flag: 'wx', mode: 0o600 });
        const fd = openSync(path, 'r');
        try { fsyncSync(fd); } finally { closeSync(fd); }
      }
      return staged;
    } catch (error) {
      this.discard(staged);
      throw error;
    }
  }

  discard(files) {
    for (const file of files) rmSync(join(this.directory, file.fileId), { recursive: true, force: true });
  }

  // Only after all browsers have closed: a page may still read its attached files even after
  // authority is revoked. Live grants retain their snapshots for service restart.
  retireUnused(fileIds) {
    mkdirSync(this.directory, { recursive: true, mode: 0o700 });
    for (const fileId of readdirSync(this.directory)) {
      if (!fileIds.has(fileId)) rmSync(join(this.directory, fileId), { recursive: true, force: true });
    }
  }

  resolve(grant, fileIds) {
    return fileIds.map(fileId => {
      const file = grant?.uploadFiles?.find(candidate => candidate.fileId === fileId);
      if (!file || !/^[a-f0-9-]{36}$/.test(file.fileId) || /[/\\]/.test(file.name)) invalid('Upload file is not authorized');
      const path = join(this.directory, file.fileId, file.name);
      if (statSync(path).size !== file.byteLength) invalid('Staged upload size changed');
      const bytes = readFileSync(path);
      if (bytes.length !== file.byteLength || sha256Hex(bytes) !== file.sha256) invalid('Staged upload bytes changed');
      return { ...file, path };
    });
  }
}

function validateUploadParams(params, config) {
  if (!params || Object.keys(params).some(key => key !== 'fileIds') || !Array.isArray(params.fileIds)
    || !config.uploads || !params.fileIds.length || params.fileIds.length > config.uploads.maxFilesPerAction
    || params.fileIds.some(id => typeof id !== 'string' || !id)
    || new Set(params.fileIds).size !== params.fileIds.length) invalid('Upload params must contain only distinct approved fileIds');
}

function checkUploadTarget(element, files) {
  if (element.tag !== 'input' || element.inputType !== 'file' || element.disabled
    || (!element.multiple && files.length !== 1)) invalid('Upload requires an enabled file input with compatible multiplicity');
  const accepts = (element.accept ?? '').split(',').map(value => value.trim().toLowerCase()).filter(Boolean);
  // Extension checks are deterministic here. MIME acceptance is browser/site-owned, not a
  // promise inferred from a filename. The page may still reject a successfully attached file.
  const extensions = accepts.filter(value => value.startsWith('.'));
  if (extensions.length === accepts.length && extensions.length
    && files.some(file => !extensions.some(extension => file.name.toLowerCase().endsWith(extension)))) invalid('Filename does not match the file input accept extensions');
}

export { UploadStore, validateUploadParams, checkUploadTarget };
