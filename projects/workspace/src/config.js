// Fawn workspace — service configuration
//
// Loads config/fawn-workspace-service.json; every tunable the service uses comes from it.

import { readFileSync } from 'node:fs';
import { REJECTION_CODES, workspaceError } from './errors.js';
import { BROWSER_CHANNELS, validateFawnBuild } from './browser-launch.js';

const DEFAULT_CONFIG_URL = new URL('../config/fawn-workspace-service.json', import.meta.url);
const SUPPORTED_SCHEMA_VERSION = 5;
const SUPPORTED_PROTOCOL_VERSION = 4;

const POSITIVE_INTEGER_FIELDS = Object.freeze([
  'credentials.secretBytes',
  'observation.maxAgeMs',
  'observation.maxTextChars',
  'observation.maxElements',
  'observation.maxRegions',
  'dispatch.actionTimeoutMs',
  'dispatch.completionTimeoutMs',
  'dispatch.completionPollMs',
  'dispatch.valueSettleMs',
]);

const NON_EMPTY_LIST_FIELDS = Object.freeze([
  'actionKinds',
  'observationScopes',
  'observationViews',
  'conditionKinds',
  'reconciliationMethods',
]);

function readPath(object, dottedPath) {
  return dottedPath.split('.').reduce((value, key) => (value == null ? undefined : value[key]), object);
}

function invalid(path, expected, received) {
  return workspaceError(REJECTION_CODES.INVALID_CONFIG, `${path}: expected ${expected}`, {
    path,
    expected,
    received,
  });
}

/**
 * Validate a parsed service config; the JSON schema in config/ is the canonical contract.
 * @param {object} config
 */
function validateServiceConfig(config, { platform = process.platform } = {}) {
  if (![3, 4, SUPPORTED_SCHEMA_VERSION].includes(config?.schemaVersion)) {
    throw invalid('schemaVersion', SUPPORTED_SCHEMA_VERSION, config?.schemaVersion);
  }
  if (![3, SUPPORTED_PROTOCOL_VERSION].includes(config.protocolVersion)) {
    throw invalid('protocolVersion', SUPPORTED_PROTOCOL_VERSION, config.protocolVersion);
  }
  for (const field of POSITIVE_INTEGER_FIELDS) {
    const value = readPath(config, field);
    if (!Number.isInteger(value) || value < 1) throw invalid(field, 'positive integer', value);
  }
  if (config.schemaVersion >= 5 || config.actionKinds?.includes('upload')) {
    for (const field of ['maxFilesPerAction', 'maxFileBytes', 'maxStagedBytes', 'maxNameBytes']) {
      if (!Number.isSafeInteger(config.uploads?.[field]) || config.uploads[field] < 1) {
        throw invalid(`uploads.${field}`, 'positive safe integer', config.uploads?.[field]);
      }
    }
    if (config.uploads.maxStagedBytes < config.uploads.maxFileBytes) throw invalid('uploads.maxStagedBytes', 'at least maxFileBytes', config.uploads.maxStagedBytes);
  }
  for (const field of NON_EMPTY_LIST_FIELDS) {
    const value = config[field];
    if (!Array.isArray(value) || value.length === 0) throw invalid(field, 'non-empty array', value);
  }
  for (const field of ['journal.fileName', 'journal.lockFileName']) {
    const value = readPath(config, field);
    if (typeof value !== 'string' || !/^[a-z0-9.-]+$/.test(value)) {
      throw invalid(field, 'plain file name', value);
    }
  }
  if (config.browser?.engine !== 'chromium') throw invalid('browser.engine', 'chromium', config.browser?.engine);
  if (typeof config.browser?.headless !== 'boolean') throw invalid('browser.headless', 'boolean', config.browser?.headless);
  if (config.browser?.transport !== 'pipe') throw invalid('browser.transport', 'pipe', config.browser?.transport);
  if (!BROWSER_CHANNELS.includes(config.browser?.channel)) throw invalid('browser.channel', BROWSER_CHANNELS.join(' | '), config.browser?.channel);
  if (config.schemaVersion === 3 && (config.browser.channel === 'fawn' || config.browser.fawnBuild !== undefined)) {
    throw invalid('schemaVersion', '4 for explicit Fawn builds', config.schemaVersion);
  }
  try { validateFawnBuild(config.browser, { platform }); }
  catch (error) { throw invalid('browser.fawnBuild', error.message, config.browser?.fawnBuild); }
  if (config.browser?.persistentProfiles !== true) {
    throw invalid('browser.persistentProfiles', true, config.browser?.persistentProfiles);
  }
  return Object.freeze(config);
}

/**
 * @param {URL} [configUrl]
 * @param {{browserChannel?: string, headless?: boolean}} [overrides] a compatibility run may name
 *   another browser channel or a headed session
 */
function loadServiceConfig(configUrl = DEFAULT_CONFIG_URL, { browserChannel, headless } = {}) {
  const config = JSON.parse(readFileSync(configUrl, 'utf8'));
  if (browserChannel) config.browser = { ...config.browser, channel: browserChannel };
  if (headless !== undefined) config.browser = { ...config.browser, headless };
  return validateServiceConfig(config);
}

export { loadServiceConfig, validateServiceConfig };
