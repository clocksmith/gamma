// One jitless development call. No expected result is sent to this process.
'use strict';
const fs=require('node:fs'), crypto=require('node:crypto');
const source=process.argv[2], args=JSON.parse(fs.readFileSync(0,'utf8')), candidate=require(source);
// Accept both export shapes: a callable module (module.exports = solve) and an
// object footer such as { solve, Solution, <nativeMethod> }. The pure `solve`
// entrypoint wins whenever it exists; native ABI methods are never called here.
const fn=typeof candidate?.solve==='function'?candidate.solve:candidate;
function wire(value) {
  if (typeof value==='bigint') return value>=-9007199254740991n&&value<=9007199254740991n?Number(value):{$integer:value.toString()};
  if (Array.isArray(value)) return value.map(wire);
  if (value&&typeof value==='object') return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,wire(v)]));
  return value;
}
let result=null, exception=null;
const start=process.hrtime.bigint();
try { result=fn(...args); } catch(error) { exception={type:error.name,message:error.message,trace:error.stack.slice(-1800)}; }
const elapsedSeconds=Number(process.hrtime.bigint()-start)/1e9;
process.stdout.write(JSON.stringify({result:wire(result),exception,argumentsAfter:args,elapsedSeconds,rssBytes:process.memoryUsage().rss,sourceSha256:crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex')}));
