import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import { relative, resolve } from "node:path";
import { promisify } from "node:util";
import { CodexCliRunner } from "../callers/codex-cli-runner.js";
import { CodexCliCaller } from "../callers/codex-cli-caller.js";
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

export const rulesDocumentResponseSchema = objectSchema({
  summary: { type: "string", minLength: 1 },
  keyRules: stringArray(2, 12),
  crossReferencesNeeded: stringArray(0, 6),
  questions: questionArray(0, 4)
});

export const followupResponseSchema = objectSchema({
  summary: { type: "string", minLength: 1 },
  resolvedUnderstanding: stringArray(2),
  remainingQuestions: questionArray(0, 4),
  readyToPlay: { type: "boolean" }
});

export const finalReadinessResponseSchema = objectSchema({
  summary: { type: "string", minLength: 1 },
  resolvedSessionContext: stringArray(2, 8),
  blockingQuestions: questionArray(0, 4),
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

export function chunkRulesDocument(document, maximumCharacters = 8000) {
  const chunks = [];
  let start = 0;
  let activeHeading = document.headings[0] || document.fileName;
  while (start < document.contents.length) {
    let end = Math.min(start + maximumCharacters, document.contents.length);
    if (end < document.contents.length) {
      const paragraphBreak = document.contents.lastIndexOf("\n\n", end);
      if (paragraphBreak > start + Math.floor(maximumCharacters / 2)) {
        end = paragraphBreak + 2;
      }
    }
    const contents = document.contents.slice(start, end);
    const localHeadings = headings(contents);
    chunks.push({
      id: `${document.id}-part-${chunks.length + 1}`,
      sourceId: document.id,
      fileName: document.fileName,
      part: chunks.length + 1,
      contents,
      activeHeading,
      headings: localHeadings
    });
    const lastHeading = localHeadings.at(-1);
    if (lastHeading) activeHeading = lastHeading;
    start = end;
  }
  return chunks.map((chunk) => ({ ...chunk, parts: chunks.length }));
}

export function facilitatorResponseSchema(questions, documents) {
  return objectSchema({
    answers: {
      type: "array",
      minItems: questions.length,
      maxItems: questions.length,
      items: objectSchema({
        questionId: {
          type: "string",
          enum: questions.map((question) => question.id)
        },
        answer: { type: "string", minLength: 1 },
        citations: {
          type: "array",
          minItems: 1,
          maxItems: 4,
          items: {
            anyOf: documents.map((document) => objectSchema({
              sourceId: { type: "string", const: document.id },
              heading: { type: "string", enum: document.headings }
            }))
          }
        }
      })
    },
    unresolved: stringArray(0, questions.length)
  });
}

function facilitatorEvidenceSchema(questions, document) {
  return objectSchema({
    findings: {
      type: "array",
      minItems: 0,
      maxItems: questions.length,
      items: objectSchema({
        questionId: {
          type: "string",
          enum: questions.map((question) => question.id)
        },
        evidence: { type: "string", minLength: 1 },
        heading: { type: "string", enum: document.headings }
      })
    }
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

async function mapWithConcurrency(values, concurrency, operation, onItemComplete) {
  const results = new Array(values.length);
  let cursor = 0;
  const workers = Array.from(
    { length: Math.min(concurrency, values.length) },
    async () => {
      while (cursor < values.length) {
        const index = cursor;
        cursor += 1;
        results[index] = await operation(values[index], index);
        await onItemComplete?.(values[index], index, results[index]);
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
    (document.provider.maximumAttemptsPerRequest !== undefined &&
      (!Number.isInteger(document.provider.maximumAttemptsPerRequest) ||
        document.provider.maximumAttemptsPerRequest < 1 ||
        document.provider.maximumAttemptsPerRequest > 3)) ||
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
  const readingDocuments = documents.flatMap((document) => chunkRulesDocument(document));
  return { root, manifestPath, manifest, documents, readingDocuments };
}

function participantContext(participant) {
  return `Human seat ${participant.seat + 1} (engine seat ${participant.seat}); faction ${participant.factionName} (${participant.factionId}); decision profile ${participant.profileId}.`;
}

export function finalReadinessPrompt({
  participant,
  playerCount,
  followup,
  answers,
  unresolved
}) {
  return [
    "Continue as the same first-time Mandate 2038 participant after the final facilitator response.",
    participantContext(participant),
    `Your follow-up record:\n${JSON.stringify(followup, null, 2)}`,
    `Final source-grounded answers:\n${JSON.stringify(answers, null, 2)}`,
    `Question ids still unresolved by the frozen documents:\n${JSON.stringify(unresolved)}`,
    "The following operational session facts are authoritative and resolve any conflicting inference in your follow-up record:",
    `- This is a ${playerCount}-player Default Game. Your registered faction is exactly ${participant.factionName} (${participant.factionId}); other faction entries in the Card and Board Reference do not apply to you.`,
    `- ${participant.profileId} is the simulator's decision persona, not a player ability, aid, restriction, or hidden rule.`,
    "- No Facility is placed during setup. All four begin in supply; the first Facility has the integrated starting-grid identifier and receives that Power after it is legally constructed.",
    "- Core Rules are the baseline authority. A Headline changes only its named rule while that specific Headline is currently revealed and active; unrelated Headline variants are not simultaneous alternatives.",
    "- A black Systemic Risk cube applies the current Era's colored-cube Audit penalty to every player with at least three Customers.",
    "- The shuffled board, Initiative, revealed Headline, current Mandate, legal targets, costs, applicable card text, and complete legal choices are exposed by the game state and legal-choice packet when each decision occurs.",
    "- You may rely on those visible legal choices during play, but not on hidden simulator state.",
    "State whether every question that blocks legal play is resolved. List only genuinely blocking questions. Do not retain a blocker that an authoritative session fact above resolves. You may be ready even when future shuffled cards are not yet revealed."
  ].join("\n\n");
}

export function validateFinalReadiness(results) {
  if (!Array.isArray(results) || results.length !== 4) {
    throw new Error("Final readiness requires exactly four participant records.");
  }
  const blocked = results.flatMap((result, seat) => {
    const output = result?.output;
    const questions = output?.blockingQuestions;
    if (!Array.isArray(questions)) {
      throw new Error(`Final readiness seat ${seat + 1} omitted blockingQuestions.`);
    }
    return output.readyToPlay === true && questions.length === 0
      ? []
      : [{ seat, readyToPlay: output.readyToPlay === true, blockingQuestions: questions }];
  });
  if (blocked.length) {
    throw new Error(`Final readiness failed for engine seats ${blocked.map((entry) => entry.seat).join(", ")}.`);
  }
  return results;
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

function facilitatorEvidencePrompt(questions, document, label) {
  return [
    `You are collecting source evidence for a recorded Mandate 2038 ${label}.`,
    "Do not answer from memory and do not use tools. Read only the one embedded frozen document.",
    `This is part ${document.part} of ${document.parts} from ${document.fileName}. Its inherited section heading is ${document.activeHeading}.`,
    "For each question this source chunk materially helps answer, record concise evidence and the exact Markdown heading. Omit questions this chunk does not resolve.",
    `Questions:\n${JSON.stringify(questions, null, 2)}`,
    fencedSources([document])
  ].join("\n\n");
}

function facilitatorSynthesisPrompt(questions, sourceEvidence, label) {
  return [
    `You are the rules facilitator for a recorded Mandate 2038 ${label}.`,
    "Answer only from the source-evidence packets below. Do not use tools, outside knowledge, or invent intent.",
    "Preserve the exact source id and Markdown heading attached to every cited packet.",
    "If the packets genuinely do not resolve something, say so and add its question id to unresolved.",
    `Questions:\n${JSON.stringify(questions, null, 2)}`,
    `Source-evidence packets:\n${JSON.stringify(sourceEvidence, null, 2)}`
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
  onParticipantComplete,
  onProviderAttempt,
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
  const maximumAttempts = registration.provider.maximumAttemptsPerRequest || 1;
  const runStructured = async (request) => {
    const failedAttempts = [];
    for (let attempt = 1; attempt <= maximumAttempts; attempt += 1) {
      try {
        const result = await runner.run(request);
        return {
          ...result,
          receipt: {
            ...result.receipt,
            attempt,
            maximumAttempts,
            failedAttempts
          }
        };
      } catch (error) {
        const failure = {
          attempt,
          maximumAttempts,
          errorClass: error?.name || "Error",
          errorMessage: error?.message || "Unknown provider failure.",
          providerExitCode: Number.isInteger(error?.details?.code) ? error.details.code : null,
          providerTimeoutMs: error?.details?.timeoutMs || null
        };
        failedAttempts.push(failure);
        await onProviderAttempt?.({
          requestId: request.requestId,
          completedAt: new Date().toISOString(),
          ...failure
        });
        if (attempt === maximumAttempts) {
          error.providerAttempts = failedAttempts;
          throw error;
        }
      }
    }
    throw new Error("Structured provider retry loop ended without a result.");
  };
  const gameplayCallerFactory = ({ model, reasoningEffort, timeoutMs }) => {
    const caller = new CodexCliCaller({ model, reasoningEffort, timeoutMs });
    return {
      decisionProtocolVersion: caller.decisionProtocolVersion,
      async decide(packet, options) {
        const failedAttempts = [];
        for (let attempt = 1; attempt <= maximumAttempts; attempt += 1) {
          try {
            const result = await caller.decide(packet, options);
            return {
              ...result,
              receipt: {
                ...result.receipt,
                attempt,
                maximumAttempts,
                failedAttempts
              }
            };
          } catch (error) {
            failedAttempts.push({
              attempt,
              maximumAttempts,
              errorClass: error?.name || "Error",
              errorMessage: error?.message || "Unknown provider failure.",
              providerReceipt: error?.providerReceipt || null
            });
            if (attempt === maximumAttempts) {
              error.providerAttempts = failedAttempts;
              throw error;
            }
          }
        }
        throw new Error("Gameplay provider retry loop ended without a result.");
      }
    };
  };
  const participants = [...registration.participants].sort((left, right) => left.seat - right.seat);
  const startedAt = new Date().toISOString();
  const stage = async (id, operation) => {
    onProgress?.({ phase: "session_stage", id, status: "started" });
    const result = await operation();
    await onStageComplete?.({ id, completedAt: new Date().toISOString(), result });
    onProgress?.({ phase: "session_stage", id, status: "completed" });
    return result;
  };
  const facilitate = async (stagePrefix, questions, label) => {
    const sourceEvidence = {};
    for (const document of kit.readingDocuments) {
      const originalDocument = kit.documents.find((candidate) =>
        candidate.id === document.sourceId
      );
      const sourceStageId = `${stagePrefix}-${document.id}`;
      sourceEvidence[document.id] = {
        sourceId: document.sourceId,
        part: document.part,
        parts: document.parts,
        activeHeading: document.activeHeading,
        result: await stage(sourceStageId, () => runStructured({
          requestId: `${registration.id}:${sourceStageId}`,
          responseSchema: facilitatorEvidenceSchema(questions, originalDocument),
          signal,
          prompt: facilitatorEvidencePrompt(questions, document, label)
        }))
      };
    }
    const synthesis = await stage(`${stagePrefix}-synthesis`, async () => validateFacilitator(
      await runStructured({
        requestId: `${registration.id}:${stagePrefix}:synthesis`,
        responseSchema: facilitatorResponseSchema(questions, kit.documents),
        signal,
        prompt: facilitatorSynthesisPrompt(questions, sourceEvidence, label)
      }),
      questions,
      kit.documents
    ));
    return { sourceEvidence, synthesis };
  };

  const unboxing = await stage("unboxing", () => mapWithConcurrency(
    participants,
    registration.provider.maxConcurrent,
    (participant) => runStructured({
      requestId: `${registration.id}:unboxing:seat-${participant.seat + 1}`,
      responseSchema: unboxingResponseSchema,
      signal,
      prompt: [
        "You are emulating a first-time participant opening a frozen Mandate 2038 prototype kit.",
        "This is an LLM simulation, not a claim about physical handling. Inspect the inventory before reading the rules.",
        "Do not use tools or inspect the filesystem; the complete allowed inventory source is embedded below.",
        participantContext(participant),
        "Record what you believe is present, how you would sort it, and concrete questions caused by the components alone.",
        `Kit identity:\n${JSON.stringify(kit.manifest, null, 2)}`,
        fencedSources(kit.documents.filter((document) => document.id === "component-reference"))
      ].join("\n\n")
    }),
    (participant, _index, result) => onParticipantComplete?.({
      stageId: "unboxing",
      seat: participant.seat,
      completedAt: new Date().toISOString(),
      result
    })
  ));

  const documentReadings = {};
  for (const document of kit.readingDocuments) {
    const stageId = `rules-reading-${document.id}`;
    documentReadings[document.id] = await stage(stageId, () => mapWithConcurrency(
      participants,
      registration.provider.maxConcurrent,
      (participant, index) => runStructured({
        requestId: `${registration.id}:${stageId}:seat-${participant.seat + 1}`,
        responseSchema: rulesDocumentResponseSchema,
        signal,
        prompt: [
          `You are a first-time Mandate 2038 participant reading part ${document.part} of ${document.parts} from ${document.fileName} without facilitator help.`,
          "Do not use tools or inspect the filesystem; the complete source chunk is embedded below.",
          participantContext(participant),
          `Your earlier unboxing notes:\n${JSON.stringify(unboxing[index].output, null, 2)}`,
          `This part inherits the section heading ${document.activeHeading}. Record the rules this source chunk contributes, explicit cross-references you still need, and concrete questions. Do not use outside knowledge or Advanced Play procedures.`,
          fencedSources([document])
        ].join("\n\n")
      }),
      (participant, _index, result) => onParticipantComplete?.({
        stageId,
        seat: participant.seat,
        completedAt: new Date().toISOString(),
        result
      })
    ));
  }
  const rulesReading = await stage("rules-synthesis", () => mapWithConcurrency(
    participants,
    registration.provider.maxConcurrent,
    (participant, index) => runStructured({
      requestId: `${registration.id}:rules-synthesis:seat-${participant.seat + 1}`,
      responseSchema: rulesResponseSchema,
      signal,
      prompt: [
        "You are the same first-time participant after reading all four frozen Default Game documents.",
        "Do not use tools or outside knowledge. Synthesize only the recorded document-reading notes below.",
        participantContext(participant),
        `Document-reading records:\n${JSON.stringify(Object.fromEntries(
          Object.entries(documentReadings).map(([id, results]) => [id, results[index].output])
        ), null, 2)}`,
        "Reconstruct setup, cycle play, End-of-Era Resolution, scoring, and ending. Ask the specific questions you would ask before play."
      ].join("\n\n")
    }),
    (participant, _index, result) => onParticipantComplete?.({
      stageId: "rules-synthesis",
      seat: participant.seat,
      completedAt: new Date().toISOString(),
      result
    })
  ));
  const initialQuestions = questionsFrom(rulesReading, "questions", "rules");
  const initialFacilitation = await facilitate(
    "initial-facilitation",
    initialQuestions,
    "pre-play rules session"
  );

  const followup = await stage("participant-followup", () => mapWithConcurrency(
    participants,
    registration.provider.maxConcurrent,
    (participant, index) => {
      const answers = initialFacilitation.synthesis.output.answers.filter((answer) =>
        initialQuestions.find((question) => question.id === answer.questionId)?.seat === participant.seat
      );
      return runStructured({
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
    },
    (participant, _index, result) => onParticipantComplete?.({
      stageId: "participant-followup",
      seat: participant.seat,
      completedAt: new Date().toISOString(),
      result
    })
  ));
  const remainingQuestions = questionsFrom(followup, "remainingQuestions", "followup");
  const followupFacilitation = remainingQuestions.length
    ? await facilitate(
      "followup-facilitation",
      remainingQuestions,
      "follow-up rules session"
    )
    : null;

  const finalReadiness = await stage("final-readiness", async () => validateFinalReadiness(
    await mapWithConcurrency(
      participants,
      registration.provider.maxConcurrent,
      (participant, index) => {
        const ownQuestions = remainingQuestions.filter((question) => question.seat === participant.seat);
        const ownQuestionIds = new Set(ownQuestions.map((question) => question.id));
        const answers = followupFacilitation?.synthesis.output.answers.filter((answer) =>
          ownQuestionIds.has(answer.questionId)
        ) || [];
        const unresolved = followupFacilitation?.synthesis.output.unresolved.filter((id) =>
          ownQuestionIds.has(id)
        ) || [];
        return runStructured({
          requestId: `${registration.id}:final-readiness:seat-${participant.seat + 1}`,
          responseSchema: finalReadinessResponseSchema,
          signal,
          prompt: finalReadinessPrompt({
            participant,
            playerCount: registration.playerCount,
            followup: followup[index].output,
            answers,
            unresolved
          })
        });
      },
      (participant, _index, result) => onParticipantComplete?.({
        stageId: "final-readiness",
        seat: participant.seat,
        completedAt: new Date().toISOString(),
        result
      })
    )
  ));

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
    callerFactory: gameplayCallerFactory,
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
    (participant, index) => runStructured({
      requestId: `${registration.id}:postgame:seat-${participant.seat + 1}`,
      responseSchema: postgameResponseSchema,
      signal,
      prompt: [
        "Continue as the same Mandate 2038 participant after the recorded game.",
        participantContext(participant),
        `Your final pre-play readiness record:\n${JSON.stringify(finalReadiness[index].output, null, 2)}`,
        `Recorded game outcome:\n${JSON.stringify(gameSummary, null, 2)}`,
        "Without rereading the rules, explain the winner, World Ending, defining moments, remembered rules structure, confusing moments, and what you would teach differently."
      ].join("\n\n")
    }),
    (participant, _index, result) => onParticipantComplete?.({
      stageId: "postgame-reconstruction",
      seat: participant.seat,
      completedAt: new Date().toISOString(),
      result
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
        sourceCommit: kit.manifest.identity.sourceCommit,
        readingCoverage: kit.documents.map((document) => ({
          sourceId: document.id,
          fileName: document.fileName,
          parts: kit.readingDocuments.filter((chunk) =>
            chunk.sourceId === document.id
          ).length
        }))
      },
      release: registration.release,
      participants,
      stages: {
        unboxing,
        documentReadings,
        rulesReading,
        initialQuestions,
        initialFacilitation,
        followup,
        remainingQuestions,
        followupFacilitation,
        finalReadiness,
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
