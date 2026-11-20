#!/usr/bin/env node
// Generate a build profile; the service rechecks artifact bytes before every launch.
import { createHash } from 'node:crypto';
import { readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { loadServiceConfig, validateServiceConfig } from '../src/config.js';
import { prepareFawnLaunch } from '../src/browser-launch.js';

const options = { dependencies: [] };
for (let index = 2; index < process.argv.length; index += 2) {
  const key = process.argv[index];
  const value = process.argv[index + 1];
  if (!['--executable', '--runtime', '--library', '--dependency', '--out'].includes(key) || !value || value.startsWith('--')) {
    throw new Error('usage: create-browser-profile.js --executable IMAGE --runtime doe-c|dawn [--library LIB --dependency FILE ...] --out NEW.json');
  }
  if (key === '--dependency') options.dependencies.push(value);
  else {
    if (options[key] !== undefined) throw new Error(`duplicate option ${key}`);
    options[key] = value;
  }
}
if (!options['--executable'] || !options['--out'] || !['doe-c', 'dawn'].includes(options['--runtime'])) {
  throw new Error('explicit executable, runtime and new output path are required');
}
if ((options['--runtime'] === 'doe-c') !== Boolean(options['--library'])) {
  throw new Error('only doe-c requires --library');
}
const artifact = path => ({ path: realpathSync.native(resolve(path)),
  sha256: createHash('sha256').update(readFileSync(path)).digest('hex') });
const config = structuredClone(loadServiceConfig());
config.browser = { ...config.browser, channel: 'fawn', fawnBuild: {
  executable: artifact(options['--executable']), dependencies: options.dependencies.map(artifact),
  runtime: { mode: options['--runtime'], ...(options['--library'] ? { library: artifact(options['--library']) } : {}) },
} };
validateServiceConfig(config);
prepareFawnLaunch(config.browser);
writeFileSync(resolve(options['--out']), `${JSON.stringify(config, null, 2)}\n`, { flag: 'wx', mode: 0o600 });
console.log(resolve(options['--out']));
