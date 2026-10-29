// Build the Doppler-namespace view this campaign executes in.
//
// Every campaign file was moved byte-for-byte from Doppler, and Doppler's frozen
// policies and receipts pin those bytes and address one repository namespace
// (tools/, src/, reports/, artifacts/, ...). The campaign therefore runs in a
// generated directory that reproduces that namespace:
//   - campaign files (docs/, src/, tests/, tools/ here) are hardlinked, so they
//     keep their exact bytes and module paths;
//   - every other entry is a symlink into the Doppler checkout (DOPPLER_ROOT);
//   - `.git` is a gitfile naming Doppler's git directory, so read-only git
//     commands (rev-parse, show, cat-file, merge-base) report Doppler identity.
// The directory is rebuilt on every launch and is never committed.

import { execFileSync } from 'node:child_process';
import {
  existsSync, linkSync, lstatSync, mkdirSync, readdirSync, readFileSync, rmSync, symlinkSync, writeFileSync,
} from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const CAMPAIGN_ROOT = dirname(fileURLToPath(import.meta.url));
export const NAMESPACE_ROOT = join(CAMPAIGN_ROOT, '.namespace');
const GAMMA_ROOT = resolve(CAMPAIGN_ROOT, '..', '..', '..', '..');
// Top-level Doppler directories that contain moved campaign files.
const MIRROR_ROOTS = ['docs', 'src', 'tests', 'tools'];

function git(cwd, args) {
  return execFileSync('git', ['-C', cwd, ...args], { encoding: 'utf8' }).trim();
}

export function resolveDopplerRoot() {
  const root = resolve(process.env.DOPPLER_ROOT || join(GAMMA_ROOT, '..', 'doppler'));
  const packagePath = join(root, 'package.json');
  if (!existsSync(packagePath)) {
    throw new Error(`wgsl_campaign_doppler_root_missing: no Doppler checkout at ${root}; set DOPPLER_ROOT`);
  }
  const name = JSON.parse(readFileSync(packagePath, 'utf8')).name;
  if (name !== 'doppler-gpu') {
    throw new Error(`wgsl_campaign_doppler_root_invalid: ${packagePath} names ${JSON.stringify(name)}, expected "doppler-gpu"`);
  }
  return root;
}

function sameBytes(left, right) {
  return readFileSync(left).equals(readFileSync(right));
}

function merge(relativeDir, dopplerRoot, counts) {
  const campaignDir = join(CAMPAIGN_ROOT, relativeDir);
  const dopplerDir = join(dopplerRoot, relativeDir);
  const namespaceDir = join(NAMESPACE_ROOT, relativeDir);
  mkdirSync(namespaceDir, { recursive: true });
  const campaignEntries = new Map(readdirSync(campaignDir, { withFileTypes: true }).map((entry) => [entry.name, entry]));
  const dopplerEntries = existsSync(dopplerDir) && lstatSync(dopplerDir).isDirectory() ? readdirSync(dopplerDir) : [];
  for (const name of dopplerEntries) {
    if (campaignEntries.has(name)) continue;
    symlinkSync(join(dopplerDir, name), join(namespaceDir, name));
    counts.dopplerLinks += 1;
  }
  for (const [name, entry] of campaignEntries) {
    const relativePath = join(relativeDir, name);
    if (entry.isDirectory()) {
      merge(relativePath, dopplerRoot, counts);
      continue;
    }
    const dopplerPath = join(dopplerRoot, relativePath);
    if (existsSync(dopplerPath) && !sameBytes(dopplerPath, join(CAMPAIGN_ROOT, relativePath))) {
      throw new Error(
        `wgsl_campaign_namespace_conflict: ${relativePath} differs between the campaign and the Doppler checkout`
      );
    }
    linkSync(join(CAMPAIGN_ROOT, relativePath), join(NAMESPACE_ROOT, relativePath));
    counts.campaignFiles += 1;
  }
}

export function buildNamespace() {
  const dopplerRoot = resolveDopplerRoot();
  rmSync(NAMESPACE_ROOT, { recursive: true, force: true });
  mkdirSync(NAMESPACE_ROOT);
  const counts = { campaignFiles: 0, dopplerLinks: 0 };
  for (const name of readdirSync(dopplerRoot)) {
    if (name === '.git' || MIRROR_ROOTS.includes(name)) continue;
    symlinkSync(join(dopplerRoot, name), join(NAMESPACE_ROOT, name));
    counts.dopplerLinks += 1;
  }
  for (const name of MIRROR_ROOTS) merge(name, dopplerRoot, counts);
  writeFileSync(join(NAMESPACE_ROOT, '.git'), `gitdir: ${git(dopplerRoot, ['rev-parse', '--absolute-git-dir'])}\n`);
  return {
    schema: 'gamma.wgsl-campaign-namespace.v1',
    namespace: relative(CAMPAIGN_ROOT, NAMESPACE_ROOT),
    dopplerHead: git(dopplerRoot, ['rev-parse', 'HEAD']),
    gammaHead: git(CAMPAIGN_ROOT, ['rev-parse', 'HEAD']),
    ...counts,
  };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  console.log(JSON.stringify(buildNamespace(), null, 2));
}
