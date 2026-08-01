import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  buildProviderDecisionPrompt,
  providerDecisionProtocolVersion,
  validateProviderDecisionResponse
} from "../contracts/decision-contract.js";
import {
  attachProviderFailure,
  extractDecisionCandidate,
  parseJsonText,
  responseSchemaUrl,
  sha256
} from "./caller-utils.js";
import { runCliProcess } from "./process-runner.js";

export class CodexCliCaller {
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
    this.decisionProtocolVersion = providerDecisionProtocolVersion;
  }

  invocation(packet, temporaryDirectory, outputPath, { redactPrompt = false } = {}) {
    const providerPrompt = buildProviderDecisionPrompt(packet);
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
      fileURLToPath(responseSchemaUrl),
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
      input: redactPrompt ? "<decision-prompt>" : providerPrompt.prompt,
      aliases: providerPrompt.aliases
    };
  }

  async describeInvocation(packet) {
    return this.invocation(
      packet,
      "<isolated-temporary-directory>",
      "<last-message-output>",
      { redactPrompt: true }
    );
  }

  async decide(packet, { signal } = {}) {
    const temporaryDirectory = await mkdtemp(join(tmpdir(), "frontier-codex-"));
    const outputPath = join(temporaryDirectory, "decision.json");
    const invocation = this.invocation(packet, temporaryDirectory, outputPath);
    try {
      const result = await runCliProcess({
        ...invocation,
        cwd: temporaryDirectory,
        env: this.env,
        timeoutMs: this.timeoutMs,
        signal
      });
      const text = await readFile(outputPath, "utf8").catch(() => result.stdout);
      const decision = validateProviderDecisionResponse(
        packet,
        extractDecisionCandidate(parseJsonText(text, "Codex CLI"), "Codex CLI"),
        invocation.aliases
      );
      return {
        decision,
        receipt: {
          provider: "codex-cli",
          model: this.model || null,
          reasoningEffort: this.reasoningEffort || null,
          requestId: packet.requestId,
          promptSha256: sha256(invocation.input),
          decisionId: decision.decisionId,
          durationMs: result.durationMs
        }
      };
    } catch (error) {
      throw attachProviderFailure(error, {
        provider: "codex-cli",
        model: this.model,
        reasoningEffort: this.reasoningEffort,
        requestId: packet.requestId,
        prompt: invocation.input
      });
    } finally {
      await rm(temporaryDirectory, { recursive: true, force: true });
    }
  }
}
