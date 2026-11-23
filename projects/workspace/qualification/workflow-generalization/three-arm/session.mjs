// Launches one model session for an arm and reads back what it cost
// (clocksmith/deco#88, same-model three-arm test).
//
// The session gets no shell and no web tool, file tools confined to an empty
// working directory, and one MCP server. User, project and local settings are
// not loaded. Nothing here decides anything: it starts the CLI, keeps its full
// event log and returns the CLI's own usage report.
import { spawn } from 'node:child_process';
import { createWriteStream } from 'node:fs';

export const FILE_TOOLS = Object.freeze(['Read', 'Write', 'Edit', 'Glob', 'Grep']);

/** `server` is { command, args, env } for the arm's MCP server; `mcpTools` are its tool names. */
export function sessionArgs({ model, budgetUsd, systemPrompt, server, mcpTools, fileTools = FILE_TOOLS, jsonSchema = null }) {
  const allowed = [...fileTools, ...mcpTools.map(name => `mcp__app__${name}`)];
  return {
    allowedTools: allowed,
    args: ['--print', '--output-format', 'stream-json', '--verbose', '--model', model,
      '--max-budget-usd', String(budgetUsd), '--restricted', '--tools', fileTools.join(','),
      '--strict-mcp-config', '--mcp-config', JSON.stringify({ mcpServers: { app: server } }),
      '--setting-sources', '', '--no-session-persistence',
      '--permission-mode', 'acceptEdits', '--permission-prompts', 'none', '--allowedTools', allowed.join(','),
      '--system-prompt', systemPrompt,
      ...(jsonSchema ? ['--json-schema', JSON.stringify(jsonSchema)] : [])],
  };
}

export function runSession({ executable, args, cwd, prompt, logFile, timeoutMs, spawnProcess = spawn }) {
  const startedAt = new Date();
  return new Promise(done => {
    const child = spawnProcess(executable, args, { cwd, stdio: ['pipe', 'pipe', 'pipe'], shell: false });
    const log = createWriteStream(logFile, { mode: 0o600 });
    const lines = [];
    let buffer = '';
    let timedOut = false;
    let startError = null;
    const timer = setTimeout(() => { timedOut = true; child.kill('SIGTERM'); setTimeout(() => child.kill('SIGKILL'), 3000); }, timeoutMs);
    child.on('error', error => { startError = String(error.code ?? error.message); });
    child.stdin.on('error', () => {});
    child.stderr.resume();
    child.stdout.on('data', chunk => {
      log.write(chunk);
      buffer += chunk;
      for (let cut; (cut = buffer.indexOf('\n')) !== -1; buffer = buffer.slice(cut + 1)) lines.push(buffer.slice(0, cut));
    });
    child.once('close', exitCode => {
      clearTimeout(timer);
      if (buffer) lines.push(buffer);
      log.end();
      const endedAt = new Date();
      const events = lines.flatMap(line => { try { return [JSON.parse(line)]; } catch { return []; } });
      const final = events.findLast(e => e?.type === 'result') ?? null;
      const assistantIds = new Set(events.filter(e => e?.type === 'assistant').map((e, i) => e.message?.id ?? `event-${i}`));
      done({
        exitCode, timedOut, startError, lines,
        startedAt: startedAt.toISOString(), endedAt: endedAt.toISOString(), wallMs: endedAt - startedAt,
        costUsd: Number.isFinite(final?.total_cost_usd) ? final.total_cost_usd : null,
        modelTurns: Number.isInteger(final?.num_turns) ? final.num_turns : 0,
        modelCalls: assistantIds.size,
        models: Object.keys(final?.modelUsage ?? {}),
        isError: final ? Boolean(final.is_error) : true,
        subtype: final?.subtype ?? (timedOut ? 'timed_out' : 'no_result'),
        structured: final?.structured_output ?? null,
        text: typeof final?.result === 'string' ? final.result : null,
      });
    });
    child.stdin.end(prompt);
  });
}
