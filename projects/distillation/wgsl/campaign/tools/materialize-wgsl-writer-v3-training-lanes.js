#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const SOURCE = 'reports/training/wgsl-writer/doppler-wgsl-writer-v3/corpus-v1/train.jsonl';
const OUTPUT_ROOT = 'reports/training/wgsl-writer/doppler-wgsl-writer-v3/training-lanes-v1';

function parseArgs(argv) {
  const args = { source: SOURCE, outputRoot: OUTPUT_ROOT };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--source') args.source = argv[++index] || '';
    else if (token === '--out-root') args.outputRoot = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.source || !args.outputRoot) {
    throw new Error('--source and --out-root require values.');
  }
  return args;
}

function sha256(value) {
  return createHash('sha256').update(value).digest('hex');
}

async function readJsonl(filePath) {
  return (await fs.readFile(filePath, 'utf8')).trim().split('\n').filter(Boolean).map(JSON.parse);
}

function toJsonl(rows) {
  return `${rows.map((row) => JSON.stringify(row)).join('\n')}\n`;
}

function corruptedPackage(row, ordinal) {
  const value = JSON.parse(row.completion);
  const mode = ordinal % 6;
  if (mode === 0) value.outputs = [];
  if (mode === 1 && value.passes[0]?.bindings?.[0]) {
    value.passes[0].bindings[0].shaderName = 'missing_binding_name';
  }
  if (mode === 2 && value.passes[0]?.kind === 'compute') {
    value.passes[0].entryPoints.compute = 'missing_compute_main';
  }
  if (mode === 2 && value.passes[0]?.kind === 'render') {
    value.passes[0].entryPoints.fragment = 'missing_fragment_main';
  }
  if (mode === 3) value.requirements.features = ['unavailable-training-sentinel'];
  if (mode === 4 && value.resources[0]) value.resources[0].ownership = 'generated';
  if (mode === 5 && value.passes[0]?.kind === 'compute') {
    value.passes[0].dispatch.x = { kind: 'literal', value: 0 };
  }
  if (mode === 5 && value.passes[0]?.kind === 'render') {
    value.passes[0].draw.vertexCount = { kind: 'literal', value: 0 };
  }
  return JSON.stringify(value);
}

function repairPrompt(row, ordinal) {
  const failureKinds = [
    'output_required',
    'wgsl_declaration_missing',
    'entry_point_missing',
    'feature_unavailable',
    'host_ownership_contract_mismatch',
    'dispatch_or_draw_produced_no_output',
  ];
  return [
    'Repair one failed executable WebGPU shader package.',
    'Return the corrected doppler.wgsl-author-package/v1 JSON object only; no Markdown or explanation.',
    '<original_request>',
    row.prompt,
    '</original_request>',
    '<failed_package>',
    corruptedPackage(row, ordinal),
    '</failed_package>',
    `<failure>${failureKinds[ordinal % failureKinds.length]}</failure>`,
  ].join('\n');
}

function materializeRepair(rows) {
  const familyOrdinal = new Map();
  return rows.map((row) => {
    const ordinal = familyOrdinal.get(row.semanticFamilyId) || 0;
    familyOrdinal.set(row.semanticFamilyId, ordinal + 1);
    if (ordinal >= 6) return { ...row, lane: 'repair_mixed_sft' };
    const prompt = repairPrompt(row, ordinal);
    return {
      ...row,
      schema: 'doppler.wgsl-writer-v3-repair-row/v1',
      rowId: `${row.rowId}-repair`,
      taskId: `${row.taskId}-repair`,
      prompt,
      promptSha256: sha256(prompt),
      lane: 'repair_mixed_sft',
      repairFailureOrdinal: ordinal,
    };
  });
}

function materializeControl(rows) {
  const families = [...new Set(rows.map((row) => row.semanticFamilyId))];
  const rowsByFamily = new Map(families.map((family) => [
    family,
    rows.filter((row) => row.semanticFamilyId === family),
  ]));
  return rows.map((row, index) => {
    const familyIndex = families.indexOf(row.semanticFamilyId);
    const donorFamily = families[(familyIndex + 1) % families.length];
    const donorRows = rowsByFamily.get(donorFamily);
    const donor = donorRows[index % donorRows.length];
    return {
      ...row,
      schema: 'doppler.wgsl-writer-v3-control-row/v1',
      completion: donor.completion,
      completionSha256: donor.completionSha256,
      packageSha256: donor.packageSha256,
      lane: 'count_matched_mismatched_control',
      donorSemanticFamilyId: donorFamily,
      capabilityAuthority: false,
    };
  });
}

export async function materializeTrainingLanes(options = {}) {
  const source = options.source || SOURCE;
  const outputRoot = options.outputRoot || OUTPUT_ROOT;
  const sourceRows = await readJsonl(source);
  const lanes = {
    package_sft: sourceRows.map((row) => ({ ...row, lane: 'package_sft' })),
    repair_mixed_sft: materializeRepair(sourceRows),
    count_matched_control: materializeControl(sourceRows),
  };
  await fs.mkdir(outputRoot, { recursive: true });
  const bindings = {};
  for (const [lane, rows] of Object.entries(lanes)) {
    const filePath = path.join(outputRoot, `${lane.replaceAll('_', '-')}.jsonl`);
    const contents = toJsonl(rows);
    await fs.writeFile(filePath, contents, 'utf8');
    bindings[lane] = {
      path: filePath,
      sha256: sha256(contents),
      rows: rows.length,
      semanticFamilies: new Set(rows.map((row) => row.semanticFamilyId)).size,
      completionTokenMultisetSource: source,
    };
  }
  const sourceBytes = await fs.readFile(source);
  const core = {
    schema: 'doppler.wgsl-writer-v3-training-lanes/v1',
    source: { path: source, sha256: sha256(sourceBytes), rows: sourceRows.length },
    transform: {
      package_sft: 'identity',
      repair_mixed_sft: 'six_deterministic_failure_repairs_per_family_plus_eighteen_identity_rows',
      count_matched_control: 'next_family_completion_permutation',
    },
    matching: {
      rowsPerLane: sourceRows.length,
      completionMultisetIdenticalForPackageAndRepair: true,
      updateBudgetIdentical: true,
      controlCapabilityAuthority: false,
    },
    lanes: bindings,
    claimBoundary: 'The derived lanes freeze matched row and supervised-completion budgets. The mismatched control has no capability authority.',
  };
  const manifest = { ...core, manifestSha256: sha256(JSON.stringify(core)) };
  const manifestPath = path.join(outputRoot, 'manifest.json');
  await fs.writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
  return { manifestPath, manifest, rows: sourceRows.length };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  materializeTrainingLanes(parseArgs(process.argv.slice(2))).then((result) => {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  }).catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
