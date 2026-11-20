// Fawn workspace differentiation — durable agent checkpoint shared by both arms.
//
// The agent records its step before and after each consequential tool call; the file is
// rewritten atomically and fsynced, so a restarted agent resumes from the same durability on
// either side of the comparison.

import { closeSync, existsSync, fsyncSync, openSync, readFileSync, renameSync, writeSync } from 'node:fs';

class Checkpoint {
  constructor(path) {
    this._path = path;
    this._state = existsSync(path) ? JSON.parse(readFileSync(path, 'utf8')) : {};
  }

  get() {
    return this._state;
  }

  update(patch) {
    this._state = { ...this._state, ...patch };
    const temporary = `${this._path}.tmp`;
    const fd = openSync(temporary, 'w');
    writeSync(fd, JSON.stringify(this._state));
    fsyncSync(fd);
    closeSync(fd);
    renameSync(temporary, this._path);
    return this._state;
  }
}

export { Checkpoint };
