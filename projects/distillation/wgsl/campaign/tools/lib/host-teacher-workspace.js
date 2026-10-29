import {
  access,
  appendFile,
  lstat,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  symlink,
  writeFile,
} from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

import { sha256Hex } from '../../src/utils/sha256.js';
import { resolveRepoPath } from './host-teacher-contracts.js';
import { runHostProcess } from './host-teacher-process.js';

function countOccurrences(source, needle) {
  let count = 0;
  let offset = 0;
  while (offset <= source.length - needle.length) {
    const found = source.indexOf(needle, offset);
    if (found === -1) break;
    count += 1;
    offset = found + needle.length;
  }
  return count;
}

async function requireSuccessfulProcess(command, args, options = {}) {
  const result = await runHostProcess(command, args, options);
  if (result.code !== 0 || result.signal) {
    throw new Error(
      `Snapshot command failed: ${command} ${args.join(' ')}\n${result.stdout}\n${result.stderr}`
    );
  }
  return result;
}

async function pathExists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

async function applyTaskMutations(workspace, task) {
  const originals = new Map();
  for (const mutation of task.mutations) {
    const absolutePath = resolveRepoPath(workspace, mutation.path);
    const source = await readFile(absolutePath, 'utf8');
    if (!originals.has(mutation.path)) {
      originals.set(mutation.path, {
        content: source,
        hash: sha256Hex(source),
      });
    }
    const observedOccurrences = countOccurrences(source, mutation.find);
    if (observedOccurrences !== mutation.occurrences) {
      throw new Error(
        `${task.id}: mutation expected ${mutation.occurrences} occurrence(s) in ${mutation.path}, observed ${observedOccurrences}.`
      );
    }
    const mutated = source.split(mutation.find).join(mutation.replace);
    await writeFile(absolutePath, mutated, 'utf8');
  }
  for (const [path, original] of originals) {
    const mutated = await readFile(resolveRepoPath(workspace, path), 'utf8');
    if (sha256Hex(mutated) === original.hash) {
      throw new Error(`${task.id}: mutation did not change ${path}.`);
    }
    original.mutatedHash = sha256Hex(mutated);
  }
  return originals;
}

async function initializeBaselineRepository(workspace, task) {
  await requireSuccessfulProcess('git', ['init', '--quiet'], { cwd: workspace });
  await requireSuccessfulProcess('git', ['config', 'user.name', 'Doppler Host Teacher'], { cwd: workspace });
  await requireSuccessfulProcess('git', ['config', 'user.email', 'host-teacher@invalid'], { cwd: workspace });
  await requireSuccessfulProcess('git', ['add', '--all'], { cwd: workspace });
  await requireSuccessfulProcess('git', ['commit', '--quiet', '-m', `mutated baseline: ${task.id}`], {
    cwd: workspace,
  });
  const revision = await requireSuccessfulProcess('git', ['rev-parse', 'HEAD'], { cwd: workspace });
  return revision.stdout.trim();
}

export async function createHostTeacherWorkspace(contracts, task, options = {}) {
  const parent = await mkdtemp(join(tmpdir(), 'doppler-host-teacher-'));
  try {
    const workspace = join(parent, 'workspace');
    const archivePath = join(parent, 'source.tar.gz');
    await mkdir(workspace);
    await requireSuccessfulProcess('git', [
      'archive',
      '--format=tar.gz',
      '--output',
      archivePath,
      contracts.taskBank.baseRevision,
      '--',
      ...(options.paths ? options.paths.map(path => {
        resolveRepoPath(workspace, path);
        return `:(literal)${path}`;
      }) : ['.']),
      ...contracts.policy.snapshot.excludedPaths.map((path) => {
        resolveRepoPath(workspace, path);
        return `:(exclude,literal)${path}`;
      }),
    ], { cwd: contracts.root });
    await requireSuccessfulProcess('tar', ['-xf', archivePath, '-C', workspace]);
    await rm(archivePath, { force: true });

    for (const excludedPath of contracts.policy.snapshot.excludedPaths) {
      await rm(resolveRepoPath(workspace, excludedPath), { recursive: true, force: true });
    }

    const originals = await applyTaskMutations(workspace, task);
    const baselineRevision = await initializeBaselineRepository(workspace, task);

    if (contracts.policy.snapshot.linkNodeModules) {
      const sourceNodeModules = join(contracts.root, 'node_modules');
      if (!(await pathExists(sourceNodeModules))) {
        throw new Error('Host teacher policy requires the repository node_modules directory.');
      }
      const stats = await lstat(sourceNodeModules);
      if (!stats.isDirectory()) {
        throw new Error('Host teacher node_modules source must be a directory.');
      }
      await symlink(sourceNodeModules, join(workspace, 'node_modules'), 'dir');
      await appendFile(join(workspace, '.git', 'info', 'exclude'), '\nnode_modules\n', 'utf8');
    }

    return {
      parent,
      workspace,
      baselineRevision,
      originals,
      cleanup: () => rm(parent, { recursive: true, force: true }),
    };
  } catch (error) {
    await rm(parent, { recursive: true, force: true });
    throw error;
  }
}

export async function readWorkspaceStatus(workspace) {
  const status = await requireSuccessfulProcess(
    'git',
    ['status', '--porcelain=v1', '-z', '--untracked-files=all'],
    { cwd: workspace }
  );
  const records = status.stdout.split('\0').filter(Boolean);
  const paths = [];
  for (let index = 0; index < records.length; index += 1) {
    const record = records[index];
    const statusCode = record.slice(0, 2);
    const path = record.slice(3);
    paths.push(path);
    if (statusCode.includes('R') || statusCode.includes('C')) {
      index += 1;
      if (records[index]) paths.push(records[index]);
    }
  }
  return [...new Set(paths)].sort((left, right) => left.localeCompare(right));
}

export async function readWorkspacePatch(workspace) {
  const tracked = await requireSuccessfulProcess('git', ['diff', '--binary', '--no-ext-diff', 'HEAD'], {
    cwd: workspace,
  });
  return tracked.stdout;
}
