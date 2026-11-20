// Blitzen workspace launch defaults to stock Chrome; an explicitly requested Fawn build has no fallback.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { isDeepStrictEqual } from 'node:util';
import { loadServiceConfig, validateServiceConfig } from '../config.js';
import { prepareFawnLaunch } from '../browser-launch.js';

export function loadClientServiceConfig({ directory, browserConfig, browserChannel, headless }) {
  const effectiveChannel = browserChannel ?? (browserConfig ? 'fawn' : 'chrome');
  if (effectiveChannel !== 'fawn') {
    if (browserConfig) throw Error('Choose a Fawn browser profile or an explicit stock channel, not both');
    return loadServiceConfig(undefined, { browserChannel: effectiveChannel, headless });
  }
  const path = browserConfig ?? join(directory, 'browser-profile.json');
  let profile;
  try { profile = JSON.parse(readFileSync(path, 'utf8')); }
  catch (error) {
    if (error.code === 'ENOENT') throw Error(`Fawn browser profile missing: ${path}. Create it with qualification/create-browser-profile.js or select --browser-config. No stock-browser fallback.`);
    throw error;
  }
  const { browser, ...policy } = validateServiceConfig(profile);
  const { browser: _baseBrowser, ...basePolicy } = loadServiceConfig();
  if (!isDeepStrictEqual(policy, basePolicy)) throw Error('Browser profile may change only browser configuration');
  if (browser.channel !== 'fawn') throw Error('Selected Fawn browser profile must select channel "fawn"');
  const config = validateServiceConfig({ ...profile, browser: { ...browser,
    ...(headless === undefined ? {} : { headless }) } });
  prepareFawnLaunch(config.browser);
  return config;
}
