#!/usr/bin/env node
// Blitzen durable browser workspace above stock Chrome by default; Fawn builds remain explicit and hash-pinned.
import { readFile } from 'node:fs/promises';
import { mkdirSync, chmodSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { homedir } from 'node:os';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { loadClientServiceConfig } from './browser-selection.js';
import { WorkspaceService } from '../service.js';
import { createPlaywrightAdapter } from '../adapters/playwright-adapter.js';
import { createCdpAdapter } from '../adapters/cdp-adapter.js';
import { createCliPlanner } from './cli-planner.js';
import { createPlanner } from './planner.js';
import { WorkspaceController } from './controller.js';
import { WorkflowSync } from './workflow-sync.js';
import { WorkflowStore } from './workflow-store.js';
import { createNativePicker } from './native-picker.js';
import { startWorkspaceServer } from './server.js';

export async function openWorkspaceApp({ stateDir, port, headless = false, adapter = 'playwright', config: supplied, planner: suppliedPlanner,
  workflowPersistence = null, workflowTasks = new Map(), browserConfig, browserChannel, nativePicker = null, commitAuthority = null } = {}) {
  const config = supplied ?? JSON.parse(await readFile(new URL('../../config/fawn-workspace-client.json', import.meta.url), 'utf8'));
  for (const field of ['port', 'maxBodyBytes', 'maxEvidenceBytes', 'maxRepositoryFiles', 'maxTurns', 'maxInputBytes', 'maxOutputTokens', 'modelTimeoutMs', 'pollMs', 'delegationMaxAgeMs', 'shutdownWaitMs', 'cliTerminationGraceMs']) {
    if (!Number.isSafeInteger(config[field]) || config[field] < (field === 'port' ? 0 : 1)) throw Error(`Invalid client config ${field}`);
  }
  if (!Number.isFinite(config.cliMaxBudgetUsd) || config.cliMaxBudgetUsd <= 0) throw Error('Invalid CLI planner budget');
  const plannerEnv = process.env.BLITZEN_PLANNER ?? process.env.FAWN_PLANNER;
  const modelEnv = process.env.BLITZEN_MODEL ?? process.env.FAWN_MODEL;
  if (plannerEnv && !['claude-cli', 'anthropic'].includes(plannerEnv)) throw Error('Unknown planner selection');
  if (config.host !== '127.0.0.1') throw Error('Workspace control service only listens on loopback');
  const directory = resolve(stateDir ?? process.env.BLITZEN_STATE_DIR ?? process.env.FAWN_WORKSPACE_STATE_DIR ?? join(homedir(), '.local/state/blitzen'));
  const serviceConfig = loadClientServiceConfig({ directory, headless,
    browserConfig: browserConfig ?? process.env.BLITZEN_BROWSER_CONFIG ?? process.env.FAWN_BROWSER_CONFIG,
    browserChannel: browserChannel ?? process.env.BLITZEN_BROWSER_CHANNEL ?? process.env.FAWN_BROWSER_CHANNEL });
  mkdirSync(directory, { recursive: true, mode: 0o700 }); chmodSync(directory, 0o700);
  const planner = suppliedPlanner ?? (plannerEnv === 'claude-cli' ? createCliPlanner({
    executable: process.env.BLITZEN_CLAUDE_BIN ?? process.env.FAWN_CLAUDE_BIN ?? 'claude', model: modelEnv, directory: join(directory, 'planner'), config
  }) : createPlanner({ model: modelEnv, endpoint: config.modelEndpoint,
    apiKey: process.env[config.apiKeyEnvironment], maxOutputTokens: config.maxOutputTokens, timeoutMs: config.modelTimeoutMs }));
  const factory = { playwright: createPlaywrightAdapter, cdp: createCdpAdapter }[adapter];
  if (!factory) throw Error('Choose playwright or cdp');
  const service = await WorkspaceService.open({ stateDir: join(directory, 'service'),
    config: serviceConfig, createAdapter: factory, commitAuthority });
  let controller, http;
  try {
    const workflowStore = workflowPersistence ? new WorkflowStore({ ...workflowPersistence,
      directory: join(directory, 'workflows'),
      sync: workflowPersistence.sync ? new WorkflowSync({ ...workflowPersistence.sync, ownerScope: workflowPersistence.ownerScope }) : null }) : null;
    controller = new WorkspaceController({ service, stateDir: directory, config, planner, workflowStore, workflowTasks });
    await controller.restore();
    http = await startWorkspaceServer({ controller, config, port, nativePicker });
    return { ...http, controller, service, browser: serviceConfig.browser,
      async close() { await http.close(); await controller.close({ release: () => service.close() }); } };
  } catch (error) { controller?.store.close(); await service.close(); throw error; }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2), value = name => { const index = args.indexOf(name); return index < 0 ? undefined : args[index + 1]; };
  if (args.includes('--help')) {
    console.log('Usage: npm --prefix projects/workspace start -- [--browser-channel chrome|chromium|chromium-headless-shell|fawn] [--browser-config PATH] [--workflow-module PATH] [--state-dir PATH] [--port NUMBER] [--adapter playwright|cdp] [--headless] [--native-picker-bin PATH --native-picker-sha256 HASH]');
    console.log('Default: installed Google Chrome (--browser-channel chrome) under ~/.local/state/blitzen (existing state retained). Pass --browser-channel fawn or --browser-config PATH (or BLITZEN_BROWSER_CONFIG) to require a hash-pinned Fawn browser build without fallback.');
  } else {
    const workflowModulePath = value('--workflow-module') ?? process.env.BLITZEN_WORKFLOW_MODULE ?? process.env.FAWN_WORKFLOW_MODULE;
    const loadedWorkflow = workflowModulePath ? await import(pathToFileURL(resolve(workflowModulePath)).href) : null;
    const workflowConfig = typeof loadedWorkflow?.createWorkflowConfig === 'function'
      ? await loadedWorkflow.createWorkflowConfig() : (loadedWorkflow ?? {});
    const binary = value('--native-picker-bin'), sha256 = value('--native-picker-sha256');
    const nativePicker = binary === undefined && sha256 === undefined ? null : (() => {
      if (process.platform !== 'darwin') throw Error('Native picker requires a local macOS desktop');
      return createNativePicker({ executable: binary, sha256 });
    })();
    const app = await openWorkspaceApp({ stateDir: value('--state-dir'), port: value('--port') === undefined ? undefined : Number(value('--port')),
      adapter: value('--adapter'), headless: args.includes('--headless'),
      workflowPersistence: workflowConfig.workflowPersistence ?? null,
      workflowTasks: workflowConfig.workflowTasks ?? new Map(),
      // The trusted workflow module may supply the host's approval store and record reader.
      commitAuthority: workflowConfig.commitAuthority ?? null,
      browserConfig: value('--browser-config'), browserChannel: value('--browser-channel'), nativePicker });
    console.log(`Gamma workspace (${app.browser.channel}, ${app.browser.fawnBuild?.runtime.mode ?? 'stock provider'}): ${app.loginUrl}`);
    console.log('Start with human control. Model calls occur only after an explicit delegation.');
    let closing = false;
    const close = async () => { if (closing) return; closing = true; try { await app.close(); process.exitCode = 0; } catch (error) { console.error(error.message); process.exitCode = 1; } };
    process.on('SIGINT', close); process.on('SIGTERM', close);
  }
}
