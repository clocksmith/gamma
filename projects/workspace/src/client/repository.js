// Explicitly selected repository root is the only filesystem read capability for the agent.
import { realpath, readFile, stat, readdir } from 'node:fs/promises';
import { resolve, relative, isAbsolute } from 'node:path';
import { sha256Hex } from '../journal.js';
const EXCLUDED = new Set(['node_modules', '.git', '.claude', '.deployment-checkouts', '.tmp']);
export async function repositoryEvidence(root, file, maxBytes) {
  if (!root || typeof file !== 'string') throw Error('Select a repository before reading its evidence');
  const base = await realpath(root), target = await realpath(resolve(base, file));
  const path = relative(base, target);
  if (!path || path.startsWith('..') || isAbsolute(path)) throw Error('Repository read escapes the selected root');
  const info = await stat(target);
  if (!info.isFile() || info.size > maxBytes) throw Error('Repository evidence must be a bounded regular file');
  const bytes = await readFile(target);
  if (bytes.length > maxBytes || bytes.includes(0)) throw Error('Repository evidence is oversized or binary');
  const content = bytes.toString('utf8');
  if (!Buffer.from(content, 'utf8').equals(bytes)) throw Error('Repository text evidence requires valid UTF-8 bytes');
  return { kind: 'repository', path, content, sha256: sha256Hex(content) };
}
export async function repositoryFiles(root, maxFiles) {
  if (!root) throw Error('No selected repository');
  const base = await realpath(root), files = [], pending = [''];
  while (pending.length && files.length < maxFiles) {
    const current = pending.shift();
    for (const entry of (await readdir(resolve(base, current), { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name))) {
      if (EXCLUDED.has(entry.name) || entry.isSymbolicLink()) continue;
      const path = current ? `${current}/${entry.name}` : entry.name;
      if (entry.isDirectory()) pending.push(path);
      else if (entry.isFile()) files.push(path);
      if (files.length >= maxFiles) break;
    }
  }
  return { files, truncated: pending.length > 0 || files.length === maxFiles };
}
