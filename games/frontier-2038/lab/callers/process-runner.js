import { spawn } from "node:child_process";

export class CliProcessError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = "CliProcessError";
    this.details = details;
  }
}

export function runCliProcess({
  command,
  args,
  input = "",
  cwd,
  env = {},
  timeoutMs = 120000,
  maxOutputBytes = 2_000_000
}) {
  return new Promise((resolve, reject) => {
    const startedAt = performance.now();
    const child = spawn(command, args, {
      cwd,
      env: { ...process.env, ...env },
      shell: false,
      stdio: ["pipe", "pipe", "pipe"]
    });
    const stdout = [];
    const stderr = [];
    let stdoutBytes = 0;
    let stderrBytes = 0;
    let finished = false;
    let timedOut = false;

    const finish = (callback) => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      callback();
    };

    const timer = setTimeout(() => {
      timedOut = true;
      child.kill("SIGTERM");
      setTimeout(() => child.kill("SIGKILL"), 1000).unref();
    }, timeoutMs);

    child.on("error", (error) => {
      finish(() => reject(new CliProcessError(
        `Unable to start ${command}: ${error.message}`,
        { command, cause: error.code }
      )));
    });

    const capture = (target, chunk, stream) => {
      const bytes = Buffer.byteLength(chunk);
      if (stream === "stdout") stdoutBytes += bytes;
      else stderrBytes += bytes;
      if (stdoutBytes + stderrBytes > maxOutputBytes) {
        child.kill("SIGTERM");
        finish(() => reject(new CliProcessError(
          `${command} exceeded the ${maxOutputBytes}-byte output limit.`,
          { command, stream }
        )));
        return;
      }
      target.push(chunk);
    };

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => capture(stdout, chunk, "stdout"));
    child.stderr.on("data", (chunk) => capture(stderr, chunk, "stderr"));

    child.on("close", (code, signal) => {
      finish(() => {
        const result = {
          code,
          signal,
          stdout: stdout.join(""),
          stderr: stderr.join(""),
          durationMs: Math.round(performance.now() - startedAt)
        };
        if (timedOut) {
          reject(new CliProcessError(
            `${command} exceeded the ${timeoutMs}ms timeout.`,
            { command, timeoutMs }
          ));
        } else if (code !== 0) {
          reject(new CliProcessError(
            `${command} exited with code ${code}.`,
            { ...result, command }
          ));
        } else {
          resolve(result);
        }
      });
    });

    child.stdin.on("error", (error) => {
      if (error.code !== "EPIPE") {
        finish(() => reject(new CliProcessError(
          `Unable to write input to ${command}: ${error.message}`,
          { command, cause: error.code }
        )));
      }
    });
    child.stdin.end(input);
  });
}
