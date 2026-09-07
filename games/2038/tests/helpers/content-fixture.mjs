import { cp, mkdir, mkdtemp, readFile, rm } from "node:fs/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const exec = promisify(execFile);
const sourceRoot = resolve(import.meta.dirname, "../..");

// Exercise real compilation and release gates without rewriting a working-tree
// release or borrowing historical artifacts whose sources no longer match.
export async function createContentFixture() {
  const directory = await mkdtemp(join(tmpdir(), "mandate-content-"));
  const root = resolve(directory, "games/2038");
  const dispose = () => rm(directory, {recursive: true, force: true});
  try {
    await mkdir(root, {recursive: true});
    const graph = JSON.parse(await readFile(resolve(sourceRoot, "content/graph.json"), "utf8"));
    for (const path of new Set([...graph.sourceRoots, "tasks", "lab", "docs", "physical", "package.json",
      "versions/current-release.json"])) {
      await cp(resolve(sourceRoot, path), resolve(root, path), {recursive: true});
    }
    await exec("git", ["init", "--initial-branch=main", directory]);
    await exec("git", ["-c", "user.name=Content Fixture", "-c", "user.email=fixture@example.invalid",
      "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", "Fixture identity"], {cwd: directory});
    const run = (script, ...args) => exec(process.execPath, [script, ...args], {cwd: root});
    for (const [script, ...args] of [
      ["tasks/content/compile.mjs"], ["tasks/render-docs.mjs"],
      ["tasks/render-gallery.mjs"], ["tasks/render-gallery.mjs", "--baseline"],
      ["tasks/create-game-release.mjs"]
    ]) await run(script, ...args);
    return {root, run, dispose};
  } catch (error) {
    await dispose();
    throw error;
  }
}
