import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";

export const responseSchemaUrl = new URL(
  "../contracts/decision-response.schema.json",
  import.meta.url
);

export async function loadResponseSchema() {
  return JSON.parse(await readFile(responseSchemaUrl, "utf8"));
}

export function sha256(value) {
  return createHash("sha256").update(String(value)).digest("hex");
}

export function attachProviderFailure(error, {
  provider,
  model,
  reasoningEffort,
  requestId,
  prompt
}) {
  const details = error?.details || {};
  error.providerReceipt = {
    attemptedProvider: provider,
    attemptedModel: model || null,
    attemptedReasoningEffort: reasoningEffort || null,
    attemptedRequestId: requestId,
    attemptedPromptSha256: sha256(prompt),
    providerErrorClass: error?.name || "Error",
    providerErrorMessage: error?.message || "Unknown provider failure.",
    providerErrorExitCode: Number.isInteger(details.code) ? details.code : null,
    providerErrorStderrSha256:
      typeof details.stderr === "string" && details.stderr.length > 0
        ? sha256(details.stderr)
        : null,
    providerDurationMs: details.durationMs ?? null
  };
  return error;
}

export function parseJsonText(text, label) {
  const trimmed = String(text).trim();
  if (!trimmed) throw new TypeError(`${label} returned no output.`);
  try {
    return JSON.parse(trimmed);
  } catch {
    const fenced = trimmed.match(/```(?:json)?\s*([\s\S]*?)\s*```/i);
    if (fenced) return JSON.parse(fenced[1]);
    const start = trimmed.indexOf("{");
    const end = trimmed.lastIndexOf("}");
    if (start >= 0 && end > start) return JSON.parse(trimmed.slice(start, end + 1));
    throw new TypeError(`${label} did not return JSON.`);
  }
}

export function extractDecisionCandidate(value, label) {
  if (value && typeof value === "object" && typeof value.decisionId === "string") {
    return value;
  }
  for (const key of ["structured_output", "structuredOutput", "output"]) {
    if (value?.[key] && typeof value[key] === "object") {
      return extractDecisionCandidate(value[key], label);
    }
  }
  if (typeof value?.result === "string") {
    return extractDecisionCandidate(parseJsonText(value.result, label), label);
  }
  if (value?.result && typeof value.result === "object") {
    return extractDecisionCandidate(value.result, label);
  }
  throw new TypeError(`${label} output did not contain a decision object.`);
}
