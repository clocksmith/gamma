// Sealed pre-relocation releases retain their original Git paths. Resolve the
// recorded commit's one project root without rewriting its evidence bytes.
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const execute = promisify(execFile);
export async function releaseSourceRoot(revision, cwd) {
  const pointers = [
    'apps/mandate-2038/versions/current.json',
    'apps/games/2038/versions/current.json',
    'games/2038/versions/current.json'
  ];
  const { stdout } = await execute('git', ['ls-tree', '--full-tree', '--name-only', revision, '--', ...pointers], { cwd });
  const found = stdout.trim().split('\n').filter(Boolean);
  if (found.length !== 1 || !pointers.includes(found[0])) throw Error('Source commit must carry exactly one Mandate release root');
  return found[0].slice(0, -'/versions/current.json'.length);
}
