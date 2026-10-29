// Author-local development runner. This is deliberately not qualification evidence.
'use strict';
const fs = require('node:fs'), assert = require('node:assert/strict');
const [source, packet] = process.argv.slice(2), rows = JSON.parse(fs.readFileSync(packet, 'utf8'));
const candidate = require(source);
const declared = process.argv[4] ? JSON.parse(process.argv[4]) : null;
const clone = value => JSON.parse(JSON.stringify(value));
function wire(value) {
  if (typeof value === 'bigint') return value >= -9007199254740991n && value <= 9007199254740991n ? Number(value) : value.toString();
  if (Array.isArray(value)) return value.map(wire);
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k,v]) => [k,wire(v)]));
  return value;
}
let maxSeconds = 0, maxRss = 0;
if (declared && rows.length) {
  const args = clone(rows[0].args);
  if (declared.kind === 'function') {
    assert.equal(typeof candidate[declared.name], 'function');
    assert.deepStrictEqual(wire(candidate[declared.name](...clone(args))), rows[0].expected);
    assert.deepStrictEqual(wire(new candidate.Solution()[declared.name](...clone(args))), rows[0].expected);
  } else {
    assert.equal(typeof candidate[declared.classname], 'function');
    const [operations, argumentsByCall] = args;
    const constructorArgs = declared.classname === 'PaginationAPI'
      ? [{getPage(page) { return page < argumentsByCall[0][0].length ? argumentsByCall[0][0][page].slice() : []; }}]
      : argumentsByCall[0];
    const instance = new candidate[declared.classname](...constructorArgs), observed = [null];
    for (let i = 1; i < operations.length; i++) observed.push(instance[operations[i]](...argumentsByCall[i]) ?? null);
    assert.deepStrictEqual(wire(observed), rows[0].expected);
  }
}
for (let i = 0; i < rows.length; i++) {
  const row = rows[i], args = clone(row.args), before = clone(args), start = process.hrtime.bigint();
  const result = candidate(...args);
  const elapsed = Number(process.hrtime.bigint()-start)/1e9;
  maxSeconds = Math.max(maxSeconds, elapsed); maxRss = Math.max(maxRss, process.memoryUsage().rss);
  try {
    assert.deepStrictEqual(wire(result),row.expected);
    assert.deepStrictEqual(args,before,'input mutation');
    assert(elapsed < 1, 'case exceeded one second');
    assert(maxRss < 1024**3, 'case exceeded one GiB RSS');
  } catch (error) {
    process.stdout.write(JSON.stringify({passed:false,case:i,args:row.args,expected:row.expected,actual:wire(result),message:error.message}));
    process.exit(1);
  }
}
process.stdout.write(JSON.stringify({passed:true,cases:rows.length,maxCaseSeconds:maxSeconds,maxRssBytes:maxRss,node:process.version,jitless:process.execArgv.includes('--jitless')}));
