import { buildDecisionPrompt, validateDecisionResponse } from "../contracts/decision-contract.js";
import {
  attachProviderFailure,
  extractDecisionCandidate,
  loadResponseSchema,
  parseJsonText,
  sha256
} from "./caller-utils.js";
import { runCliProcess } from "./process-runner.js";

export class ClaudeCliCaller {
  constructor({
    command = "claude",
    prefixArgs = [],
    model,
    reasoningEffort,
    cwd = process.cwd(),
    env = {},
    timeoutMs = 120000,
    maxBudgetUsd
  } = {}) {
    this.command = command;
    this.prefixArgs = prefixArgs;
    this.model = model;
    this.reasoningEffort = reasoningEffort;
    this.cwd = cwd;
    this.env = env;
    this.timeoutMs = timeoutMs;
    this.maxBudgetUsd = maxBudgetUsd;
  }

  async invocation(packet, { redactPrompt = false } = {}) {
    const responseSchema = await loadResponseSchema();
    const prompt = buildDecisionPrompt(packet);
    const args = [
      ...this.prefixArgs,
      "-p",
      "--tools",
      "",
      "--safe-mode",
      "--no-session-persistence",
      "--output-format",
      "json",
      "--json-schema",
      JSON.stringify(responseSchema)
    ];
    if (this.model) args.push("--model", this.model);
    if (this.reasoningEffort) args.push("--effort", this.reasoningEffort);
    if (this.maxBudgetUsd !== undefined) {
      args.push("--max-budget-usd", String(this.maxBudgetUsd));
    }
    return {
      command: this.command,
      args,
      input: redactPrompt ? "<decision-prompt>" : prompt
    };
  }

  async decide(packet, { signal } = {}) {
    const invocation = await this.invocation(packet);
    try {
      const result = await runCliProcess({
        ...invocation,
        cwd: this.cwd,
        env: this.env,
        timeoutMs: this.timeoutMs,
        signal
      });
      const envelope = parseJsonText(result.stdout, "Claude CLI");
      const decision = validateDecisionResponse(
        packet,
        extractDecisionCandidate(envelope, "Claude CLI")
      );
      return {
        decision,
        receipt: {
          provider: "claude-cli",
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
        provider: "claude-cli",
        model: this.model,
        reasoningEffort: this.reasoningEffort,
        requestId: packet.requestId,
        prompt: invocation.input
      });
    }
  }
}
