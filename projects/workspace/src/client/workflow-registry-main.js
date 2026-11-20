// node .../workflow-registry-main.js /absolute/path/to/server.private.json
import { readFileSync, lstatSync } from 'node:fs';
import { privateStat } from './private-json-file.js';
import { WorkflowRegistry, registryServer } from './workflow-registry.js';

const path = process.argv[2];
if (!path) throw Error('Private server configuration path required');
privateStat(lstatSync(path));
const config = JSON.parse(readFileSync(path, 'utf8'));
if (!Number.isInteger(config.port) || config.port < 1024 || config.port > 65535) throw Error('Invalid loopback port');
const registry = new WorkflowRegistry(config);
const server = registryServer({ registry, clients: config.clients });
server.listen(config.port, '127.0.0.1', () => console.log(`Workflow registry ready on loopback:${config.port}`));
for (const signal of ['SIGTERM', 'SIGINT']) process.on(signal, () => server.close(() => process.exit(0)));
