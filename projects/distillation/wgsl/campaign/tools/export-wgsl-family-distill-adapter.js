#!/usr/bin/env node

import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { loadLoRAFromManifest } from '../src/experimental/adapters/lora-loader.js';
import { exportLoRAAdapter } from '../src/experimental/training/export.js';
import { readGammaAdapterTensors } from './trainers/gamma-wgsl-trainer.js';

const ROOT = path.resolve(import.meta.dirname, '..');
const POLICY_PATH = path.join(ROOT, 'tools/policies/wgsl-writer-family-distillation-policy.json');

function parseArgs(argv) {
  const args = { arm: '', adapterDir: '', outputDir: '' };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--arm') args.arm = argv[++index] || '';
    else if (token === '--adapter-dir') args.adapterDir = argv[++index] || '';
    else if (token === '--output-dir') args.outputDir = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  for (const [key, value] of Object.entries(args)) {
    if (!value) throw new Error(`--${key.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`)} is required`);
  }
  return args;
}

function sha256(value) {
  return createHash('sha256').update(value).digest('hex');
}

export function validateTensorPairs(tensors, expectedRank, allowedModules) {
  const pairs = new Map();
  for (const tensor of tensors) {
    const match = tensor.name.match(/^layers\.(\d+)\.([^.]+)\.lora_([ab])$/);
    if (!match) throw new Error(`Unexpected normalized tensor: ${tensor.name}`);
    const [, layer, moduleName, factor] = match;
    if (!allowedModules.includes(moduleName)) {
      throw new Error(`Adapter contains undeclared target module: ${moduleName}`);
    }
    const key = `${layer}.${moduleName}`;
    const pair = pairs.get(key) || {};
    if (pair[factor]) throw new Error(`Duplicate adapter factor: ${key}.lora_${factor}`);
    pair[factor] = tensor;
    pairs.set(key, pair);
  }
  for (const [key, pair] of pairs) {
    if (!pair.a || !pair.b) throw new Error(`Incomplete adapter pair: ${key}`);
    if (pair.a.shape[1] !== expectedRank || pair.b.shape[0] !== expectedRank) {
      throw new Error(`Adapter rank mismatch for ${key}`);
    }
  }
  return {
    tensors: tensors.length,
    pairs: pairs.size,
    layers: [...new Set([...pairs.keys()].map((key) => Number(key.split('.')[0])))].sort((a, b) => a - b),
    targetModules: [...new Set([...pairs.keys()].map((key) => key.split('.')[1]))].sort(),
  };
}

export async function exportFamilyDistillAdapter(options) {
  const [policyBytes, adapterConfigBytes, sourceWeights] = await Promise.all([
    readFile(POLICY_PATH),
    readFile(path.join(path.resolve(options.adapterDir), 'adapter_config.json')),
    readFile(path.join(path.resolve(options.adapterDir), 'adapter_model.safetensors')),
  ]);
  const policy = JSON.parse(policyBytes.toString('utf8'));
  const arm = policy.arms.find((entry) => entry.id === options.arm);
  if (!arm) throw new Error(`Unknown family-distillation arm: ${options.arm}`);
  const student = policy.students.find((entry) => entry.modelId === 'Qwen/Qwen3.5-0.8B');
  if (!student?.trainingSnapshotProvisioned) throw new Error('0.8B student is not provisioned');
  const adapterConfig = JSON.parse(adapterConfigBytes.toString('utf8'));
  const tensors = await readGammaAdapterTensors(options.adapterDir);
  const summary = validateTensorPairs(
    tensors,
    Number(adapterConfig.r),
    [...adapterConfig.target_modules],
  );
  const exportId = `doppler-wgsl-writer-qwen35-0-8b-${options.arm}`;
  const weightsFilename = `${exportId}.adapters.safetensors`;
  const exported = await exportLoRAAdapter({
    id: exportId,
    name: `Doppler WGSL Writer Qwen 3.5 0.8B ${options.arm}`,
    description: `Runtime export for the ${options.arm} family-distillation comparison arm.`,
    baseModel: student.runtimeModelId,
    rank: Number(adapterConfig.r),
    alpha: Number(adapterConfig.lora_alpha),
    targetModules: [...adapterConfig.target_modules],
    tensors,
    weightsFormat: 'safetensors',
    weightsPath: weightsFilename,
    pretty: true,
    metadata: {
      policyId: policy.policyId,
      policySha256: sha256(policyBytes),
      method: arm.method,
      studentSourceModelId: student.modelId,
      studentSourceRevision: student.revision,
      runtimeModelId: student.runtimeModelId,
      sourceAdapterWeightsSha256: sha256(sourceWeights),
      claimBoundary: policy.claimBoundary,
    },
  });
  if (!exported.weights) throw new Error('Doppler adapter export returned no weights');
  const outputDir = path.resolve(options.outputDir);
  const manifestPath = path.join(outputDir, 'runtime-adapter-manifest.json');
  const weightsPath = path.join(outputDir, weightsFilename);
  await mkdir(outputDir, { recursive: true });
  await Promise.all([
    writeFile(manifestPath, exported.json, 'utf8'),
    writeFile(weightsPath, new Uint8Array(exported.weights)),
  ]);
  await loadLoRAFromManifest(exported.manifest, {
    readFile: async (filePath) => readFile(path.join(outputDir, filePath)),
  });
  const receipt = {
    schema: 'doppler.wgsl-writer-family-distill-adapter-export/v1',
    armId: arm.id,
    method: arm.method,
    policyPath: path.relative(ROOT, POLICY_PATH),
    policySha256: sha256(policyBytes),
    sourceAdapterDir: path.resolve(options.adapterDir),
    sourceAdapterConfigSha256: sha256(adapterConfigBytes),
    sourceAdapterWeightsSha256: sha256(sourceWeights),
    runtimeModelId: student.runtimeModelId,
    runtimeManifestPath: manifestPath,
    runtimeManifestSha256: sha256(await readFile(manifestPath)),
    runtimeWeightsPath: weightsPath,
    runtimeWeightsSha256: sha256(await readFile(weightsPath)),
    tensorSummary: summary,
    claimBoundary: 'Format and identity parity only; browser model-output parity and shader execution remain required.',
  };
  const receiptPath = path.join(outputDir, 'export-receipt.json');
  await writeFile(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return { receiptPath, receipt };
}

async function main() {
  const result = await exportFamilyDistillAdapter(parseArgs(process.argv.slice(2)));
  console.log(JSON.stringify(result, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}
