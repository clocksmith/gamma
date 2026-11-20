// Run under the storage owner. Atomic source replacement makes a single read a coherent snapshot.
import { readFileSync, writeFileSync, mkdirSync, renameSync, openSync, fsyncSync, closeSync, readdirSync, unlinkSync } from 'node:fs';
import { join } from 'node:path';
import { WorkflowRegistry } from '../src/client/workflow-registry.js';
const [directory, destination] = process.argv.slice(2);
if (!directory || !destination) throw Error('Usage: backup-registry.js STATE_DIRECTORY BACKUP_DIRECTORY');
const registry = new WorkflowRegistry({ directory });
const bytes = readFileSync(registry.file.path);
registry.validate(JSON.parse(bytes));
mkdirSync(destination, { recursive: true, mode: 0o700 });
const name = `${new Date().toISOString().replaceAll(':', '-')}.private.json`;
const temporary = join(destination, name + '.tmp'), target = join(destination, name);
const fd = openSync(temporary, 'wx', 0o600);
try { writeFileSync(fd, bytes); fsyncSync(fd); } finally { closeSync(fd); }
renameSync(temporary, target);
const dir = openSync(destination, 'r'); try { fsyncSync(dir); } finally { closeSync(dir); }
// This directory is dedicated to generated backups, never the authoritative store.
for (const old of readdirSync(destination).filter(n => /^\d{4}-.*\.private\.json$/.test(n)).sort().slice(0, -14)) unlinkSync(join(destination, old));
console.log('Workflow registry backup verified and saved');
