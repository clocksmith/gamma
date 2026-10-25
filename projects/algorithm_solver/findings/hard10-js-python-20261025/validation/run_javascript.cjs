'use strict';
// Input-only local worker. It receives no expected outputs or test-oracle code.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const problemId = Number(process.argv[2]);
const assignment = JSON.parse(fs.readFileSync(path.join(root, 'assignment.json'), 'utf8'));
const problem = assignment.problems.find(item => item.id === problemId);
const implementation = require(path.join(root, 'javascript', `${String(problemId).padStart(4, '0')}.js`));
const functions = { solve: implementation.solve, native: implementation[problem.native] };

function containers(value) {
  if (!Array.isArray(value)) {
    return [];
  }
  return [value, ...value.flatMap(containers)];
}

const input = fs.readFileSync(0, 'utf8').trim();
if (input.length > 0) {
  for (const line of input.split('\n')) {
    const request = JSON.parse(line);
    const results = {};
    for (const [name, implementationFunction] of Object.entries(functions)) {
      const args = structuredClone(request.args);
      const before = JSON.stringify(args);
      const references = containers(args);
      const start = process.hrtime.bigint();
      try {
        const value = implementationFunction(...args);
        const afterReferences = containers(args);
        results[name] = {
          ok: true,
          value,
          type: typeof value,
          safe_integer: typeof value === 'number' ? Number.isSafeInteger(value) : null,
          input_changed: JSON.stringify(args) !== before,
          container_identity_changed: references.length !== afterReferences.length ||
            references.some((reference, index) => reference !== afterReferences[index]),
          elapsed_ns: Number(process.hrtime.bigint() - start)
        };
      } catch (error) {
        results[name] = {
          ok: false,
          error: `${error.name}: ${error.message}`,
          elapsed_ns: Number(process.hrtime.bigint() - start)
        };
      }
    }
    process.stdout.write(`${JSON.stringify({ case_id: request.case_id, results })}\n`);
  }
}
