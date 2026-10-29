import { readFile } from 'node:fs/promises';

import { renderProviderArgs } from './host-teacher-contracts.js';
import { parseJsonlEvents, runHostProcess } from './host-teacher-process.js';

function parseJsonText(value) {
  if (value != null && typeof value === 'object' && !Array.isArray(value)) return value;
  if (typeof value !== 'string' || !value.trim()) return null;
  const text = value.trim();
  try {
    return JSON.parse(text);
  } catch {
    const fenced = text.match(/```(?:json)?\s*([\s\S]*?)\s*```/i)?.[1];
    const candidate = fenced || text.slice(text.indexOf('{'), text.lastIndexOf('}') + 1);
    if (!candidate) return null;
    try {
      return JSON.parse(candidate);
    } catch {
      return null;
    }
  }
}

function readClaudeFinalOutput(events) {
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const event = events[index];
    if (event?.type !== 'result') continue;
    return parseJsonText(event.structured_output)
      || parseJsonText(event.structuredOutput)
      || parseJsonText(event.result);
  }
  return null;
}

function collectCommandFields(value, commands, parentKey = '') {
  if (Array.isArray(value)) {
    for (const entry of value) collectCommandFields(entry, commands, parentKey);
    return;
  }
  if (value == null || typeof value !== 'object') return;
  for (const [key, entry] of Object.entries(value)) {
    const normalizedKey = key.toLowerCase();
    if (
      typeof entry === 'string'
      && (normalizedKey === 'command' || normalizedKey === 'cmd' || normalizedKey === 'command_line')
    ) {
      commands.push(entry);
      continue;
    }
    collectCommandFields(entry, commands, normalizedKey || parentKey);
  }
}

export function extractProviderCommands(events) {
  const commands = [];
  for (const event of events) collectCommandFields(event, commands);
  return [...new Set(commands)];
}

export function buildHostTeacherPrompt(task) {
  const validations = task.validationCommands
    .map((command) => `- ${command.command} ${command.args.join(' ')}`)
    .join('\n');
  return [
    'You are repairing one defect in a disposable Doppler repository snapshot.',
    'Read and follow the repository AGENTS.md and the nearest relevant style guide before editing.',
    'Do not use the network, install dependencies, inspect git history, reset files, or create new files.',
    `Task ID: ${task.id}`,
    `Lane: ${task.lane}`,
    `Task: ${task.prompt}`,
    `You may modify only: ${task.allowedChangedPaths.join(', ')}`,
    `Relevant files: ${task.sourceFiles.join(', ')}`,
    'Run the relevant checks below after the repair:',
    validations,
    'Your final response must be only the JSON object required by the supplied schema.',
    'Use exactly these keys: taskId, summary, changedFiles, verification, residualRisks.',
    'changedFiles and verification are arrays of strings; residualRisks is an array of strings and may be empty.',
    `Set taskId to ${JSON.stringify(task.id)} and report the files you actually changed.`,
    'Do not put a patch or markdown fence in the final response; the harness captures the git diff.',
  ].join('\n\n');
}

export async function runHostTeacherProvider(options) {
  const {
    providerId,
    provider,
    modelId,
    workspace,
    outputPath,
    schemaPath,
    schemaJson,
    task,
  } = options;
  const prompt = buildHostTeacherPrompt(task);
  const args = renderProviderArgs(provider, {
    modelId,
    outputPath,
    prompt,
    schemaJson,
    schemaPath,
    workspace,
  });
  const result = await runHostProcess(provider.command, args, {
    cwd: workspace,
    stdin: provider.promptTransport === 'stdin' ? prompt : undefined,
    env: {
      ...process.env,
      CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: '1',
      NO_COLOR: '1',
    },
  });
  const parsed = parseJsonlEvents(result.stdout);
  let finalOutput = null;
  if (provider.finalOutputMode === 'file') {
    try {
      finalOutput = parseJsonText(await readFile(outputPath, 'utf8'));
    } catch (error) {
      if (error?.code !== 'ENOENT') throw error;
    }
  } else if (providerId === 'claude') {
    finalOutput = readClaudeFinalOutput(parsed.events);
  }
  return {
    prompt,
    args,
    process: result,
    events: parsed.events,
    eventParseErrors: parsed.errors,
    commands: extractProviderCommands(parsed.events),
    finalOutput,
  };
}
