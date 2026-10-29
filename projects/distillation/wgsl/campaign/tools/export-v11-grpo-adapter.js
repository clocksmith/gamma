#!/usr/bin/env node

import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readdir, readFile, stat, writeFile, mkdir } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { loadLoRAFromManifest } from '../src/experimental/adapters/lora-loader.js';
import { exportLoRAAdapter } from '../src/experimental/training/export.js';
import { readGammaAdapterTensors } from './trainers/gamma-wgsl-trainer.js';

const ROOT = path.resolve(import.meta.dirname, '..');
const POLICY_PATH = path.join(ROOT, 'tools/policies/wgsl-repair-v11-policy.json');
const STATUS_PATH = path.join(ROOT, 'docs/status/wgsl-repair-v11-2026-07-12.json');
const SOURCE_ADAPTER_SUFFIX = 'gamma/grpo/adapter/adapter_model.safetensors';
const EXPORT_ID = 'doppler-wgsl-qwen35-9b-v11-grpo-seed11';
const WEIGHTS_FILENAME = `${EXPORT_ID}.adapters.safetensors`;
const MANIFEST_FILENAME = `${EXPORT_ID}.adapter.manifest.json`;

function parseArgs(argv) {
  const args = {
    adapterDir: null,
    outputDir: null,
    receiptPath: null,
    help: false,
  };
  for (let index = 2; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--help' || arg === '-h') {
      args.help = true;
      continue;
    }
    if (arg === '--adapter-dir') {
      args.adapterDir = argv[++index] ?? null;
      continue;
    }
    if (arg === '--output-dir') {
      args.outputDir = argv[++index] ?? null;
      continue;
    }
    if (arg === '--receipt') {
      args.receiptPath = argv[++index] ?? null;
      continue;
    }
    throw new Error(`Unknown argument "${arg}".`);
  }
  if (!args.help && (!args.adapterDir || !args.outputDir)) {
    throw new Error('--adapter-dir and --output-dir are required.');
  }
  return args;
}

function printHelp() {
  console.log([
    'Usage: node tools/export-v11-grpo-adapter.js --adapter-dir <path> --output-dir <path> [options]',
    '',
    'Exports the exact checked-in V11 seed-11 GRPO PEFT adapter into Doppler LoRA format.',
    '',
    'Options:',
    '  --adapter-dir <path>  Gamma/PEFT adapter directory containing adapter_model.safetensors',
    '  --output-dir <path>   Destination for Doppler manifest, weights, and receipt',
    '  --receipt <path>      Override the receipt path',
    '  --help, -h            Show this help',
  ].join('\n'));
}

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function run(command, args) {
  try {
    return execFileSync(command, args, {
      cwd: ROOT,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
  } catch {
    return null;
  }
}

function hostMetadata() {
  const cpus = os.cpus();
  let metal = null;
  if (process.platform === 'darwin') {
    let adapter = null;
    try {
      const displays = JSON.parse(run('system_profiler', ['SPDisplaysDataType', '-json']));
      const entry = displays?.SPDisplaysDataType?.[0] ?? null;
      adapter = entry ? {
        name: entry._name ?? null,
        model: entry.sppci_model ?? null,
        gpuCoreCount: Number(entry.sppci_cores) || null,
        metalFamilySupport: entry.spdisplays_mtlgpufamilysupport ?? null,
      } : null;
    } catch {
      adapter = null;
    }
    metal = {
      productVersion: run('sw_vers', ['-productVersion']),
      buildVersion: run('sw_vers', ['-buildVersion']),
      adapter,
    };
  }
  return {
    platform: process.platform,
    arch: process.arch,
    osRelease: os.release(),
    nodeVersion: process.version,
    cpuModel: cpus?.[0]?.model ?? null,
    logicalCpuCount: cpus?.length ?? null,
    totalMemoryBytes: os.totalmem(),
    metal,
  };
}

function invocationMetadata() {
  const script = path.relative(ROOT, path.resolve(process.argv[1]));
  return {
    workingDirectory: 'repository root',
    executable: 'node',
    script,
    argv: process.argv.slice(2),
    command: ['node', script, ...process.argv.slice(2)],
  };
}

async function inspectDirectory(directory) {
  const entries = (await readdir(directory, { withFileTypes: true }))
    .filter((entry) => entry.isFile())
    .sort((left, right) => left.name.localeCompare(right.name));
  const files = [];
  for (const entry of entries) {
    const absolutePath = path.join(directory, entry.name);
    const bytes = await readFile(absolutePath);
    files.push({
      filename: entry.name,
      bytes: bytes.byteLength,
      sha256: sha256(bytes),
    });
  }
  return files;
}

function validateTensorPairs(tensors, expectedRank, allowedModules) {
  const pairs = new Map();
  for (const tensor of tensors) {
    const match = tensor.name.match(/^layers\.(\d+)\.([^.]+)\.lora_([ab])$/);
    if (!match) {
      throw new Error(`Unexpected normalized adapter tensor name: ${tensor.name}.`);
    }
    const [, layer, moduleName, kind] = match;
    if (!allowedModules.includes(moduleName)) {
      throw new Error(`V11 adapter contains unapproved target module "${moduleName}".`);
    }
    const key = `${layer}.${moduleName}`;
    const pair = pairs.get(key) ?? {};
    if (pair[kind]) {
      throw new Error(`Duplicate V11 adapter tensor ${key}.lora_${kind}.`);
    }
    pair[kind] = tensor;
    pairs.set(key, pair);
  }
  for (const [key, pair] of pairs) {
    if (!pair.a || !pair.b) {
      throw new Error(`Incomplete V11 adapter pair for ${key}.`);
    }
    if (pair.a.shape?.[1] !== expectedRank || pair.b.shape?.[0] !== expectedRank) {
      throw new Error(`V11 adapter rank mismatch for ${key}; expected ${expectedRank}.`);
    }
  }
  return {
    tensorCount: tensors.length,
    pairCount: pairs.size,
    layers: [...new Set([...pairs.keys()].map((key) => Number(key.split('.')[0])))].sort((a, b) => a - b),
    targetModules: [...new Set([...pairs.keys()].map((key) => key.split('.')[1]))].sort(),
  };
}

async function loadContracts() {
  const [policyBytes, statusBytes] = await Promise.all([
    readFile(POLICY_PATH),
    readFile(STATUS_PATH),
  ]);
  const policy = JSON.parse(policyBytes.toString('utf8'));
  const status = JSON.parse(statusBytes.toString('utf8'));
  const sourceArtifact = status.sourceArtifacts?.find((entry) => (
    entry.path?.endsWith(SOURCE_ADAPTER_SUFFIX)
  ));
  if (!sourceArtifact?.sha256) {
    throw new Error('V11 status does not declare the GRPO adapter SHA-256.');
  }
  return {
    policy,
    policySha256: sha256(policyBytes),
    statusSha256: sha256(statusBytes),
    sourceArtifact,
  };
}

export async function exportV11GrpoAdapter(options) {
  const adapterDir = path.resolve(options.adapterDir);
  const outputDir = path.resolve(options.outputDir);
  const manifestReceiptPath = path.join(options.outputDir, MANIFEST_FILENAME);
  const weightsReceiptPath = path.join(options.outputDir, WEIGHTS_FILENAME);
  const receiptPath = path.resolve(
    options.receiptPath ?? path.join(outputDir, `${EXPORT_ID}.export.receipt.json`)
  );
  const contracts = await loadContracts();
  const adapterConfig = contracts.policy.trainer.adapter;
  const sourceFiles = await inspectDirectory(adapterDir);
  const sourceWeights = sourceFiles.find((entry) => entry.filename === 'adapter_model.safetensors');
  if (!sourceWeights) {
    throw new Error(`Missing ${path.join(adapterDir, 'adapter_model.safetensors')}.`);
  }
  if (sourceWeights.sha256 !== contracts.sourceArtifact.sha256) {
    throw new Error(
      `V11 GRPO adapter SHA-256 mismatch: expected ${contracts.sourceArtifact.sha256}, got ${sourceWeights.sha256}.`
    );
  }

  const tensors = await readGammaAdapterTensors(adapterDir);
  const tensorSummary = validateTensorPairs(
    tensors,
    adapterConfig.rank,
    adapterConfig.targetModules
  );
  const exported = await exportLoRAAdapter({
    id: EXPORT_ID,
    name: 'Doppler WGSL Repair V11 GRPO Seed 11',
    description: 'Runtime export of the frozen V11 seed-11 GRPO adapter.',
    baseModel: contracts.policy.models.primary.modelId,
    rank: adapterConfig.rank,
    alpha: adapterConfig.alpha,
    targetModules: adapterConfig.targetModules,
    tensors,
    weightsFormat: 'safetensors',
    weightsPath: WEIGHTS_FILENAME,
    pretty: true,
    metadata: {
      policyId: contracts.policy.policyId,
      sourceRevision: contracts.policy.models.primary.revision,
      sourceAdapterSha256: sourceWeights.sha256,
      trainingClaimBoundary: contracts.policy.claimBoundary,
    },
  });
  if (!exported.weights) {
    throw new Error('Doppler V11 adapter export returned no weights.');
  }

  await mkdir(outputDir, { recursive: true });
  const manifestPath = path.join(outputDir, MANIFEST_FILENAME);
  const weightsPath = path.join(outputDir, WEIGHTS_FILENAME);
  await Promise.all([
    writeFile(manifestPath, exported.json, 'utf8'),
    writeFile(weightsPath, new Uint8Array(exported.weights)),
  ]);
  await loadLoRAFromManifest(exported.manifest, {
    readFile: async (filePath) => readFile(path.join(outputDir, filePath)),
  });

  const manifestBytes = await readFile(manifestPath);
  const weightsStats = await stat(weightsPath);
  const receipt = {
    artifactKind: 'v11_grpo_runtime_adapter_export_receipt',
    schemaVersion: 1,
    ok: true,
    recordedAt: new Date().toISOString(),
    dopplerCommit: run('git', ['rev-parse', 'HEAD']),
    host: hostMetadata(),
    invocation: invocationMetadata(),
    source: {
      adapterDir: options.adapterDir,
      files: sourceFiles,
      expectedWeightsSha256: contracts.sourceArtifact.sha256,
      statusPath: path.relative(ROOT, STATUS_PATH),
      statusSha256: contracts.statusSha256,
      policyPath: path.relative(ROOT, POLICY_PATH),
      policySha256: contracts.policySha256,
      policyId: contracts.policy.policyId,
      modelId: contracts.policy.models.primary.modelId,
      sourceRevision: contracts.policy.models.primary.revision,
      rank: adapterConfig.rank,
      alpha: adapterConfig.alpha,
      targetModules: adapterConfig.targetModules,
    },
    normalizedTensors: tensorSummary,
    output: {
      manifestPath: manifestReceiptPath,
      manifestSha256: sha256(manifestBytes),
      weightsPath: weightsReceiptPath,
      weightsBytes: weightsStats.size,
      weightsSha256: exported.weightsSha256,
      declaredWeightsSha256: exported.manifest.checksum,
      roundTripLoadPassed: true,
      manifestIdentity: {
        id: exported.manifest.id,
        name: exported.manifest.name,
        baseModel: exported.manifest.baseModel,
        rank: exported.manifest.rank,
        alpha: exported.manifest.alpha,
        targetModules: exported.manifest.targetModules,
      },
    },
    runtimeConfiguration: {
      operation: 'cpu_adapter_export',
      gpuUsed: false,
    },
    inferenceEvidence: {
      status: 'not_run',
      reason: 'Base-model token parity gates adapter activation and inference.',
      promptTokenIds: null,
      firstTokenLogits: null,
      selectedToken: null,
      generatedOutput: null,
    },
    claimBoundary: {
      trainingImprovement: 'Referenced from the checked-in V11 receipt; not re-evaluated by this export.',
      baseModelInferenceCorrectness: 'Not established by adapter export.',
      adapterInferenceCorrectness: 'Not established until deterministic local activation and inference pass.',
      runtimePerformance: 'Not measured.',
    },
  };
  await mkdir(path.dirname(receiptPath), { recursive: true });
  await writeFile(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return { receipt, receiptPath, manifestPath, weightsPath };
}

async function main() {
  let args = null;
  try {
    args = parseArgs(process.argv);
    if (args.help) {
      printHelp();
      return;
    }
    const result = await exportV11GrpoAdapter(args);
    console.log(result.receiptPath);
  } catch (error) {
    if (args?.outputDir) {
      const outputDir = path.resolve(args.outputDir);
      const receiptPath = path.resolve(
        args.receiptPath ?? path.join(outputDir, `${EXPORT_ID}.export.receipt.json`)
      );
      const failure = {
        artifactKind: 'v11_grpo_runtime_adapter_export_receipt',
        schemaVersion: 1,
        ok: false,
        recordedAt: new Date().toISOString(),
        dopplerCommit: run('git', ['rev-parse', 'HEAD']),
        host: hostMetadata(),
        invocation: invocationMetadata(),
        source: {
          adapterDir: args.adapterDir,
        },
        error: {
          name: error?.name ?? 'Error',
          message: error instanceof Error ? error.message : String(error),
          code: error?.code ?? null,
        },
        inferenceEvidence: {
          status: 'not_run',
          reason: 'Adapter export failed before the base-model parity gate could permit activation.',
          promptTokenIds: null,
          firstTokenLogits: null,
          selectedToken: null,
          generatedOutput: null,
        },
        claimBoundary: {
          trainingImprovement: 'Not re-evaluated.',
          baseModelInferenceCorrectness: 'Not evaluated.',
          adapterInferenceCorrectness: 'Not established.',
          runtimePerformance: 'Not measured.',
        },
      };
      await mkdir(path.dirname(receiptPath), { recursive: true });
      await writeFile(receiptPath, `${JSON.stringify(failure, null, 2)}\n`, 'utf8');
    }
    throw error;
  }
}

const entryPath = process.argv[1] ? path.resolve(process.argv[1]) : null;
if (entryPath && fileURLToPath(import.meta.url) === entryPath) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
}
