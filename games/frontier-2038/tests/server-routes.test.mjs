import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import test from "node:test";

const execute = promisify(execFile);
const root = new URL("../", import.meta.url);

async function startServer(port, {
  bridgeToken = "test-bridge-token",
  bridgeOrigins = "https://gamma-web-game.web.app"
} = {}) {
  await execute(process.execPath, ["tasks/render-docs.mjs"], { cwd: root });
  const child = spawn(process.execPath, ["tasks/serve.mjs"], {
    cwd: root,
    env: {
      ...process.env,
      FRONTIER_PORT: String(port),
      FRONTIER_BRIDGE_TOKEN: bridgeToken,
      FRONTIER_BRIDGE_ORIGINS: bridgeOrigins
    },
    stdio: ["ignore", "pipe", "pipe"]
  });
  let output = "";
  const ready = new Promise((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error(`Server did not start:\n${output}`)),
      10_000
    );
    const capture = (chunk) => {
      output += chunk;
      if (output.includes(`http://localhost:${port}/`)) {
        clearTimeout(timer);
        resolve();
      }
    };
    child.stdout.on("data", capture);
    child.stderr.on("data", capture);
    child.once("exit", (code) => {
      clearTimeout(timer);
      reject(new Error(`Server exited ${code}:\n${output}`));
    });
  });
  await ready;
  return child;
}

async function readTerminalJob(request, id) {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    const response = await request(`/api/simulations/${id}`);
    const job = await response.json();
    if (job.status === "complete" || job.status === "failed") return job;
    await new Promise((resolve) => setTimeout(resolve, 25));
  }
  throw new Error(`Simulation job ${id} did not settle.`);
}

test("docs reader routes preserve their /docs/ base and serve rendered pages", async () => {
  const port = 20_000 + (process.pid % 10_000);
  const server = await startServer(port);
  const request = (path, options = {}) =>
    fetch(`http://127.0.0.1:${port}${path}`, options);

  try {
    const docsRedirect = await request("/docs", { redirect: "manual" });
    assert.equal(docsRedirect.status, 308);
    assert.equal(docsRedirect.headers.get("location"), "/docs/");

    assert.equal((await request("/docs/")).status, 200);
    assert.equal((await request("/docs/core-rules.html")).status, 200);

    const compatibility = await request("/core-rules.html", {
      redirect: "manual"
    });
    assert.equal(compatibility.status, 308);
    assert.equal(
      compatibility.headers.get("location"),
      "/docs/core-rules.html"
    );

    const design = await request("/docs/design-decisions.html").then(
      (response) => response.text()
    );
    assert.match(design, /href="core-rules\.html"/);
    assert.doesNotMatch(design, /href="core-rules\.md"/);
  } finally {
    server.kill("SIGTERM");
  }
});

test("deployed UI can pair with the token-gated localhost bridge", async () => {
  const port = 30_001 + (process.pid % 10_000);
  const bridgeToken = "exact-test-token";
  const origin = "https://gamma-web-game.web.app";
  const server = await startServer(port, { bridgeToken });
  const request = (path, options = {}) =>
    fetch(`http://127.0.0.1:${port}${path}`, options);

  try {
    const preflight = await request("/api/bridge", {
      method: "OPTIONS",
      headers: {
        origin,
        "access-control-request-method": "GET",
        "access-control-request-headers": "x-m3t4-bridge-token",
        "access-control-request-private-network": "true"
      }
    });
    assert.equal(preflight.status, 204);
    assert.equal(preflight.headers.get("access-control-allow-origin"), origin);
    assert.equal(
      preflight.headers.get("access-control-allow-private-network"),
      "true"
    );
    assert.match(
      preflight.headers.get("access-control-allow-headers"),
      /X-M3T4-Bridge-Token/i
    );

    const unpaired = await request("/api/bridge", {
      headers: { origin }
    });
    assert.equal(unpaired.status, 401);

    const wrong = await request("/api/bridge", {
      headers: {
        origin,
        "x-m3t4-bridge-token": "wrong"
      }
    });
    assert.equal(wrong.status, 401);

    const paired = await request("/api/bridge", {
      headers: {
        origin,
        "x-m3t4-bridge-token": bridgeToken
      }
    });
    assert.equal(paired.status, 200);
    assert.equal(paired.headers.get("access-control-allow-origin"), origin);
    const status = await paired.json();
    assert.equal(status.connected, true);
    assert.equal(status.maximumLlmDecisionsPerOpponent, 24);
    assert.deepEqual(status.interactiveBackends, [
      "weighted",
      "greedy",
      "claude",
      "codex",
      "hybrid-claude",
      "hybrid-codex"
    ]);

    const gameResponse = await request("/api/games", {
      method: "POST",
      headers: {
        origin,
        "content-type": "application/json",
        "x-m3t4-bridge-token": bridgeToken
      },
      body: JSON.stringify({
        playerCount: 3,
        factionId: "coalition_lab",
        seed: "remote-bridge-game",
        opponentProfileIds: ["power_broker", "trust_governor"],
        opponentBackends: ["weighted", "greedy"],
        allowLlm: false,
        maxLlmDecisions: 0
      })
    });
    assert.equal(gameResponse.status, 202);
    const game = await gameResponse.json();
    assert.deepEqual(
      game.opponents.map((opponent) => [
        opponent.profileId,
        opponent.backend,
        opponent.remainingLlmDecisions
      ]),
      [
        ["power_broker", "weighted", null],
        ["trust_governor", "greedy", null]
      ]
    );

    const excessiveLlmBudget = await request("/api/simulations", {
      method: "POST",
      headers: {
        origin,
        "content-type": "application/json",
        "x-m3t4-bridge-token": bridgeToken
      },
      body: JSON.stringify({
        allowLlm: true,
        maxLlmDecisions: 25,
        backends: ["codex"]
      })
    });
    assert.equal(excessiveLlmBudget.status, 400);
    assert.match(
      (await excessiveLlmBudget.json()).error,
      /24 LLM decisions per configured policy/
    );

    const requiredLlm = await request("/api/simulations", {
      method: "POST",
      headers: {
        origin,
        "content-type": "application/json",
        "x-m3t4-bridge-token": bridgeToken
      },
      body: JSON.stringify({
        runs: 1,
        playerCount: 3,
        sampleReplays: 0,
        allowLlm: true,
        requireLlm: true,
        maxLlmDecisions: 0,
        backends: ["codex"]
      })
    });
    assert.equal(requiredLlm.status, 202);
    const requiredLlmJob = await readTerminalJob(request, (await requiredLlm.json()).id);
    assert.equal(requiredLlmJob.status, "failed");
    assert.equal(requiredLlmJob.failure.outcome, "blocked");
    assert.match(requiredLlmJob.failure.message, /Required LLM decision failed/);

    const rejected = await request("/api/bridge", {
      headers: {
        origin: "https://example.com",
        "x-m3t4-bridge-token": bridgeToken
      }
    });
    assert.equal(rejected.status, 403);
  } finally {
    server.kill("SIGTERM");
  }
});
