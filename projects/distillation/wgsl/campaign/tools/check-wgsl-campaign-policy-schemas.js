#!/usr/bin/env node
// Validate the campaign's policy-to-schema bindings.
//
// These entries moved out of Doppler's src/config/schema/policy-schema-registry.json
// with the campaign. Doppler's checker resolves paths against its own checkout,
// so this campaign-owned check applies the same entry rules relative to the
// working directory, which `node run.js` sets to the Doppler-namespace view.

import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

export const CAMPAIGN_REGISTRY_PATH = 'src/config/schema/wgsl-campaign-policy-schema-registry.json';
const ID_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const JSON_SCHEMA_2020_12 = 'https://json-schema.org/draft/2020-12/schema';

function text(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function isRepoRelativeJsonPath(value) {
  return Boolean(
    value
    && !path.isAbsolute(value)
    && !value.includes('\\')
    && !value.split('/').includes('..')
    && value.endsWith('.json')
  );
}

async function readExistingJson(root, relativePath, label, errors) {
  if (!isRepoRelativeJsonPath(relativePath)) {
    errors.push(`${label} must be a repo-relative JSON path`);
    return null;
  }
  try {
    return JSON.parse(await fs.readFile(path.join(root, relativePath), 'utf8'));
  } catch (error) {
    errors.push(`${label} is not readable JSON: ${relativePath} (${error.code || error.message})`);
    return null;
  }
}

export async function buildCampaignPolicySchemaReport(options = {}) {
  const root = path.resolve(options.root || process.cwd());
  const registryPath = options.registryPath || CAMPAIGN_REGISTRY_PATH;
  const errors = [];
  const registry = await readExistingJson(root, registryPath, 'registry', errors);
  const policies = Array.isArray(registry?.policies) ? registry.policies : [];
  if (registry && registry.schemaVersion !== 1) errors.push('registry schemaVersion must be 1');
  if (registry && registry.source !== 'gamma-wgsl-campaign') errors.push('registry source must be "gamma-wgsl-campaign"');
  if (registry && policies.length === 0) errors.push('registry policies must be a non-empty array');
  const seenIds = new Set();
  for (const entry of policies) {
    const id = text(entry?.id);
    if (!id) {
      errors.push('registry entry is missing id');
      continue;
    }
    if (!ID_PATTERN.test(id)) errors.push(`${id}: id must be lowercase kebab-case`);
    if (seenIds.has(id)) errors.push(`${id}: duplicate id`);
    seenIds.add(id);
    const policyPath = text(entry.policyPath);
    const schemaPath = text(entry.schemaPath);
    const [policy, schema] = await Promise.all([
      readExistingJson(root, policyPath, `${id}: policyPath`, errors),
      readExistingJson(root, schemaPath, `${id}: schemaPath`, errors),
    ]);
    if (!policy || !schema) continue;
    const expectedRef = path.relative(path.dirname(policyPath), schemaPath).replaceAll(path.sep, '/');
    if (text(policy.$schema) !== expectedRef) errors.push(`${id}: policy $schema must be ${expectedRef}`);
    if (schema.$schema !== JSON_SCHEMA_2020_12) errors.push(`${id}: schema must use JSON Schema 2020-12`);
    if (!text(schema.$id)) errors.push(`${id}: schema $id is required`);
    if (schema.additionalProperties !== false) errors.push(`${id}: schema must set additionalProperties false at root`);
  }
  return { ok: errors.length === 0, registryPath, policies: policies.length, errors };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const report = await buildCampaignPolicySchemaReport();
  console.log(JSON.stringify(report, null, 2));
  if (!report.ok) process.exitCode = 1;
}
