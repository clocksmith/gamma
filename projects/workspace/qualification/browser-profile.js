// Bind an optional operator-selected browser build without changing the frozen
// service rules. This is launch identity, not proof of GPU provider ownership.
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { isDeepStrictEqual } from 'node:util';
import { loadServiceConfig, validateServiceConfig } from '../src/config.js';
import { REPO_ROOT } from './identity.js';
import { evidencePath } from './evidence-input.js';

const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const withoutBrowser = ({ browser, ...rest }) => rest;

function matchesSelectedBuild(config, observed) {
  const expected = config?.browser.fawnBuild?.executable.sha256;
  return !expected || (observed.length > 0 && observed.every(value => value.sha256 === expected));
}

function stageBrowserProfile(source, output) {
  if (!source) return null;
  const bytes = readFileSync(source);
  const config = validateServiceConfig(JSON.parse(bytes));
  if (!isDeepStrictEqual(withoutBrowser(config), withoutBrowser(loadServiceConfig()))) {
    throw new Error('qualification browser profile may change only browser configuration');
  }
  const path = join(output, 'browser-config.json');
  writeFileSync(path, bytes, { flag: 'wx' });
  writeFileSync(join(output, 'service-config-base.json'), readFileSync(join(REPO_ROOT, 'projects/workspace/config/fawn-workspace-service.json')), { flag: 'wx' });
  return { path, identity: { path: 'browser-config.json', sha256: digest(bytes) }, config };
}

function profileFailures(resultDir, result) {
  const ref = result.identity.browserLaunchConfig;
  if (!ref) return result.browserChannel === 'fawn' ? ['Fawn build profile is missing'] : [];
  try {
    const bytes = readFileSync(evidencePath(resultDir, ref.path, result.identity.os.platform));
    if (digest(bytes) !== ref.sha256) return ['browser profile hash differs from its receipt'];
    const baseBytes = readFileSync(evidencePath(resultDir, 'service-config-base.json', result.identity.os.platform));
    if (digest(baseBytes) !== result.identity.serviceConfig.sha256) return ['frozen base service config hash differs'];
    const config = validateServiceConfig(JSON.parse(bytes), { platform: result.identity.os.platform });
    if (!isDeepStrictEqual(withoutBrowser(config), withoutBrowser(JSON.parse(baseBytes)))) {
      return ['browser profile changed frozen service rules'];
    }
    if (result.browserChannel !== config.browser.channel) return ['browser channel differs from profile'];
    if (result.headless !== config.browser.headless) return ['headless selection differs from profile'];
    if (config.browser.channel !== 'fawn') return [];
    const roots = result.runs.flatMap(run => run.inspections ?? []).flatMap(value => value.executables ?? []);
    if (!roots.length) return ['no observed browser executable for Fawn build'];
    if (!matchesSelectedBuild(config, roots)) {
      return ['observed browser executable differs from selected Fawn build'];
    }
    return [];
  } catch (error) {
    return [`invalid browser profile evidence: ${error.message}`];
  }
}

export { stageBrowserProfile, profileFailures, matchesSelectedBuild };
