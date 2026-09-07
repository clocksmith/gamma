import { mkdir, readFile, writeFile } from "node:fs/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { dirname } from "node:path";

export async function writeImmutableArtifact(path, contents) {
  try {
    const existing = await readFile(path, "utf8");
    if (existing !== contents) {
      throw new Error(`Refusing to overwrite immutable release artifact: ${path}`);
    }
    return false;
  } catch (error) {
    if (error?.code !== "ENOENT") throw error;
  }

  await mkdir(dirname(path), { recursive: true });
  try {
    await writeFile(path, contents, { flag: "wx" });
  } catch (error) {
    if (error?.code === "EEXIST") {
      throw new Error(`Refusing to overwrite immutable release artifact: ${path}`);
    }
    throw error;
  }
  return true;
}

// Publication and kit freezing verify immutable identity; ordinary authoring
// checks can validate revised prose before a new release is declared.
export async function verifyRelease(root) {
  return promisify(execFile)(process.execPath, ["tasks/create-game-release.mjs", "--verify"], { cwd: root });
}
