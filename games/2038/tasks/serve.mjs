import { createReadStream, existsSync, statSync } from "node:fs";
import { readdir, readFile, stat } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, join, normalize, resolve } from "node:path";
import { randomBytes, randomUUID, timingSafeEqual } from "node:crypto";
import { archiveSimulationReport } from "../lab/report-archive.js";
import { cancellationError } from "../lab/cancellation.js";
import { runExperiment } from "../lab/runtime/run-experiment.js";
import { createInteractiveGame } from "../lab/runtime/create-interactive-game.js";

const projectRoot = resolve(import.meta.dirname, "..");
const simulationArchiveDirectory = resolve(
  projectRoot,
  "evidence/studies/simulation"
);
const port = Number(process.env.FRONTIER_PORT || 8038);
const mime = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
  ".svg": "image/svg+xml"
};
const jobs = new Map();
const games = new Map();
const interactiveLlmDecisionLimit = 24;
const allowedHosts = new Set([`localhost:${port}`, `127.0.0.1:${port}`]);
const localOrigins = new Set([
  `http://localhost:${port}`,
  `http://127.0.0.1:${port}`
]);
const remoteOrigins = new Set(
  (
    process.env.FRONTIER_BRIDGE_ORIGINS ||
    "https://canvascontext.com"
  ).split(",").map((origin) => origin.trim()).filter(Boolean)
);
const allowedOrigins = new Set([...localOrigins, ...remoteOrigins]);
const bridgeToken = process.env.FRONTIER_BRIDGE_TOKEN ||
  randomBytes(18).toString("base64url");

function tokenMatches(value) {
  if (typeof value !== "string") return false;
  const actual = Buffer.from(value);
  const expected = Buffer.from(bridgeToken);
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}

function applyCors(request, response) {
  const origin = request.headers.origin;
  if (!origin || !allowedOrigins.has(origin)) return;
  response.setHeader("access-control-allow-origin", origin);
  response.setHeader("vary", "Origin");
}

function authorizeApiRequest(request, response) {
  if (!allowedHosts.has(request.headers.host)) {
    json(response, 403, { error: "Untrusted Host header." });
    return false;
  }
  const origin = request.headers.origin;
  if (origin && !allowedOrigins.has(origin)) {
    json(response, 403, { error: "Untrusted Origin." });
    return false;
  }
  applyCors(request, response);
  if (
    origin &&
    remoteOrigins.has(origin) &&
    !tokenMatches(request.headers["x-mandate-2038-bridge-token"])
  ) {
    json(response, 401, { error: "Local bridge pairing token is missing or invalid." });
    return false;
  }
  return true;
}

function preflight(request, response) {
  if (!allowedHosts.has(request.headers.host)) {
    json(response, 403, { error: "Untrusted Host header." });
    return;
  }
  const origin = request.headers.origin;
  if (!origin || !allowedOrigins.has(origin)) {
    json(response, 403, { error: "Untrusted Origin." });
    return;
  }
  applyCors(request, response);
  response.setHeader("access-control-allow-methods", "GET, POST, OPTIONS");
  response.setHeader(
    "access-control-allow-headers",
    "Content-Type, X-Mandate-2038-Bridge-Token"
  );
  response.setHeader("access-control-max-age", "600");
  if (request.headers["access-control-request-private-network"] === "true") {
    response.setHeader("access-control-allow-private-network", "true");
  }
  response.writeHead(204);
  response.end();
}

function json(response, status, value) {
  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store"
  });
  response.end(`${JSON.stringify(value)}\n`);
}

async function readJson(request) {
  const chunks = [];
  let bytes = 0;
  for await (const chunk of request) {
    bytes += chunk.length;
    if (bytes > 1_000_000) throw new RangeError("Request body exceeds 1 MB.");
    chunks.push(chunk);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function pruneJobs() {
  const completed = [...jobs.values()]
    .filter((job) => ["complete", "failed", "cancelled"].includes(job.status))
    .sort((left, right) => left.updatedAt - right.updatedAt);
  while (jobs.size > 20 && completed.length) {
    jobs.delete(completed.shift().id);
  }
}

function publicSimulationJob(job) {
  return {
    id: job.id,
    status: job.status,
    progress: job.progress,
    createdAt: job.createdAt,
    updatedAt: job.updatedAt,
    cancelledAt: job.cancelledAt || null,
    failure: job.failure || null,
    error: job.error || null,
    ...(job.status === "complete" ? {
      report: job.report,
      archive: job.archive
    } : {})
  };
}

function simulationFailure(error) {
  return {
    outcome: error?.evidenceOutcome || "invalid",
    message: error?.message || "Unknown simulation failure.",
    providerReceipt: error?.providerReceipt
      ? structuredClone(error.providerReceipt)
      : null
  };
}

function archivedReportPath(fileName) {
  if (!/^[^/\\]+\.json$/u.test(fileName)) return null;
  const path = resolve(simulationArchiveDirectory, fileName);
  return path.startsWith(`${simulationArchiveDirectory}/`) ? path : null;
}

async function recentSimulationReports() {
  const entries = await readdir(simulationArchiveDirectory, {
    withFileTypes: true
  });
  const reports = await Promise.all(entries
    .filter((entry) => entry.isFile() && entry.name.endsWith(".json"))
    .map(async (entry) => {
      const metadata = await stat(join(simulationArchiveDirectory, entry.name));
      return {
        fileName: entry.name,
        modifiedAt: metadata.mtime.toISOString(),
        bytes: metadata.size
      };
    }));
  const readable = [];
  for (const entry of reports.sort((left, right) => right.modifiedAt.localeCompare(left.modifiedAt))) {
    try {
      const report = JSON.parse(await readFile(join(simulationArchiveDirectory, entry.fileName), "utf8"));
      if (report?.evidenceLabel !== "simulation" || typeof report.reportType !== "string") continue;
      readable.push(entry);
      if (readable.length === 24) break;
    } catch {
      // A partial write or an auxiliary study artifact is not a viewable report.
    }
  }
  return readable;
}

async function sendArchivedSimulationReport(response, fileName) {
  const path = archivedReportPath(fileName);
  if (!path || !existsSync(path)) {
    json(response, 404, { error: "Simulation report not found." });
    return;
  }
  try {
    const report = JSON.parse(await readFile(path, "utf8"));
    if (report?.evidenceLabel !== "simulation") {
      json(response, 422, { error: "Archived file is not simulation evidence." });
      return;
    }
    json(response, 200, report);
  } catch {
    json(response, 422, { error: "Archived simulation report is invalid JSON." });
  }
}

async function startSimulation(request, response) {
  try {
    if (!allowedHosts.has(request.headers.host)) {
      json(response, 403, { error: "Untrusted Host header." });
      return;
    }
    if (request.headers.origin && !allowedOrigins.has(request.headers.origin)) {
      json(response, 403, { error: "Untrusted Origin." });
      return;
    }
    if ([...jobs.values()].some((job) => job.status === "queued" || job.status === "running")) {
      json(response, 409, { error: "Another simulation job is already running." });
      return;
    }
    const options = await readJson(request);
    if (
      options.allowLlm &&
      options.maxLlmDecisions !== undefined &&
      (
        !Number.isInteger(Number(options.maxLlmDecisions)) ||
        Number(options.maxLlmDecisions) < 0 ||
        Number(options.maxLlmDecisions) > 10000
      )
    ) {
      json(response, 400, {
        error: "Web simulation LLM decision budgets must be integers from 0 to 10000."
      });
      return;
    }
    const id = randomUUID();
    const job = {
      id,
      status: "queued",
      controller: new AbortController(),
      publicationValid: true,
      progress: {
        phase: options.mode || "tournament",
        completed: 0,
        total: Number(
          options.mode === "strategy-evolution"
            ? (options.generations || 4) * (options.population || 6)
            : options.mode === "balance-audit"
              ? options.maximumMatches || options.runs || 480
            : options.mode === "llm-holdout"
              ? options.runs || 2
            : options.mode === "faction-swap"
              ? options.runs || 100
            : options.mode === "rule-search"
              ? options.iterations || 12
              : options.runs || 100
        )
      },
      createdAt: Date.now(),
      updatedAt: Date.now()
    };
    jobs.set(id, job);
    json(response, 202, { id, status: job.status });

    queueMicrotask(async () => {
      if (job.controller.signal.aborted) return;
      job.status = "running";
      try {
        const completedReport = await runExperiment({
          ...options,
          signal: job.controller.signal
        }, (progress) => {
          if (job.controller.signal.aborted) return;
          job.progress = {
            phase: progress.phase || options.mode || "tournament",
            completed: progress.completed,
            total: progress.total || progress.runs,
            kind: progress.kind || null,
            round: progress.round ?? null,
            cycle: progress.cycle ?? null,
            cycleNumber: progress.cycleNumber ?? null,
            turnNumber: progress.turnNumber ?? null,
            completedSeat: progress.completedSeat ?? null,
            llmDecisionsUsed: progress.llmDecisionsUsed ?? null
          };
          job.updatedAt = Date.now();
        });
        if (!job.publicationValid) return;
        const archive = await archiveSimulationReport(completedReport, {
          projectRoot,
          jobId: id,
          canPublish: () => job.publicationValid && !job.controller.signal.aborted
        });
        if (!job.publicationValid) return;
        job.report = completedReport;
        job.archive = archive;
        job.status = "complete";
      } catch (error) {
        if (!job.publicationValid || job.controller.signal.aborted || error?.name === "AbortError") {
          job.status = "cancelled";
          job.error = null;
          job.failure = simulationFailure(error);
        } else {
          job.status = "failed";
          job.error = error.message;
          job.failure = simulationFailure(error);
        }
      }
      job.updatedAt = Date.now();
      pruneJobs();
    });
  } catch (error) {
    json(response, error instanceof RangeError ? 413 : 400, { error: error.message });
  }
}

function cancelSimulation(response, id) {
  const job = jobs.get(id);
  if (!job) {
    json(response, 404, { error: "Simulation job not found." });
    return;
  }
  if (job.status === "cancelled") {
    json(response, 200, publicSimulationJob(job));
    return;
  }
  if (["complete", "failed"].includes(job.status)) {
    json(response, 409, { error: "Simulation job has already settled." });
    return;
  }
  job.publicationValid = false;
  job.status = "cancelled";
  job.cancelledAt = Date.now();
  job.updatedAt = job.cancelledAt;
  job.controller.abort(cancellationError("Simulation job cancelled by the Lab."));
  json(response, 202, publicSimulationJob(job));
  pruneJobs();
}

function publicGame(game) {
  return {
    id: game.id,
    status: game.status,
    createdAt: game.createdAt,
    updatedAt: game.updatedAt,
    pending: game.pending,
    state: game.runtime?.match.snapshot() || null,
    replay: game.runtime?.match.replay || [],
    opponents: game.runtime?.opponents?.map((opponent) => ({
      seat: opponent.seat,
      profileId: opponent.profile.id,
      profileName: opponent.profile.name,
      backend: opponent.backend,
      remainingLlmDecisions: opponent.decisionBudget?.remaining ?? null
    })) || [],
    result: game.result || null,
    error: game.error || null
  };
}

async function startGame(request, response) {
  try {
    if (!allowedHosts.has(request.headers.host)) {
      json(response, 403, { error: "Untrusted Host header." });
      return;
    }
    if (request.headers.origin && !allowedOrigins.has(request.headers.origin)) {
      json(response, 403, { error: "Untrusted Origin." });
      return;
    }
    const options = await readJson(request);
    const id = randomUUID();
    const game = {
      id,
      status: "starting",
      pending: null,
      createdAt: Date.now(),
      updatedAt: Date.now()
    };
    games.set(id, game);
    game.runtime = await createInteractiveGame(options, (packet) => {
      game.pending = packet;
      game.status = "waiting";
      game.updatedAt = Date.now();
    });
    game.status = "running";
    queueMicrotask(async () => {
      try {
        game.result = await game.runtime.match.play(game.runtime.policies);
        game.pending = null;
        game.status = "complete";
      } catch (error) {
        game.pending = null;
        game.status = "failed";
        game.error = error.message;
      }
      game.updatedAt = Date.now();
    });
    json(response, 202, publicGame(game));
  } catch (error) {
    json(response, 400, { error: error.message });
  }
}

async function submitGameDecision(request, response, game) {
  try {
    if (!game || game.status !== "waiting" || !game.pending) {
      json(response, 409, { error: "This game is not waiting for a human decision." });
      return;
    }
    const body = await readJson(request);
    if (body.requestId && body.requestId !== game.pending.requestId) {
      json(response, 409, { error: "The submitted decision belongs to a stale request." });
      return;
    }
    game.runtime.human.submit(body.decisionId, body.rationale);
    game.pending = null;
    game.status = "running";
    game.updatedAt = Date.now();
    await new Promise((resolve) => setImmediate(resolve));
    json(response, 200, publicGame(game));
  } catch (error) {
    json(response, 400, { error: error.message });
  }
}

createServer(async (request, response) => {
  const url = new URL(request.url, `http://${request.headers.host || "localhost"}`);
  if (url.pathname.startsWith("/api/") && request.method === "OPTIONS") {
    preflight(request, response);
    return;
  }
  if (url.pathname.startsWith("/api/") && !authorizeApiRequest(request, response)) {
    return;
  }
  if (request.method === "GET" && url.pathname === "/api/bridge") {
    json(response, 200, {
      connected: true,
      service: "mandate-2038-local-bridge",
      interactiveBackends: [
        "weighted",
        "greedy",
        "claude",
        "codex",
        "hybrid-claude",
        "hybrid-codex"
      ],
      maximumLlmDecisionsPerOpponent: interactiveLlmDecisionLimit
    });
    return;
  }
  if (request.method === "GET" && url.pathname === "/api/simulation-reports") {
    try {
      json(response, 200, { reports: await recentSimulationReports() });
    } catch {
      json(response, 500, { error: "Could not list archived simulation reports." });
    }
    return;
  }
  const archivedReportMatch = url.pathname.match(/^\/api\/simulation-reports\/([^/]+)$/);
  if (request.method === "GET" && archivedReportMatch) {
    await sendArchivedSimulationReport(response, archivedReportMatch[1]);
    return;
  }
  if (request.method === "POST" && url.pathname === "/api/simulations") {
    await startSimulation(request, response);
    return;
  }
  const simulationCancelMatch = url.pathname.match(/^\/api\/simulations\/([a-f0-9-]+)\/cancel$/);
  if (request.method === "POST" && simulationCancelMatch) {
    cancelSimulation(response, simulationCancelMatch[1]);
    return;
  }
  if (request.method === "POST" && url.pathname === "/api/games") {
    await startGame(request, response);
    return;
  }
  const gameMatch = url.pathname.match(/^\/api\/games\/([a-f0-9-]+)$/);
  const gameDecisionMatch = url.pathname.match(
    /^\/api\/games\/([a-f0-9-]+)\/decisions$/
  );
  if (request.method === "GET" && gameMatch) {
    const game = games.get(gameMatch[1]);
    if (!game) {
      json(response, 404, { error: "Game not found." });
      return;
    }
    json(response, 200, publicGame(game));
    return;
  }
  if (request.method === "POST" && gameDecisionMatch) {
    await submitGameDecision(request, response, games.get(gameDecisionMatch[1]));
    return;
  }
  const jobMatch = url.pathname.match(/^\/api\/simulations\/([a-f0-9-]+)$/);
  if (request.method === "GET" && jobMatch) {
    const job = jobs.get(jobMatch[1]);
    if (!job) {
      json(response, 404, { error: "Simulation job not found." });
      return;
    }
    json(response, 200, publicSimulationJob(job));
    return;
  }
  if (request.method !== "GET" && request.method !== "HEAD") {
    json(response, 405, { error: "Method not allowed." });
    return;
  }
  if (url.pathname === "/docs") {
    response.writeHead(308, {
      location: "/docs/",
      "cache-control": "no-store"
    });
    response.end();
    return;
  }
  if (url.pathname === "/core-rules.html") {
    response.writeHead(308, {
      location: "/docs/core-rules.html",
      "cache-control": "no-store"
    });
    response.end();
    return;
  }
  const requested = url.pathname === "/"
    ? "/dist/site/index.html"
    : url.pathname === "/first-game-guide"
      ? "/dist/site/first-game-guide.html"
    : url.pathname === "/lab"
      ? "/dist/site/simulation.html"
      : url.pathname === "/docs/"
        ? "/dist/site/docs/index.html"
        : url.pathname.startsWith("/docs/")
          ? `/dist/site${url.pathname}`
        : url.pathname === "/gallery" || url.pathname === "/gallery/"
          ? "/dist/site/gallery.html"
          : url.pathname;
  const relative = normalize(decodeURIComponent(requested)).replace(/^(\.\.[/\\])+/, "");
  const filePath = join(projectRoot, relative);
  if (!filePath.startsWith(projectRoot) || !existsSync(filePath) || !statSync(filePath).isFile()) {
    response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
    response.end("Not found");
    return;
  }
  response.writeHead(200, {
    "content-type": mime[extname(filePath)] || "application/octet-stream",
    "cache-control": "no-store"
  });
  createReadStream(filePath).pipe(response);
}).listen(port, "127.0.0.1", () => {
  process.stdout.write(`Mandate 2038 prototype:      http://localhost:${port}/\n`);
  process.stdout.write(`Mandate 2038 first game guide: http://localhost:${port}/first-game-guide\n`);
  process.stdout.write(`Mandate 2038 simulation lab: http://localhost:${port}/lab\n`);
  process.stdout.write(`Mandate 2038 docs reader:    http://localhost:${port}/docs\n`);
  process.stdout.write(`Mandate 2038 content gallery: http://localhost:${port}/gallery\n`);
  process.stdout.write(
    `Mandate 2038 deployed bridge: ${[...remoteOrigins].join(", ")}\n`
  );
  process.stdout.write(`Mandate 2038 bridge token: ${bridgeToken}\n`);
  process.stdout.write(
    `Interactive LLM cap: ${interactiveLlmDecisionLimit} decisions per opponent\n`
  );
});
