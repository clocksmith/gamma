import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import test from "node:test";

const execute = promisify(execFile);
const root = new URL("../", import.meta.url);

async function startServer(port) {
  await execute(process.execPath, ["tools/render-docs.mjs"], { cwd: root });
  const child = spawn(process.execPath, ["tools/serve.mjs"], {
    cwd: root,
    env: { ...process.env, FRONTIER_PORT: String(port) },
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
