import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize, resolve } from "node:path";
import { randomUUID } from "node:crypto";
import { archiveSimulationReport } from "../simulation/report-archive.js";
import { runExperiment } from "../simulation/runtime/run-experiment.js";
import { createInteractiveGame } from "../simulation/runtime/create-interactive-game.js";

const projectRoot = resolve(import.meta.dirname, "..");
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
const allowedHosts = new Set([`localhost:${port}`, `127.0.0.1:${port}`]);
const allowedOrigins = new Set([
  `http://localhost:${port}`,
  `http://127.0.0.1:${port}`
]);

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
    .filter((job) => job.status === "complete" || job.status === "failed")
    .sort((left, right) => left.updatedAt - right.updatedAt);
  while (jobs.size > 20 && completed.length) {
    jobs.delete(completed.shift().id);
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
    if (options.allowLlm && Number(options.maxLlmDecisions || 24) > 240) {
      json(response, 400, {
        error: "Web simulation jobs are limited to 240 authorized LLM decisions."
      });
      return;
    }
    const id = randomUUID();
    const job = {
      id,
      status: "queued",
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
      job.status = "running";
      try {
        job.report = await runExperiment(options, (progress) => {
          job.progress = {
            phase: progress.phase || options.mode || "tournament",
            completed: progress.completed,
            total: progress.total || progress.runs
          };
          job.updatedAt = Date.now();
        });
        job.archive = await archiveSimulationReport(job.report, {
          projectRoot,
          jobId: id
        });
        job.status = "complete";
      } catch (error) {
        job.status = "failed";
        job.error = error.message;
      }
      job.updatedAt = Date.now();
      pruneJobs();
    });
  } catch (error) {
    json(response, error instanceof RangeError ? 413 : 400, { error: error.message });
  }
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
  if (request.method === "POST" && url.pathname === "/api/simulations") {
    await startSimulation(request, response);
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
    json(response, 200, job);
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
    ? "/prototype/index.html"
    : url.pathname === "/lab"
      ? "/prototype/simulation.html"
      : url.pathname === "/docs/"
        ? "/dist/docs/index.html"
        : url.pathname.startsWith("/docs/")
          ? `/dist${url.pathname}`
        : url.pathname === "/gallery" || url.pathname === "/gallery/"
          ? "/dist/gallery.html"
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
  process.stdout.write(`M3T4 2038 prototype:      http://localhost:${port}/\n`);
  process.stdout.write(`M3T4 2038 simulation lab: http://localhost:${port}/lab\n`);
  process.stdout.write(`M3T4 2038 docs reader:    http://localhost:${port}/docs\n`);
  process.stdout.write(`M3T4 2038 content gallery: http://localhost:${port}/gallery\n`);
});
