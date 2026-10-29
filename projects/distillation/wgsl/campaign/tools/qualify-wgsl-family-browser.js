#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { chromium } from 'playwright';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';
import { createStaticFileServer } from '../src/tooling/node-browser-command-runner.js';

const ROOT = path.resolve(import.meta.dirname, '..');
const POLICY_PATH = path.join(ROOT, 'tools/policies/wgsl-writer-family-distillation-policy.json');

function parseArgs(argv) {
  const args = { modelDir: '', dataset: '', peftReference: '', outputPath: '' };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--model-dir') args.modelDir = argv[++index] || '';
    else if (token === '--dataset') args.dataset = argv[++index] || '';
    else if (token === '--peft-reference') args.peftReference = argv[++index] || '';
    else if (token === '--out') args.outputPath = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.modelDir) throw new Error('--model-dir is required');
  if (!args.dataset) throw new Error('--dataset is required');
  if (!args.outputPath) throw new Error('--out is required');
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

async function readFirstJsonl(filePath) {
  const lines = (await fs.readFile(filePath, 'utf8')).split('\n').filter((line) => line.trim());
  if (lines.length === 0) throw new Error(`${filePath} contains no rows`);
  return JSON.parse(lines[0]);
}

async function sha256File(filePath) {
  return createHash('sha256').update(await fs.readFile(filePath)).digest('hex');
}

function browserArgs() {
  return [
    '--enable-unsafe-webgpu',
    '--enable-webgpu-developer-features',
    '--disable-dawn-features=disallow_unsafe_apis',
    '--ignore-gpu-blocklist',
    '--use-angle=vulkan',
    '--enable-features=Vulkan',
    '--disable-vulkan-surface',
    '--disable-breakpad',
    '--disable-gpu-sandbox',
    '--no-sandbox',
  ];
}

export async function qualifyWgslFamilyBrowser(args) {
  const policy = await readJson(POLICY_PATH);
  const student = policy.students.find((entry) => entry.modelId === 'Qwen/Qwen3.5-0.8B');
  const row = await readFirstJsonl(path.resolve(args.dataset));
  const adapterBindings = [];
  const staticMounts = [{ urlPrefix: '/__wgsl_model', rootDir: path.resolve(args.modelDir) }];
  for (const arm of policy.arms) {
    const exportRoot = path.resolve(arm.dopplerExportPath);
    const manifestPath = path.join(exportRoot, 'runtime-adapter-manifest.json');
    const manifest = await readJson(manifestPath);
    const weightsPath = path.join(exportRoot, manifest.weightsPath);
    const urlPrefix = `/__wgsl_adapter/${encodeURIComponent(arm.id)}`;
    staticMounts.push({ urlPrefix, rootDir: exportRoot });
    adapterBindings.push({
      id: arm.id,
      manifestPath,
      manifestSha256: await sha256File(manifestPath),
      weightsPath,
      weightsSha256: await sha256File(weightsPath),
      manifestUrl: null,
      urlPrefix,
    });
  }
  const server = await createStaticFileServer({ rootDir: ROOT, staticMounts });
  const browser = await chromium.launch({ headless: true, args: browserArgs() });
  let pageResult = null;
  let browserClosed = false;
  try {
    const page = await browser.newPage();
    await page.goto(`${server.baseUrl}/tools/wgsl-family-browser-runner.html`, {
      waitUntil: 'load',
      timeout: 120_000,
    });
    await page.waitForFunction(
      () => typeof window.runWgslFamilyBrowserQualification === 'function',
      null,
      { timeout: 30_000 },
    );
    pageResult = await page.evaluate(async (request) => (
      window.runWgslFamilyBrowserQualification(request)
    ), {
      modelUrl: `${server.baseUrl}/__wgsl_model`,
      modelId: student.runtimeModelId,
      adapters: adapterBindings.map((adapter) => ({
        id: adapter.id,
        manifestUrl: `${server.baseUrl}${adapter.urlPrefix}/runtime-adapter-manifest.json`,
      })),
      prompt: row.prompt,
      maxTokens: policy.evaluation.generation.maxNewTokens,
    });
  } finally {
    await browser.close();
    browserClosed = true;
    await server.close();
  }
  let peftReference = null;
  if (args.peftReference) {
    const reference = await readJson(path.resolve(args.peftReference));
    peftReference = Object.fromEntries(reference.candidates.map((candidate) => {
      const task = candidate.tasks.find((entry) => entry.taskId === (row.taskId || row.rowId));
      return [candidate.candidateId, {
        outputSha256: task?.completionSha256 ?? null,
        output: task?.completion ?? null,
      }];
    }));
  }
  const candidates = pageResult.candidates.map((candidate) => {
    const reference = peftReference?.[candidate.candidateId] ?? null;
    const outputSha256 = createHash('sha256')
      .update(candidate.generation.output)
      .digest('hex');
    return {
      ...candidate,
      outputSha256,
      peftReference: reference ? {
        outputSha256: reference.outputSha256,
        exactText: candidate.generation.output === reference.output,
      } : null,
    };
  });
  const core = {
    schema: 'doppler.wgsl-writer-family-browser-qualification/v1',
    policy: { path: path.relative(ROOT, POLICY_PATH), sha256: await sha256File(POLICY_PATH) },
    model: {
      modelId: student.runtimeModelId,
      modelDir: path.resolve(args.modelDir),
      manifestSha256: await sha256File(path.join(path.resolve(args.modelDir), 'manifest.json')),
    },
    probe: {
      taskId: row.taskId || row.rowId,
      promptSha256: createHash('sha256').update(row.prompt).digest('hex'),
      maxTokens: policy.evaluation.generation.maxNewTokens,
    },
    adapters: adapterBindings.map(({ urlPrefix, manifestUrl, ...adapter }) => adapter),
    runtime: pageResult.runtime,
    candidates,
    cleanup: { ...pageResult.cleanup, browserClosed, serverClosed: true },
    decision: candidates.every((candidate) => candidate.activation?.activated !== false)
      ? 'browser_qualification_complete'
      : 'browser_adapter_activation_failed',
    comparisonAuthority: false,
    promotionAuthority: false,
    claimBoundary: 'One disjoint prompt proves Chromium/Doppler adapter activation and generation mechanics; the full shader executor evaluation owns capability comparison.',
  };
  const receipt = { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
  await fs.mkdir(path.dirname(path.resolve(args.outputPath)), { recursive: true });
  await fs.writeFile(path.resolve(args.outputPath), `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return receipt;
}

async function main() {
  const receipt = await qualifyWgslFamilyBrowser(parseArgs(process.argv.slice(2)));
  console.log(JSON.stringify({
    decision: receipt.decision,
    runtime: receipt.runtime,
    candidates: receipt.candidates.map((candidate) => ({
      candidateId: candidate.candidateId,
      outputSha256: candidate.outputSha256,
      peftExactText: candidate.peftReference?.exactText ?? null,
    })),
    cleanup: receipt.cleanup,
    receiptHash: receipt.receiptHash,
  }, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}
