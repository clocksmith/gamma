// A planner-only CLI port: no file, shell, browser or MCP tools, and no project context discovery.
import { spawn as spawnProcess } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { PLANNER_SYSTEM, PLANNER_TOOLS } from './planner.js';

// In two retained trial sessions a model tried to call a workspace tool (record) directly, was told
// by the CLI that no such tool exists, and finished without saving its conclusions. The contracts
// below are not callable from inside the model's session; only the structured reply is.
export const REPLY_PROTOCOL = 'How to reply: you cannot call the workspace tools yourself, and trying to will fail. '
  + 'Each request asks for exactly one next step. Give it as your structured reply {tool, input}; the workspace runs that tool and asks you again with the result in history. '
  + 'Every tool in the contracts below, including record, is available this way on every request. Never report a tool as unavailable, and never put conclusions only in a finish summary: save them with record first.';

export function createCliPlanner({ executable, model, directory, config, spawn = spawnProcess,
  system = PLANNER_SYSTEM, tools = PLANNER_TOOLS }) {
  mkdirSync(directory, { recursive: true, mode: 0o700 });
  const schema = { type: 'object', additionalProperties: false, required: ['tool', 'input'], properties: {
    tool: { type: 'string', enum: Object.keys(tools) }, input: { type: 'object' }
  } };
  return {
    identity: { provider: 'claude-cli', model: model ?? 'CLI configured default; actual model recorded per turn' },
    next(context, { signal }) {
      signal.throwIfAborted();
      const args = ['--print', '--output-format', 'json', '--json-schema', JSON.stringify(schema),
        '--tools', '', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}', '--safe-mode', '--restricted',
        '--setting-sources', '', '--no-session-persistence', '--max-budget-usd', String(config.cliMaxBudgetUsd),
        '--system-prompt', `${system}\n${REPLY_PROTOCOL}\nTool contracts: ${JSON.stringify(tools)}`,
        ...(model ? ['--model', model] : [])];
      return new Promise((resolve, reject) => {
        const child = spawn(executable, args, { cwd: directory, stdio: ['pipe', 'pipe', 'pipe'], shell: false });
        let output = '', bytes = 0, failure = null, killTimer;
        const stop = error => { if (failure) return; failure = error; child.kill('SIGTERM'); killTimer = setTimeout(() => child.kill('SIGKILL'), config.cliTerminationGraceMs); };
        const abort = () => stop(signal.reason ?? Error('Planner cancelled'));
        signal.addEventListener('abort', abort, { once: true });
        const timeout = setTimeout(() => stop(Error('Planner deadline exceeded')), config.modelTimeoutMs);
        child.on('error', error => { failure ??= Error(`Planner could not start: ${error.code ?? 'process error'}`); });
        child.stdout.on('data', chunk => { bytes += chunk.length; if (bytes > config.maxBodyBytes) stop(Error('Planner output exceeds its byte budget')); else output += chunk; });
        // Drain diagnostics without exposing credentials or unbounded provider error bodies to the UI.
        child.stderr.resume();
        child.stdin.on('error', () => {});
        child.once('close', code => {
          clearTimeout(timeout); clearTimeout(killTimer); signal.removeEventListener('abort', abort);
          if (failure) return reject(failure);
          try {
            const response = JSON.parse(output), proposal = response.structured_output;
            const usage = { ...response.usage, costUsd: response.total_cost_usd ?? null, models: Object.keys(response.modelUsage ?? {}) };
            if (code !== 0 || response.is_error) throw Object.assign(Error(response.subtype === 'error_max_budget_usd'
              ? 'Planner per-request budget reached' : `Planner exited with status ${code}`), { usage });
            if (!proposal || !Object.hasOwn(tools, proposal.tool)
              || !proposal.input || typeof proposal.input !== 'object' || Array.isArray(proposal.input)) throw Object.assign(Error('Planner returned no valid structured tool proposal'), { usage });
            resolve({ ...proposal, usage });
          } catch (error) { reject(error); }
        });
        if (signal.aborted) abort();
        child.stdin.end(JSON.stringify(context));
      });
    }
  };
}
