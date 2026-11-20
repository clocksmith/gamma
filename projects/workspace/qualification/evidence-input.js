// Read retained evidence using its producer's path grammar, without rewriting receipts.
import { readFileSync, realpathSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { isDeepStrictEqual } from 'node:util';
import { isAbsolute, join, relative, sep, win32, posix } from 'node:path';

function evidencePath(root, recordedPath, platform) {
  const grammar = platform === 'win32' ? win32 : (['darwin', 'linux'].includes(platform) ? posix : null);
  if (!grammar || typeof recordedPath !== 'string' || !recordedPath || recordedPath.includes('\0')
      || grammar.parse(recordedPath).root || grammar.isAbsolute(recordedPath)) {
    throw new Error('invalid recorded evidence path or platform');
  }
  const parts = recordedPath.split(platform === 'win32' ? /[\\/]/ : /\//);
  if (parts.includes('..')) throw new Error('evidence path contains parent traversal');
  const path = realpathSync(join(root, ...parts));
  const within = relative(realpathSync(root), path);
  if (isAbsolute(within) || within === '..' || within.startsWith(`..${sep}`)) {
    throw new Error('evidence path escapes its root');
  }
  return path;
}

// A retained snapshot must match BOTH the producer's exact byte hash and every
// current frozen rule. This admits CRLF receipts without normalizing their hashes.
function caseSetMatches(resultDir, recordedHash, currentBytes) {
  let bytes;
  try {
    bytes = readFileSync(evidencePath(resultDir, 'case-set.json', process.platform));
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
    bytes = currentBytes;
  }
  return createHash('sha256').update(bytes).digest('hex') === recordedHash
    && isDeepStrictEqual(JSON.parse(bytes), JSON.parse(currentBytes));
}

export { evidencePath, caseSetMatches };
