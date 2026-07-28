import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { canonicalJson, sha256 } from "../versioning/game-identity.js";

export class DecisionCache {
  constructor(directory) {
    this.directory = resolve(directory);
  }

  key({ backend, model, packet, profile }) {
    return sha256(canonicalJson({ backend, model: model || null, packet, profile }));
  }

  async read(input) {
    const key = this.key(input);
    try {
      const value = JSON.parse(
        await readFile(resolve(this.directory, `${key}.json`), "utf8")
      );
      return { key, value };
    } catch (error) {
      if (error.code === "ENOENT") return { key, value: null };
      throw error;
    }
  }

  async write(key, value) {
    await mkdir(this.directory, { recursive: true });
    await writeFile(
      resolve(this.directory, `${key}.json`),
      `${JSON.stringify(value, null, 2)}\n`,
      { flag: "wx" }
    ).catch((error) => {
      if (error.code !== "EEXIST") throw error;
    });
  }
}
