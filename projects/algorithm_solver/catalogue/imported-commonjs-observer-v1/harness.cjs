'use strict';
// Source-interface successor only. Native CommonJS loading and every candidate
// call occur inside the existing sandbox. Expected values never enter it.
// The original typed/effect observer remains the transport implementation.
const fs = require('fs');
const {decode, encode, aliases} = require('./observer.cjs');
const apply = Reflect.apply;

function main() {
  const packet = JSON.parse(fs.readFileSync('inputs.json'));
  if (packet.entry !== 'solve') throw Error('CommonJS object interface requires solve');
  const exported = require('./program.js');
  if (exported === null || typeof exported !== 'object' ||
      !Object.hasOwn(exported, 'solve') || typeof exported.solve !== 'function') {
    throw Error('CommonJS object interface requires an own callable solve export');
  }
  for (let i = 0; i < packet.calls.length; i++) {
    const args = decode(packet.calls[i].args);
    let record;
    try {
      const before = encode(args);
      // Preserve the receiver used by the existing request-batch runner.
      const result = apply(exported.solve, exported, args);
      record = {i, result: encode(result), result_type: typeof result,
                args_before: before, args_after: encode(args), alias_edges: aliases(args, result)};
    } catch (error) {
      record = {i, error: String(error)};
    }
    process.stdout.write(JSON.stringify(record) + '\n');
  }
  process.stdout.write(JSON.stringify({done: packet.calls.length}) + '\n');
}
if (require.main === module) main();
