import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm, rename } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { releaseSourceRoot } from '../tasks/release-source-root.mjs';
test('current and pre-relocation commits verify their own sealed source roots', async () => {
  const root = await mkdtemp(join(tmpdir(), 'mandate-source-root-'));
  const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim();
  const commit = () => { git('add', '.'); git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Fixture'); return git('rev-parse', 'HEAD'); };
  try {
    git('init', '-q');
    await mkdir(join(root, 'games/2038/versions'), { recursive: true });
    await writeFile(join(root, 'games/2038/versions/current.json'), '{"sealed":true}');
    const historical = commit();
    await mkdir(join(root, 'apps'));
    await rename(join(root, 'games'), join(root, 'apps/games'));
    const previouslyRelocated = commit();
    await rename(join(root, 'apps/games/2038'), join(root, 'apps/mandate-2038'));
    const current = commit();
    assert.equal(await releaseSourceRoot(historical, root), 'games/2038');
    assert.equal(await releaseSourceRoot(previouslyRelocated, root), 'apps/games/2038');
    assert.equal(await releaseSourceRoot(current, root), 'apps/mandate-2038');
    await mkdir(join(root, 'games/2038/versions'), { recursive: true });
    await writeFile(join(root, 'games/2038/versions/current.json'), '{}');
    await assert.rejects(releaseSourceRoot(commit(), root), /exactly one/);
  } finally { await rm(root, { recursive: true, force: true }); }
});
