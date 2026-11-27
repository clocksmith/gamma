import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { parseJsonText, sha256 } from "./caller-utils.js";
import { runCliProcess } from "./process-runner.js";

export class CodexCliRunner {
  constructor({
    command = "codex",
    prefixArgs = [],
    model,
    reasoningEffort,
    env = {},
    timeoutMs = 120000
  } = {}) {
    this.command = command;
    this.prefixArgs = prefixArgs;
    this.model = model;
    this.reasoningEffort = reasoningEffort;
    this.env = env;
    this.timeoutMs = timeoutMs;
  }

  invocation(prompt, temporaryDirectory, schemaPath, outputPath, {
    redactPrompt = false
  } = {}) {
    const args = [
      ...this.prefixArgs,
      "exec",
      "--sandbox",
      "read-only",
      "--ephemeral",
      "--skip-git-repo-check",
      "--ignore-user-config",
      "--ignore-rules",
      "--color",
      "never",
      "--cd",
      temporaryDirectory,
      "--output-schema",
      schemaPath,
      "--output-last-message",
      outputPath
    ];
    if (this.model) args.push("--model", this.model);
    if (this.reasoningEffort) {
      args.push("--config", `model_reasoning_effort=${JSON.stringify(this.reasoningEffort)}`);
    }
    args.push("-");
    return {
      command: this.command,
      args,
      input: redactPrompt ? "<structured-stage-prompt>" : prompt
    };
  }

  async describeInvocation() {
    return this.invocation(
      "<structured-stage-prompt>",
      "<isolated-temporary-directory>",
      "<response-schema>",
      "<last-message-output>",
      { redactPrompt: true }
    );
  }

  async run({ requestId, prompt, responseSchema, signal } = {}) {
    if (!requestId || typeof requestId !== "string") {
      throw new TypeError("Codex structured stage requires requestId.");
    }
    if (!prompt || typeof prompt !== "string") {
      throw new TypeError("Codex structured stage requires prompt.");
    }
    if (!responseSchema || typeof responseSchema !== "object") {
      throw new TypeError("Codex structured stage requires responseSchema.");
    }
    const temporaryDirectory = await mkdtemp(join(tmpdir(), "mandate-codex-stage-"));
    const schemaPath = join(temporaryDirectory, "response.schema.json");
    const outputPath = join(temporaryDirectory, "response.json");
    await writeFile(schemaPath, `${JSON.stringify(responseSchema, null, 2)}\n`);
    const invocation = this.invocation(
      prompt,
      temporaryDirectory,
      schemaPath,
      outputPath
    );
    try {
      const result = await runCliProcess({
        ...invocation,
        cwd: temporaryDirectory,
        env: this.env,
        timeoutMs: this.timeoutMs,
        signal
      });
      const text = await readFile(outputPath, "utf8").catch(() => result.stdout);
      const output = parseJsonText(text, `Codex structured stage ${requestId}`);
      if (!output || typeof output !== "object" || Array.isArray(output)) {
        throw new TypeError(`Codex structured stage ${requestId} did not return an object.`);
      }
      return {
        output,
        receipt: {
          provider: "codex-cli",
          model: this.model || null,
          reasoningEffort: this.reasoningEffort || null,
          requestId,
          promptSha256: sha256(prompt),
          responseSha256: sha256(JSON.stringify(output)),
          durationMs: result.durationMs
        }
      };
    } finally {
      await rm(temporaryDirectory, { recursive: true, force: true });
    }
  }
}
