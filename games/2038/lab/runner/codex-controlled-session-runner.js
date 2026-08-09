import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import { relative, resolve } from "node:path";
import { promisify } from "node:util";
import { CodexCliRunner } from "../callers/codex-cli-runner.js";
import { createSimulation } from "../runtime/create-simulation.js";
import { projectRoot } from "../versioning/game-identity.js";

const execFileAsync = promisify(execFile);

const objectSchema = (properties, required = Object.keys(properties)) => ({
  type: "object",
  additionalProperties: false,
  required,
  properties
});
const stringArray = (minimum = 0, maximum = 20) => ({
  type: "array",
  minItems: minimum,
  maxItems: maximum,
  items: { type: "string", minLength: 1 }
});
const questionArray = (minimum = 0, maximum = 8) => ({
  type: "array",
  minItems: minimum,
  maxItems: maximum,
  items: objectSchema({
    text: { type: "string", minLength: 1 },
    reason: { type: "string", minLength: 1 }
  })
});

export const unboxingResponseSchema = objectSchema({
  summary: { type: "string", minLength: 1 },
  observedComponents: stringArray(4),
  sortingPlan: stringArray(2),
  immediateConfusions: questionArray(1, 6)
});

export const rulesResponseSchema = objectSchema({
  summary: { type: "string", minLength: 1 },
  rulesReconstruction: stringArray(6),
  anticipatedFriction: stringArray(1),
  questions: questionArray(2, 8)
});

export const followupResponseSchema = objectSchema({
  summary: { type: "string", minLength: 1 },
  resolvedUnderstanding: stringArray(2),
  remainingQuestions: questionArray(0, 4),
  readyToPlay: { type: "boolean" }
});

export const postgameResponseSchema = objectSchema({
  definingMoments: stringArray(1, 8),
  rulesReconstruction: stringArray(5, 16),
  winnerExplanation: { type: "string", minLength: 1 },
  worldEndingExplanation: { type: "string", minLength: 1 },
  confusingMoments: stringArray(0, 8),
  teachingChanges: stringArray(0, 8)
});

function headings(markdown) {
  return String(markdown)
    .split(/\r?\n/)
    .filter((line) => /^#{1,6}\s+\S/.test(line))
    .map((line) => line.replace(/^#{1,6}\s+/, "").trim());
}

function facilitatorResponseSchema(questions, documents) {
  return objectSchema({
    answers: {
      type: "array",
      minItems: questions.length,
      maxItems: questions.length,
      items: objectSchema({
        questionId: { enum: questions.map((question) => question.id) },
        answer: { type: "string", minLength: 1 },
        citations: {
          type: "array",
          minItems: 1,
          maxItems: 4,
          items: objectSchema({
            sourceId: { enum: documents.map((document) => document.id) },
            heading: {
              enum: [...new Set(documents.flatMap((document) => document.headings))]
            }
          })
        }
      })
    },
    unresolved: stringArray(0, questions.length)
  });
}

function fencedSources(documents) {
  return documents.map((document) => [
    `\n===== SOURCE ${document.id}: ${document.fileName} =====`,
    document.contents,
    `===== END SOURCE ${document.id} =====\n`
  ].join("\n")).join("\n");
}

function validateQuestions(questions, label) {
  if (!Array.isArray(questions)) throw new TypeError(`${label} questions must be an array.`);
  for (const question of questions) {
    if (!question || typeof question.text !== "string" || !question.text.trim()) {
      throw new TypeError(`${label} returned an invalid question.`);
    }
  }
}

function validateFacilitator(result, questions, documents) {
  const answers = result?.output?.answers;
  if (!Array.isArray(answers) || answers.length !== questions.length) {
    throw new Error("Facilitator must answer every recorded question exactly once.");
  }
  const expected = new Set(questions.map((question) => question.id));
  const observed = new Set();
  const byId = new Map(documents.map((document) => [document.id, document]));
  for (const answer of answers) {
    if (!expected.has(answer.questionId) || observed.has(answer.questionId)) {
      throw new Error(`Facilitator returned duplicate or unknown question ${answer.questionId}.`);
    }
    observed.add(answer.questionId);
    for (const citation of answer.citations || []) {
      const document = byId.get(citation.sourceId);
      if (!document?.headings.includes(citation.heading)) {
        throw new Error(
          `Facilitator citation ${citation.sourceId}#${citation.heading} is not in the frozen kit.`
        );
      }
    }
  }
  return result;
}

async function mapWithConcurrency(values, concurrency, operation) {
  const results = new Array(values.length);
  let cursor = 0;
  const workers = Array.from(
    { length: Math.min(concurrency, values.length) },
    async () => {
      while (cursor < values.length) {
        const index = cursor;
        cursor += 1;
        results[index] = await operation(values[index], index);
      }
    }
  );
  await Promise.all(workers);
  return results;
}

export function validateCodexSessionRegistration(document) {
  if (
    document?.schemaVersion !== 1 ||
    document?.artifactKind !== "codex-controlled-session-preregistration" ||
    document?.locked !== true ||
    document?.runs !== 1 ||
    document?.playerCount !== 4 ||
    !Array.isArray(document.participants) ||
    document.participants.length !== 4 ||
    !document.provider?.model ||
    !document.provider?.reasoningEffort ||
    !Number.isInteger(document.provider?.timeoutMs) ||
    document.provider.timeoutMs < 1000 ||
    !Number.isInteger(document.provider?.maxConcurrent) ||
    document.provider.maxConcurrent < 1 ||
    document.provider.maxConcurrent > 4 ||
    document.provider?.maximumLlmDecisions !== null
  ) {
    throw new TypeError("Invalid locked Codex controlled-session preregistration.");
  }
  const seats = new Set();
  const factions = new Set();
  for (const participant of document.participants) {
    if (
      !Number.isInteger(participant.seat) ||
      participant.seat < 0 ||
      participant.seat > 3 ||
      !participant.factionId ||
      !participant.factionName ||
      !participant.profileId ||
      participant.backend !== "codex"
    ) {
      throw new TypeError("Every controlled-session participant requires one Codex seat, faction, and profile.");
    }
    seats.add(participant.seat);
    factions.add(participant.factionId);
  }
  if (seats.size !== 4 || factions.size !== 4) {
    throw new TypeError("Controlled-session seats and factions must be unique.");
  }
  return document;
}

async function registrationIdentity(path) {
  const absolute = resolve(path);
  const relativePath = relative(projectRoot, absolute);
  if (
    relativePath.startsWith("..") ||
    !relativePath.startsWith("evidence/studies/simulation/preregistrations/")
  ) {
    throw new Error("Codex session preregistration must live in the simulation preregistration directory.");
  }
  await execFileAsync("git", ["ls-files", "--error-unmatch", relativePath], {
    cwd: projectRoot
  }).catch(() => {
    throw new Error("Codex session preregistration must be committed before execution.");
  });
  const { stdout } = await execFileAsync("git", ["log", "-1", "--format=%H", "--", relativePath], {
    cwd: projectRoot
  });
  return { path: relativePath, registrationCommit: stdout.trim() };
}

async function loadKit(kitManifestPath) {
  const manifestPath = resolve(kitManifestPath);
  const root = resolve(manifestPath, "..");
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  if (manifest.artifactKind !== "controlled-physical-playtest-kit") {
    throw new TypeError("Codex session requires a controlled physical-playtest kit manifest.");
  }
  const files = [
    ["core-rules", "core-rules.md"],
    ["map-reference", "map-reference.md"],
    ["component-reference", "component-reference.md"],
    ["card-reference", "card-reference.md"]
  ];
  const documents = await Promise.all(files.map(async ([id, fileName]) => {
    const contents = await readFile(resolve(root, fileName), "utf8");
    return { id, fileName, contents, headings: headings(contents) };
  }));
  return { root, manifestPath, manifest, documents };
}

function participantContext(participant) {
  return `Seat ${participant.seat + 1}; faction ${participant.factionName} (${participant.factionId}); decision profile ${participant.profileId}.`;
}

function questionsFrom(results, field, prefix) {
  return results.flatMap((result, seat) => {
    const questions = result.output[field] || [];
    validateQuestions(questions, `${prefix} seat ${seat + 1}`);
    return questions.map((question, index) => ({
      id: `${prefix}-s${seat + 1}-q${index + 1}`,
      seat,
      ...question
    }));
  });
}

function facilitatorPrompt(questions, documents, label) {
  return [
    `You are the rules facilitator for a recorded Mandate 2038 ${label}.`,
    "Answer only from the frozen sources below. Do not change a rule, invent intent, or smooth over an ambiguity.",
    "Every answer must cite an exact source id and exact Markdown heading supplied in the sources.",
    "If the frozen sources genuinely do not resolve something, say that in the answer and add its question id to unresolved.",
    "Questions:",
    JSON.stringify(questions, null, 2),
    fencedSources(documents)
  ].join("\n\n");
}

function summarizeGame(report) {
  const sample = report.samples?.[0] || {};
  return {
    standings: sample.standings || report.observations?.[0]?.standings || [],
    winnerSeats: sample.winnerSeats || report.observations?.[0]?.winnerSeats || [],
    worldEnding: sample.worldEnding || report.observations?.[0]?.worldEnding || null,
    powerTrades: sample.matchMetrics?.powerTrades || report.observations?.[0]?.powerTrades || [],
    negotiations: sample.matchMetrics?.negotiations || report.observations?.[0]?.negotiations || [],
    futureTimeline: sample.matchMetrics?.futureTimeline || report.observations?.[0]?.futureTimeline || []
  };
}

export async function runCodexControlledSession({
  preRegistrationPath,
  kitManifestPath,
  allowLlm = false,
  signal,
  onProgress,
  onStageComplete,
  runnerFactory,
  simulationFactory = createSimulation
} = {}) {
  if (!allowLlm) throw new Error("Codex controlled session requires explicit allowLlm authorization.");
  if (!preRegistrationPath || !kitManifestPath) {
    throw new TypeError("Codex controlled session requires preregistration and kit manifest paths.");
  }
  const registration = validateCodexSessionRegistration(
    JSON.parse(await readFile(resolve(preRegistrationPath), "utf8"))
  );
  const [registrationProvenance, kit] = await Promise.all([
    registrationIdentity(preRegistrationPath),
    loadKit(kitManifestPath)
  ]);
  const current = JSON.parse(await readFile(resolve(projectRoot, "versions/current.json"), "utf8"));
  if (
    current.gameVersion !== registration.release.gameVersion ||
    current.rulesCandidate.version !== registration.release.rulesVersion ||
    current.rulesetFingerprint !== registration.release.rulesetFingerprint ||
    kit.manifest.identity.rulesetFingerprint !== registration.release.rulesetFingerprint ||
    kit.manifest.identity.executableVersion !== registration.release.gameVersion ||
    kit.manifest.identity.rulesVersion !== registration.release.rulesVersion
  ) {
    throw new Error("Codex session release, preregistration, and physical kit identities do not match.");
  }
  const runner = runnerFactory?.(registration.provider) || new CodexCliRunner({
    model: registration.provider.model,
    reasoningEffort: registration.provider.reasoningEffort,
    timeoutMs: registration.provider.timeoutMs
  });
  const participants = [...registration.participants].sort((left, right) => left.seat - right.seat);
  const startedAt = new Date().toISOString();
  const stage = async (id, operation) => {
    onProgress?.({ phase: "session_stage", id, status: "started" });
    const result = await operation();
    await onStageComplete?.({ id, completedAt: new Date().toISOString(), result });
    onProgress?.({ phase: "session_stage", id, status: "completed" });
    return result;
  };

  const unboxing = await stage("unboxing", () => mapWithConcurrency(
    participants,
    registration.provider.maxConcurrent,
    (participant) => runner.run({
      requestId: `${registration.id}:unboxing:seat-${participant.seat + 1}`,
      responseSchema: unboxingResponseSchema,
      signal,
      prompt: [
        "You are emulating a first-time participant opening a frozen Mandate 2038 prototype kit.",
        "This is an LLM simulation, not a claim about physical handling. Inspect the inventory before reading the rules.",
        participantContext(participant),
        "Record what you believe is present, how you would sort it, and concrete questions caused by the components alone.",
        `Kit identity:\n${JSON.stringify(kit.manifest, null, 2)}`,
        fencedSources(kit.documents.filter((document) => document.id === "component-reference"))
      ].join("\n\n")
    })
  ));

  const rulesReading = await stage("rules-reading", () => mapWithConcurrency(
    participants,
    registration.provider.maxConcurrent,
    (participant, index) => runner.run({
      requestId: `${registration.id}:rules-reading:seat-${participant.seat + 1}`,
      responseSchema: rulesResponseSchema,
      signal,
      prompt: [
        "You are a first-time Mandate 2038 participant reading the complete frozen Default Game Play Kit without facilitator help.",
        participantContext(participant),
        `Your earlier unboxing notes:\n${JSON.stringify(unboxing[index].output, null, 2)}`,
        "Reconstruct setup, cycle play, End-of-Era Resolution, scoring, and ending. Ask specific questions you would ask before play.",
        "Do not use outside knowledge or Advanced Play procedures.",
        fencedSources(kit.documents)
      ].join("\n\n")
    })
  ));
  const initialQuestions = questionsFrom(rulesReading, "questions", "rules");
  const initialFacilitation = await stage("initial-facilitation", async () => validateFacilitator(
    await runner.run({
      requestId: `${registration.id}:facilitator:initial`,
      responseSchema: facilitatorResponseSchema(initialQuestions, kit.documents),
      signal,
      prompt: facilitatorPrompt(initialQuestions, kit.documents, "pre-play rules session")
    }),
    initialQuestions,
    kit.documents
  ));

  const followup = await stage("participant-followup", () => mapWithConcurrency(
    participants,
    registration.provider.maxConcurrent,
    (participant, index) => {
      const answers = initialFacilitation.output.answers.filter((answer) =>
        initialQuestions.find((question) => question.id === answer.questionId)?.seat === participant.seat
      );
      return runner.run({
        requestId: `${registration.id}:followup:seat-${participant.seat + 1}`,
        responseSchema: followupResponseSchema,
        signal,
        prompt: [
          "Continue as the same first-time participant. Review the facilitator's source-grounded answers.",
          participantContext(participant),
          `Your rules reconstruction and questions:\n${JSON.stringify(rulesReading[index].output, null, 2)}`,
          `Facilitator answers:\n${JSON.stringify(answers, null, 2)}`,
          "State what is now resolved, any remaining concrete questions, and whether you are ready to begin under the frozen rules."
        ].join("\n\n")
      });
    }
  ));
  const remainingQuestions = questionsFrom(followup, "remainingQuestions", "followup");
  const followupFacilitation = remainingQuestions.length
    ? await stage("followup-facilitation", async () => validateFacilitator(
      await runner.run({
        requestId: `${registration.id}:facilitator:followup`,
        responseSchema: facilitatorResponseSchema(remainingQuestions, kit.documents),
        signal,
        prompt: facilitatorPrompt(remainingQuestions, kit.documents, "follow-up rules session")
      }),
      remainingQuestions,
      kit.documents
    ))
    : null;

  const gameReport = await stage("gameplay", () => simulationFactory({
    runs: 1,
    playerCount: 4,
    seed: registration.seed,
    sampleReplays: 1,
    profileIds: participants.map((participant) => participant.profileId),
    factionIds: participants.map((participant) => participant.factionId),
    backends: participants.map(() => "codex"),
    allowLlm: true,
    requireLlm: true,
    strictLlmEvidence: true,
    maxLlmDecisions: undefined,
    model: registration.provider.model,
    reasoningEffort: registration.provider.reasoningEffort,
    timeoutMs: registration.provider.timeoutMs,
    simulateNegotiation: true,
    includeObservations: true,
    rotateProfiles: false,
    rotateFactions: false,
    archiveLlmMatches: true,
    preRegistrationId: registration.id,
    preRegistration: {
      ...registrationProvenance,
      id: registration.id,
      locked: true,
      interpretationBoundary: registration.evidenceBoundary
    },
    experimentKind: "codex_controlled_session",
    signal
  }, onProgress));
  const gameSummary = summarizeGame(gameReport);

  const postgame = await stage("postgame-reconstruction", () => mapWithConcurrency(
    participants,
    registration.provider.maxConcurrent,
    (participant, index) => runner.run({
      requestId: `${registration.id}:postgame:seat-${participant.seat + 1}`,
      responseSchema: postgameResponseSchema,
      signal,
      prompt: [
        "Continue as the same Mandate 2038 participant after the recorded game.",
        participantContext(participant),
        `Your pre-play understanding:\n${JSON.stringify(followup[index].output, null, 2)}`,
        `Recorded game outcome:\n${JSON.stringify(gameSummary, null, 2)}`,
        "Without rereading the rules, explain the winner, World Ending, defining moments, remembered rules structure, confusing moments, and what you would teach differently."
      ].join("\n\n")
    })
  ));

  return {
    session: {
      schemaVersion: 1,
      artifactKind: "codex-controlled-session",
      evidenceLabel: "simulation",
      evidenceType: "llm_simulation",
      generatedAt: new Date().toISOString(),
      startedAt,
      id: registration.id,
      preregistration: { ...registrationProvenance, document: registration },
      physicalKit: {
        manifestPath: relative(projectRoot, kit.manifestPath),
        kitId: kit.manifest.kitId,
        kitFingerprint: kit.manifest.kitFingerprint,
        sourceCommit: kit.manifest.identity.sourceCommit
      },
      release: registration.release,
      participants,
      stages: {
        unboxing,
        rulesReading,
        initialQuestions,
        initialFacilitation,
        followup,
        remainingQuestions,
        followupFacilitation,
        gameplay: gameSummary,
        postgame
      },
      gameplayIdentity: {
        reportType: gameReport.reportType,
        reportFingerprint: gameReport.reportFingerprint,
        game: gameReport.game,
        engine: gameReport.engine,
        strategies: gameReport.strategies,
        provenance: gameReport.provenance,
        usedLlmDecisions: gameReport.configuration.usedLlmDecisions,
        completedLlmArchives: gameReport.configuration.completedLlmArchives
      },
      limitations: [
        "This is LLM simulation evidence, not a facilitated or blind human playtest.",
        "Unboxing and rules reading are text-grounded emulations without physical handling.",
        "Provider duration is machine latency and cannot estimate human setup, teaching, or play duration.",
        "One match cannot establish balance, complexity weight, teachability, or comparative provider quality."
      ]
    },
    gameReport
  };
}
