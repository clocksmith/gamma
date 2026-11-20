import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync, realpathSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadServiceConfig, validateServiceConfig } from '../../src/config.js';
import { prepareFawnLaunch, validateFawnBuild, playwrightLaunchOptions } from '../../src/browser-launch.js';
import { stageBrowserProfile, profileFailures, matchesSelectedBuild } from '../../qualification/browser-profile.js';
import { forcedRuntimeArgs } from '../../../chromium/scripts/browser-runtime-selector.mjs';

const root = realpathSync.native(mkdtempSync(join(tmpdir(), 'fawn-build-')));
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const clone = value => structuredClone(value);
const artifact = name => {
  const path = join(root, name);
  writeFileSync(path, name);
  return { path, sha256: digest(name) };
};
try {
  const config = clone(loadServiceConfig());
  assert.equal(prepareFawnLaunch(config.browser), null);
  assert.deepEqual(playwrightLaunchOptions(config.browser), { channel: undefined });
  assert.deepEqual(playwrightLaunchOptions({ ...config.browser, channel: 'chrome' }), { channel: 'chrome' });
  assert.throws(() => playwrightLaunchOptions({ ...config.browser, channel: 'unrecognized' }));
  config.browser.channel = 'fawn';
  config.browser.fawnBuild = { executable: artifact('Chromium ü image'),
    dependencies: [artifact('compiler library')], runtime: { mode: 'doe-c', library: artifact('Doe C library') } };
  validateServiceConfig(config);
  const launch = prepareFawnLaunch(config.browser);
  assert.deepEqual(playwrightLaunchOptions(config.browser), { executablePath: launch.executablePath,
    args: launch.args, chromiumSandbox: true, ignoreDefaultArgs: ['--enable-unsafe-swiftshader'] });
  assert.equal(matchesSelectedBuild(config, [config.browser.fawnBuild.executable]), true);
  assert.equal(matchesSelectedBuild(config, [{ sha256: '0'.repeat(64) }]), false);
  assert.equal(matchesSelectedBuild(config, []), false);
  assert.deepEqual(launch.args.filter(value => value !== '--do-not-de-elevate'),
    ['--use-webgpu-runtime=doe', `--doe-webgpu-library-path=${config.browser.fawnBuild.runtime.library.path}`,
      ...(process.platform === 'linux' ? ['--gpu-sandbox-start-early'] : [])]);
  assert.equal(launch.identity.fallbackAllowed, false);
  assert.equal(launch.args.some(value => value.includes('no-sandbox')), false);
  for (const mutate of [
    value => { value.channel = 'chrome'; },
    value => { delete value.fawnBuild; },
    value => { value.fawnBuild.runtime.mode = 'auto'; },
    value => { value.fawnBuild.dependencies = []; },
    value => { value.fawnBuild.executable.path = 'relative'; },
    value => { value.fawnBuild.executable.sha256 = 'A'.repeat(64); },
    value => { value.fawnBuild.args = ['--no-sandbox']; },
    value => { value.args = ['--no-sandbox']; },
    value => { value.fawnBuild.runtime.extra = true; },
  ]) {
    const bad = clone(config.browser);
    mutate(bad);
    assert.throws(() => validateFawnBuild(bad));
  }
  for (const key of ['executable', 'library', 'dependency']) {
    const bad = clone(config.browser);
    const target = key === 'library' ? bad.fawnBuild.runtime.library
      : key === 'dependency' ? bad.fawnBuild.dependencies[0] : bad.fawnBuild.executable;
    target.sha256 = '0'.repeat(64);
    assert.throws(() => prepareFawnLaunch(bad), /SHA-256 mismatch/);
    target.path += '.missing';
    assert.throws(() => prepareFawnLaunch(bad), /ENOENT/);
  }
  const duplicate = clone(config.browser);
  duplicate.fawnBuild.dependencies.push(duplicate.fawnBuild.runtime.library);
  assert.throws(() => prepareFawnLaunch(duplicate), /distinct files/);
  const dawn = clone(config.browser);
  dawn.fawnBuild.runtime = { mode: 'dawn' };
  dawn.fawnBuild.dependencies = [];
  assert.deepEqual(prepareFawnLaunch(dawn).args.filter(value => value !== '--do-not-de-elevate'), ['--use-webgpu-runtime=dawn']);
  assert.throws(() => forcedRuntimeArgs('auto'));
  assert.throws(() => forcedRuntimeArgs('doe'));
  assert.deepEqual(forcedRuntimeArgs('doe', '/missing-negative-control'),
    ['--use-webgpu-runtime=doe', '--doe-webgpu-library-path=/missing-negative-control',
      ...(process.platform === 'linux' ? ['--gpu-sandbox-start-early'] : [])]);
  const old = clone(loadServiceConfig());
  old.schemaVersion = 3;
  validateServiceConfig(old);
  assert.throws(() => validateServiceConfig({ ...config, schemaVersion: 3 }), /4 for explicit Fawn builds/);
  const windows = clone(config.browser);
  windows.fawnBuild.executable.path = 'C:\\Program Files\\Fawn\\chrome.exe';
  windows.fawnBuild.dependencies[0].path = 'C:\\Program Files\\Fawn\\compiler.dll';
  windows.fawnBuild.runtime.library.path = 'C:\\Program Files\\Fawn\\doe.dll';
  validateFawnBuild(windows, { platform: 'win32' });
  windows.fawnBuild.executable.path = 'C:relative.exe';
  assert.throws(() => validateFawnBuild(windows, { platform: 'win32' }));
  const generated = join(root, 'generated.json');
  const cli = new URL('../../qualification/create-browser-profile.js', import.meta.url);
  const argv = [fileURLToPath(cli), '--executable', config.browser.fawnBuild.executable.path,
    '--runtime', 'doe-c', '--library', config.browser.fawnBuild.runtime.library.path,
    '--dependency', config.browser.fawnBuild.dependencies[0].path, '--out', generated];
  assert.equal(spawnSync(process.execPath, argv, { encoding: 'utf8' }).status, 0);
  assert.deepEqual(JSON.parse(readFileSync(generated)).browser, config.browser);
  assert.notEqual(spawnSync(process.execPath, argv, { encoding: 'utf8' }).status, 0);
  const modelOverride = spawnSync(process.execPath, [fileURLToPath(new URL('../../qualification/differentiate.js', import.meta.url)),
    '--suite', 'modelDrivenDifferentiation', '--mode', 'offline', '--browser-channel', 'chrome'], { encoding: 'utf8' });
  assert.notEqual(modelOverride.status, 0);
  assert.match(modelOverride.stderr, /frozen browser selection/);

  const source = join(root, 'profile.json');
  const out = join(root, 'evidence');
  mkdirSync(out);
  writeFileSync(source, JSON.stringify(config));
  const staged = stageBrowserProfile(source, out);
  const result = { browserChannel: 'fawn', headless: config.browser.headless, identity: { os: { platform: process.platform },
    browserLaunchConfig: staged.identity,
    serviceConfig: { sha256: digest(readFileSync(join(out, 'service-config-base.json'))) } },
    runs: [{ inspections: [{ executables: [{ sha256: config.browser.fawnBuild.executable.sha256 }] }] }] };
  assert.deepEqual(profileFailures(out, result), []);
  const changed = clone(config);
  changed.dispatch.actionTimeoutMs++;
  writeFileSync(source, JSON.stringify(changed));
  assert.throws(() => stageBrowserProfile(source, out), /only browser configuration/);
  const wrong = clone(result);
  wrong.runs[0].inspections[0].executables[0].sha256 = '0'.repeat(64);
  assert.match(profileFailures(out, wrong)[0], /differs from selected/);
  wrong.runs = [];
  assert.match(profileFailures(out, wrong)[0], /no observed/);
  const missing = clone(result);
  delete missing.identity.browserLaunchConfig;
  assert.match(profileFailures(out, missing)[0], /missing/);
  writeFileSync(join(out, 'browser-config.json'), 'tampered');
  assert.match(profileFailures(out, result)[0], /hash differs/);
  console.log('ok: explicit C/Dawn browser admission, closure integrity and frozen qualification profiles');
} finally {
  rmSync(root, { recursive: true, force: true });
}
