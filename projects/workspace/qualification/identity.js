// Fawn workspace qualification — source, harness and browser identities.
//
// Results name the exact bytes they ran: source trees by per-file SHA-256, and browser
// executables and listeners as observed by the host OS, never adapter claims.

import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { arch, platform, release } from 'node:os';
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { canonicalJson } from '../src/journal.js';
import { descendants, inspectProcesses, processesUsing, windowsFileVersion } from './process-inspection.js';

const REPO_ROOT = fileURLToPath(new URL('../../../', import.meta.url));
const EXCLUDED_DIRECTORIES = Object.freeze(['node_modules']);
const VERSION_TIMEOUT_MS = 10000;
const DEVTOOLS_PORT_FILE = 'DevToolsActivePort';
const PROFILE_RELEASE_POLL_MS = 50;
const PROFILE_RELEASE_LIMIT_MS = 15000;

function sha256File(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex');
}

function listFiles(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    if (entry.isDirectory()) return EXCLUDED_DIRECTORIES.includes(entry.name) ? [] : listFiles(join(directory, entry.name));
    return entry.isFile() ? [join(directory, entry.name)] : [];
  });
}

/** Digest of a source tree: sorted repo-relative paths with their SHA-256. */
function treeDigest(repoPath) {
  const root = join(REPO_ROOT, repoPath);
  const files = listFiles(root).map((path) => [relative(REPO_ROOT, path).split(sep).join('/'), sha256File(path)])
    .sort((a, b) => (a[0] < b[0] ? -1 : 1));
  return { path: repoPath, sha256: createHash('sha256').update(canonicalJson(files)).digest('hex'), fileCount: files.length };
}

function repoFileSha256(repoPath) {
  return sha256File(join(REPO_ROOT, repoPath));
}

function gitState() {
  try {
    const commit = execFileSync('git', ['-C', REPO_ROOT, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
    const dirty = execFileSync('git', ['-C', REPO_ROOT, 'status', '--porcelain', '--', 'projects/workspace', 'config', 'projects/workspace/src/browser-launch.js'], {
      encoding: 'utf8',
    }).trim();
    return { commit, workingTreeChanges: dirty.length > 0 ? dirty.split('\n') : [] };
  } catch (error) {
    return { commit: null, error: error.message };
  }
}

function countFilesNamed(directory, name) {
  let entries;
  try {
    entries = readdirSync(directory, { withFileTypes: true });
  } catch (error) {
    // Browser-owned temporary directories can disappear while a live profile
    // is inspected. Source-tree inventory above intentionally remains strict.
    if (error.code === 'ENOENT') return 0;
    throw error;
  }
  return entries.reduce((count, entry) => count
    + (entry.isDirectory() ? countFilesNamed(join(directory, entry.name), name)
      : Number(entry.isFile() && entry.name === name)), 0);
}

const executableCache = new Map();
const imageCache = new Map();
function describeImage(path) {
  const stat = statSync(path);
  const cached = imageCache.get(path);
  if (!cached || cached.mtimeMs !== stat.mtimeMs || cached.identity.byteLength !== stat.size) {
    imageCache.set(path, { mtimeMs: stat.mtimeMs,
      identity: { path, sha256: sha256File(path), byteLength: stat.size } });
  }
  return imageCache.get(path).identity;
}

function describeExecutable(path) {
  if (!executableCache.has(path)) {
    let version = null;
    try {
      version = process.platform === 'win32' ? windowsFileVersion(path)
        : execFileSync(path, ['--version'], { encoding: 'utf8', timeout: VERSION_TIMEOUT_MS }).trim();
    } catch (error) {
      version = `unavailable: ${error.message.split('\n')[0]}`;
    }
    executableCache.set(path, { path, sha256: sha256File(path), byteLength: statSync(path).size, version });
  }
  return executableCache.get(path);
}

/**
 * Inspect owned browser roots, descendant images, TCP listeners and DevTools port files.
 */
function inspectBrowserProcesses(hostPid, profileRoot) {
  const inspection = inspectProcesses(hostPid);
  const imagePaths = [...new Set(inspection.rows.map((row) => row.executable))].sort();
  const codeModules = inspection.codeModules.sort().map(describeImage);
  const codeModulesSha256 = createHash('sha256').update(canonicalJson(codeModules)).digest('hex');
  return {
    processCount: inspection.rows.length,
    // Root browser images are compared between adapters; platform helper
    // executables and mapped app frameworks retain their own exact identities.
    executables: [...new Set(inspection.roots.map((row) => row.executable))].sort()
      .map((path) => ({ ...describeExecutable(path), codeModulesSha256 })),
    processImages: imagePaths.map(describeImage),
    processes: inspection.rows.map(({ pid, parentPid, executable, startedAt, commandLine }) =>
      ({ pid, parentPid, executable, startedAt, commandLine })),
    codeModules,
    mappedCodeModules: inspection.mappedCodeModules.sort().map(path => ({ ...describeImage(path),
      processes: inspection.mappedCodeModuleObservations.filter(entry => entry.path === path)
        .map(({ path: _path, ...entry }) => entry).sort((left, right) => left.pid - right.pid),
    })),
    unavailableModuleMappings: inspection.unavailableModuleMappings,
    listeningTcpSockets: inspection.listeningTcpSockets,
    devToolsActivePortFiles: countFilesNamed(profileRoot, DEVTOOLS_PORT_FILE),
  };
}

function executableIdentityKey(executable) {
  return `${executable.path}|${executable.sha256}|${executable.codeModulesSha256 ?? ''}`;
}

/** Wait until no process still uses a state directory (a killed host's browser exits on pipe close). */
async function waitForProfileRelease(stateDir) {
  const deadline = Date.now() + PROFILE_RELEASE_LIMIT_MS;
  while (processesUsing(stateDir).length > 0) {
    if (Date.now() > deadline) throw new Error(`browser processes still use ${stateDir}`);
    await new Promise((resolve) => setTimeout(resolve, PROFILE_RELEASE_POLL_MS));
  }
}

/** Identities a qualification or comparison result is bound to. */
function resultIdentity() {
  const require = createRequire(import.meta.url);
  return {
    caseSet: { path: 'projects/workspace/config/fawn-workspace-qualification.json', sha256: repoFileSha256('projects/workspace/config/fawn-workspace-qualification.json') },
    serviceConfig: { path: 'projects/workspace/config/fawn-workspace-service.json', sha256: repoFileSha256('projects/workspace/config/fawn-workspace-service.json') },
    comparisonPolicy: {
      path: 'projects/workspace/config/browser-product-comparison-policy.json',
      sha256: repoFileSha256('projects/workspace/config/browser-product-comparison-policy.json'),
    },
    serviceSource: treeDigest('projects/workspace/src'),
    runtimeSelector: { path: 'projects/workspace/src/browser-launch.js',
      sha256: repoFileSha256('projects/workspace/src/browser-launch.js') },
    harness: treeDigest('projects/workspace/qualification'),
    packageLock: { path: 'projects/workspace/package-lock.json', sha256: repoFileSha256('projects/workspace/package-lock.json') },
    fixtureSite: {
      path: 'projects/workspace/qualification/fixture-site.js',
      sha256: repoFileSha256('projects/workspace/qualification/fixture-site.js'),
    },
    node: process.version,
    playwrightCore: require('playwright-core/package.json').version,
    os: { platform: platform(), release: release(), arch: arch() },
    git: gitState(),
  };
}

export {
  REPO_ROOT,
  descendants,
  executableIdentityKey,
  gitState,
  inspectBrowserProcesses,
  repoFileSha256,
  resultIdentity,
  sha256File,
  treeDigest,
  waitForProfileRelease,
};
