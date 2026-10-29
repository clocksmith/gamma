import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { access, mkdir, mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHostTeacherWorkspace } from '../../tools/lib/host-teacher-workspace.js';

const root = await mkdtemp(join(tmpdir(), 'doppler-workspace-fixture-'));
const task = { id: 'cleanup-regression', mutations: [{ path: 'source.js',
  find: 'true', replace: 'false', occurrences: 1 }] };
const contracts = { root, taskBank: { baseRevision: 'HEAD' },
  policy: { snapshot: { excludedPaths: ['history (old)', 'nested/excluded'], linkNodeModules: false } } };
const parents = async () => new Set((await readdir(tmpdir())).filter(name => name.startsWith('doppler-host-teacher-')));
const absent = async path => assert.rejects(access(path), { code: 'ENOENT' });
try {
  await mkdir(join(root, 'history (old)'));
  await mkdir(join(root, 'nested/excluded'), { recursive: true });
  await writeFile(join(root, 'history (old)/receipt.bin'), new Uint8Array(1024 * 1024));
  await writeFile(join(root, 'nested/excluded/history.txt'), 'historical evidence');
  await writeFile(join(root, 'source.js'), 'export const valid = true;\n');
  await writeFile(join(root, 'unrelated.txt'), 'Unrelated repository content');
  const git = args => execFileSync('git', args, { cwd: root, stdio: 'pipe' });
  git(['init', '--quiet']);
  git(['add', '--all']);
  git(['-c', 'user.name=Fixture', '-c', 'user.email=fixture@invalid', 'commit', '--quiet', '-m', 'fixture']);
  const state = await createHostTeacherWorkspace(contracts, task);
  try {
    assert.equal(await readFile(join(state.workspace, 'source.js'), 'utf8'), 'export const valid = false;\n');
    await absent(join(state.workspace, 'history (old)'));
    await absent(join(state.workspace, 'nested/excluded'));
    assert.deepEqual(await readdir(state.parent), ['workspace']);
  } finally { await state.cleanup(); }
  await absent(state.parent);
  const excerpt = await createHostTeacherWorkspace(contracts, task, { paths: ['source.js'] });
  try {
    assert.equal(await readFile(join(excerpt.workspace, 'source.js'), 'utf8'), 'export const valid = false;\n');
    await absent(join(excerpt.workspace, 'unrelated.txt'));
  } finally { await excerpt.cleanup(); }
  for (const broken of [
    { ...contracts, taskBank: { baseRevision: 'missing-revision' } },
    { ...contracts, policy: { snapshot: { ...contracts.policy.snapshot, linkNodeModules: true } } },
  ]) {
    const before = await parents();
    await assert.rejects(createHostTeacherWorkspace(broken, task),
      broken.taskBank.baseRevision === 'missing-revision' ? /Snapshot command failed/ : /node_modules/);
    assert.deepEqual(await parents(), before, 'Failed workspace preparation leaked its archive or checkout');
  }
} finally { await rm(root, { recursive: true, force: true }); }
console.log('host-teacher-workspace-cleanup.test: ok');
