import { spawn } from 'node:child_process';

export function runHostProcess(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const stdout = [];
    const stderr = [];
    const child = spawn(command, args, {
      cwd: options.cwd,
      env: options.env || process.env,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    child.stdout.on('data', (chunk) => stdout.push(chunk));
    child.stderr.on('data', (chunk) => stderr.push(chunk));
    child.on('error', reject);
    child.on('close', (code, signal) => {
      resolve({
        command,
        args,
        code,
        signal,
        stdout: Buffer.concat(stdout).toString('utf8'),
        stderr: Buffer.concat(stderr).toString('utf8'),
      });
    });
    if (options.stdin !== undefined) {
      child.stdin.end(String(options.stdin));
    } else {
      child.stdin.end();
    }
  });
}

export async function requireHostCommandVersion(command, versionArgs) {
  const result = await runHostProcess(command, versionArgs);
  if (result.code !== 0 || result.signal) {
    throw new Error(
      `Host teacher command version probe failed: ${command} ${versionArgs.join(' ')}\n${result.stderr}`
    );
  }
  const version = `${result.stdout}\n${result.stderr}`.trim();
  if (!version) {
    throw new Error(`Host teacher command version probe returned no version: ${command}.`);
  }
  return version;
}

export function parseJsonlEvents(text) {
  const events = [];
  const errors = [];
  const lines = String(text).split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index].trim();
    if (!line) continue;
    try {
      events.push(JSON.parse(line));
    } catch (error) {
      errors.push({
        line: index + 1,
        message: error.message,
        text: line,
      });
    }
  }
  return { events, errors };
}
