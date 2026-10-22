'use strict';
// Execute contract checks for every designed piece. A piece passes only through its own
// checks; layout pieces are parse-checked only and reported as such. Checks exercise the
// stated contract in a minimal context; they do not prove interchangeable semantics in
// every program. Usage: node qualify_components.cjs <pool.json> <receipt.json>
const fs = require('node:fs');
const crypto = require('node:crypto');

const [poolPath, receiptPath] = process.argv.slice(2);
if (!poolPath || !receiptPath) throw new Error('usage: qualify_components.cjs <pool.json> <receipt.json>');
if (fs.existsSync(receiptPath)) throw new Error(`refusing to overwrite ${receiptPath}`);
const poolBytes = fs.readFileSync(poolPath);
const pool = JSON.parse(poolBytes).pool;

// Run code with named bindings; returns the function's result.
const run = (code, bindings = {}) => new Function(...Object.keys(bindings), code)(...Object.values(bindings));
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const SAFE = Number.MAX_SAFE_INTEGER;

const checks = [];
function rule(test, fn) { checks.push({ test, fn }); }
const exact = text => piece => piece.text === text;
const match = re => piece => re.test(piece.text);

// Counters and accumulators.
rule(match(/^let (\w+) = 0;\n$/), p => { const n = p.text.match(/^let (\w+)/)[1]; const v = run(`${p.text}return ${n};`);
  return [['initializes to +0', Object.is(v, 0)], ['is a number', typeof v === 'number']]; });
rule(exact('let index2 = values.length - 1;\n'), p => [['last index of [1,2,3] is 2', run(`${p.text}return index2;`, { values: [1, 2, 3] }) === 2],
  ['empty array gives -1', run(`${p.text}return index2;`, { values: [] }) === -1]]);
rule(exact('const count = values.length;\n'), p => [['snapshot is not live', run(`${p.text}values.push(9);return count;`, { values: [1, 2] }) === 2]]);
for (const [re, delta] of [[/^(\w+) \+= 1;\n$/, 1], [/^(\w+) -= 1;\n$/, -1], [/^(\w+)\+\+;\n$/, 1], [/^(\w+)--;\n$/, -1]])
  rule(match(re), p => { const n = p.text.match(re)[1]; const step = start => run(`let ${n} = start;${p.text}return ${n};`, { start });
    return [['steps a small integer', step(5) === 5 + delta], ['exact at the safe-integer boundary', step(delta > 0 ? SAFE - 1 : -SAFE + 1) === (delta > 0 ? SAFE : -SAFE)],
      ['documented loss beyond safe integers', 2 ** 53 + 1 === 2 ** 53]]; });
rule(exact('total += value2;\n'), p => [['adds numbers', run(`let total = 2;${p.text}return total;`, { value2: 3 }) === 5],
  ['concatenates when a string is involved', run(`let total = 'a';${p.text}return total;`, { value2: 1 }) === 'a1']]);
rule(exact('maximum = Math.max(maximum, value);\n'), p => { const f = (maximum, value) => run(`${p.text}return maximum;`, { maximum, value });
  return [['keeps the larger value', f(3, 5) === 5 && f(5, 3) === 5], ['NaN propagates', Number.isNaN(f(1, NaN))], ['+0 beats -0', Object.is(f(-0, 0), 0)]]; });
rule(exact('count = Math.min(count, items.length);\n'), p => [['caps at the length', run(`let count = 5;${p.text}return count;`, { items: [1, 2] }) === 2]]);
// Collections, counting, membership, stack and copy.
rule(match(/^const (\w+) = \[\];\n$/), p => { const n = p.text.match(/^const (\w+)/)[1]; const a = run(`${p.text}return ${n};`), b = run(`${p.text}return ${n};`);
  return [['empty array', Array.isArray(a) && a.length === 0], ['fresh per execution', a !== b]]; });
rule(match(/^const (\w+) = \{\};\n$/), p => { const n = p.text.match(/^const (\w+)/)[1];
  const keys = run(`${p.text}${n}.b = 1; ${n}[2] = 1; ${n}.a = 1; ${n}[1] = 1; return Object.keys(${n});`);
  return [['plain object', Object.getPrototypeOf(run(`${p.text}return ${n};`)) === Object.prototype],
    ['integer-like keys ascend, then insertion order', same(keys, ['1', '2', 'b', 'a'])]]; });
rule(exact('counts[value] = (counts[value] || 0) + 1;\n'), p => { const counts = {}; const alias = counts;
  for (const value of [1, '1', 'x']) run(p.text, { counts, value });
  return [['string-coerced keys count together', counts['1'] === 2 && counts.x === 1], ['alias observes the update', alias === counts && alias['1'] === 2],
    ['missing entry counts as zero', run(`${p.text}return counts.k;`, { counts: {}, value: 'k' }) === 1]]; });
rule(exact('items[value] = true;\n'), p => { const items = {}; run(p.text, { items, value: 3 });
  return [['marks string-coerced membership', items['3'] === true], ['mutates in place', Object.keys(items).length === 1]]; });
rule(exact('items.pop();\n'), p => { const items = [1, 2, 3]; const alias = items; run(p.text, { items });
  return [['removes the last element', same(items, [1, 2])], ['alias observes removal', alias.length === 2]]; });
rule(exact('const items2 = values3.slice();\n'), p => { const inner = { k: 1 }; const values3 = [inner, 2]; const copy = run(`${p.text}return items2;`, { values3 });
  return [['new array', copy !== values3], ['equal contents', same(copy, values3)], ['shallow: elements shared', copy[0] === inner]]; });
rule(exact('const value3 = value + Math.floor((value2 - value) / 2);\n'), p => {
  const pairs = [[0, 0], [0, 1], [0, 9], [3, 8], [-5, -2], [-3, 4], [0, SAFE - 1]];
  const mid = (value, value2) => run(`${p.text}return value3;`, { value, value2 });
  return [['midpoint within [low, high]', pairs.every(([a, b]) => mid(a, b) >= a && mid(a, b) <= b)],
    ['equals floor((low+high)/2) for small integers', pairs.slice(0, 6).every(([a, b]) => mid(a, b) === Math.floor((a + b) / 2))],
    ['no overflow near the safe limit', mid(0, SAFE - 1) === Math.floor((SAFE - 1) / 2)]]; });
// Loops and control.
rule(match(/^for \(const (\w+) of (\w+)\) \{\n$/), p => { const [, v, arr] = p.text.match(/^for \(const (\w+) of (\w+)\)/);
  const order = run(`const out = [];${p.text}out.push(${v});}\nreturn out;`, { [arr]: [3, 1, 2] });
  const grown = run(`let n = 0;${p.text}n += 1; if (${arr}.length < 4) ${arr}.push(0);}\nreturn n;`, { [arr]: [1, 2] });
  return [['index order', same(order, [3, 1, 2])], ['appending during iteration extends it', grown === 4]]; });
rule(match(/^for \(let (\w+) = ([01]); \1 < (values\.length|count); \1 \+= 1\) \{\n$/), p => {
  const [, i, from, bound] = p.text.match(/^for \(let (\w+) = ([01]); \1 < (values\.length|count);/);
  const visit = (values, count) => run(`const out = [];${p.text}out.push(${i});}\nreturn out;`, { values, count });
  const checks = [['ascending visits', same(visit([7, 8, 9], 3), from === '0' ? [0, 1, 2] : [1, 2])]];
  if (bound === 'values.length') checks.push(['bound re-read each iteration', same(run(`const out = [];${p.text}out.push(${i}); values.pop();}\nreturn out;`, { values: [1, 2, 3, 4], count: 0 }), from === '0' ? [0, 1] : [1, 2])]);
  return checks; });
rule(match(/^while \((index|index \+ 1) (<|<=) index2\) \{\n$/), p => { const steps = (index, index2) => run(`let n = 0;${p.text}index += 1; n += 1;}\nreturn n;`, { index, index2 });
  const expect = p.text.startsWith('while (index + 1') ? 2 : p.text.includes('<=') ? 4 : 3;
  return [['terminates after the expected iterations from (0, 3)', steps(0, 3) === expect], ['no iterations when already met', steps(5, 1) === 0]]; });
rule(exact('break;\n'), p => [['leaves the innermost loop', run(`let n = 0; for (let i = 0; i < 9; i += 1) { n += 1; if (i === 2) {${p.text}} } return n;`) === 3]]);
rule(exact('continue;\n'), p => [['skips to the next iteration', run(`let n = 0; for (let i = 0; i < 4; i += 1) { if (i % 2) {${p.text}} n += 1; } return n;`) === 2]]);
// Guards and returns.
rule(match(/^if \(\w+\.length (===|!==) (0|other\.length)\) \{\n$/), p => { const t = (values, other) => run(`${p.text}return true;}\nreturn false;`, { values, other });
  if (p.text === 'if (values.length === 0) {\n') return [['empty is true', t([], []) === true], ['non-empty is false', t([1], []) === false]];
  if (p.text === 'if (other.length === 0) {\n') return [['empty is true', t([1], []) === true], ['non-empty is false', t([], [1]) === false]];
  return [['different lengths true', t([1], [1, 2]) === true], ['equal lengths false', t([1], [2]) === false]]; });
rule(match(/^return [A-Za-z_]\w*;\n$/), p => { const n = p.text.match(/^return (\w+);/)[1]; const ref = [1];
  if (['true', 'false'].includes(n)) return [['returns the boolean literal', run(p.text) === (n === 'true')]];
  return [['returns the referenced value itself', run(p.text, { [n]: ref }) === ref]]; });
rule(match(/^return -?\d+;\n$/), p => [['returns the number literal', run(p.text) === Number(p.text.match(/-?\d+/)[0])]]);
rule(exact("return items.join('');\n"), p => [['concatenates without a separator', run(p.text, { items: ['a', 1, 'b'] }) === 'a1b']]);
// Function headers and block syntax.
rule(match(/^function (\w+)\(([^)]*)\) \{\n$/), p => { const [, name, params] = p.text.match(/^function (\w+)\(([^)]*)\)/); const first = params.split(',')[0].trim();
  const arr = [1]; const fn = run(`${p.text}return ${first};}\nreturn ${name};`);
  return [['declares the named function', typeof fn === 'function' && fn.name === name], ['arity matches', fn.length === params.split(',').length],
    ['parameters alias caller arrays', fn(arr) === arr]]; });
rule(exact('}\n'), p => [['closes a block', run(`if (true) { var x = 1;${p.text}return x;`) === 1]]);
rule(exact('} else {\n'), p => [['else runs when the condition fails', run(`if (false) { return 1;${p.text}return 2; }`) === 2]]);
rule(exact('} else if ('), p => [['tested only after earlier branches fail', run(`let n = 0; if (true) { n = 1;${p.text}(n = 9)) { n = 2; } return n;`) === 1],
  ['taken when earlier branches fail', run(`if (false) { return 1;${p.text}true) { return 2; } return 3;`) === 2]]);
// Operation openers (partial units): check the callee semantics named on the card.
const callee = {
  'Math.max(': () => [['maximum', Math.max(1, 3) === 3], ['NaN propagates', Number.isNaN(Math.max(1, NaN))]],
  'Math.min(': () => [['minimum', Math.min(1, 3) === 1], ['NaN propagates', Number.isNaN(Math.min(1, NaN))]],
  'Math.floor(': () => [['toward negative infinity', Math.floor(-1.5) === -2 && Math.floor(1.5) === 1]],
  'Math.abs(': () => [['absolute value', Math.abs(-3) === 3], ['-0 becomes +0', Object.is(Math.abs(-0), 0)]],
  '.push(': () => { const a = [1]; const r = a.push(2); return [['mutates in place', same(a, [1, 2])], ['returns the new length', r === 2]]; },
  '.length': () => [['array and string length', [1, 2].length === 2 && 'abc'.length === 3]],
  "join('')": () => [['joins without a separator', ['a', 'b'].join('') === 'ab']],
  '.slice(': () => { const a = [1, 2, 3]; return [['negative indices count from the end', same(a.slice(-2), [2, 3])], ['returns a new array', a.slice() !== a]]; },
  'new Array(': () => { const a = new Array(3); return [['single integer sets length', a.length === 3], ['holes until filled', !(0 in a)]]; },
  '.fill(0)': () => { const a = [1, 2]; a.fill(0); return [['fills the existing length only', same(a, [0, 0])]]; },
  'Array.from(': () => [['from an iterable', same(Array.from('ab'), ['a', 'b'])], ['from a length', Array.from({ length: 2 }).length === 2]],
  '.charCodeAt(': () => [['UTF-16 code unit', 'a'.charCodeAt(0) === 97], ['NaN out of range', Number.isNaN('a'.charCodeAt(5))]],
  '.pop(': () => { const a = [1, 2]; return [['removes and returns the last element', a.pop() === 2 && a.length === 1]]; },
  '.join(': () => [['joins with the given separator', ['a', 'b'].join('-') === 'a-b']],
  '.fill(': () => { const a = [1, 2, 3]; a.fill(7, 1); return [['fills in place from a start index', same(a, [1, 7, 7])]]; },
  '.split(': () => [['splits a string', same('a,b'.split(','), ['a', 'b'])]],
  'new Map(': () => { const m = new Map([[NaN, 1]]); return [['SameValueZero keys find NaN', m.get(NaN) === 1]]; },
};
rule(piece => piece.unit === 'operation-opener' && piece.text in callee, p => callee[p.text]());
// Compact style: compose minimal snippets around each identifier-free unit.
rule(match(/^function solve\(([a-d,]*)\)\{$/), p => { const params = p.text.match(/\(([^)]*)\)/)[1].split(','); const arr = [1];
  const fn = run(`${p.text}return ${params[0]};}return solve;`);
  return [['declares solve', typeof fn === 'function' && fn.name === 'solve'], ['arity matches', fn.length === params.length], ['parameters alias caller arrays', fn(arr) === arr]]; });
rule(exact('}else{'), p => [['else runs when the condition fails', run(`if(false){return 1;${p.text}return 2;}`) === 2]]);
rule(exact('){'), p => [['closes a condition and opens its block', run(`if(true${p.text}return 1;}return 2;`) === 1]]);
rule(exact('if('), p => [['conditional', run(`${p.text}1>0){return 1;}return 2;`) === 1]]);
rule(exact('while('), p => [['repeats while true', run(`let n=0;${p.text}n<3){n+=1;}return n;`) === 3]]);
rule(exact('for(const '), p => [['for-of in index order', same(run(`const o=[];${p.text}x of [3,1]){o.push(x);}return o;`), [3, 1])]]);
rule(exact('for(let '), p => [['counted loop', run(`let s=0;${p.text}i=0;i<3;i+=1){s+=i;}return s;`) === 3]]);
rule(exact(' of '), p => [['for-of separator', run(`let s=0;for(const x${p.text}[1,2]){s+=x;}return s;`) === 3]]);
rule(exact('==='), p => [['no coercion', run(`return 1${p.text}'1';`) === false], ['NaN is not equal to itself', run(`return NaN${p.text}NaN;`) === false]]);
rule(exact('!=='), p => [['no coercion', run(`return 1${p.text}'1';`) === true]]);
for (const [text, start, expect] of [['=0;', 7, 0], ['+=1;', 7, 8], ['-=1;', 7, 6]])
  rule(exact(text), p => [[`a${text} applied to 7`, run(`let a=${start};a${p.text}return a;`) === expect]]);
rule(exact('=[];'), p => [['assigns a fresh empty array', Array.isArray(run(`let a${p.text}return a;`)) && run(`let a${p.text}return a;`) !== run(`let a${p.text}return a;`)]]);
rule(exact('={};'), p => [['assigns a fresh plain object', Object.getPrototypeOf(run(`let a${p.text}return a;`)) === Object.prototype]]);
for (const [text, value] of [['return false;', false], ['return true;', true], ['return 0;', 0]])
  rule(exact(text), p => [['returns the literal', Object.is(run(p.text), value)]]);
rule(exact('return '), p => [['returns the following expression', run(`${p.text}[1].length;`) === 1]]);
rule(exact('break;'), p => [['leaves the innermost loop', run(`let n=0;for(let i=0;i<9;i+=1){n+=1;if(i===2){${p.text}}}return n;`) === 3]]);
rule(exact('continue;'), p => [['skips to the next iteration', run(`let n=0;for(let i=0;i<4;i+=1){if(i%2){${p.text}}n+=1;}return n;`) === 2]]);

const results = [];
for (const p of pool) {
  if (p.kind === 'layout') {
    let parsed = true; try { new Function(`if (true) {\n${p.text}return 1;\n}`); } catch { parsed = false; }
    results.push({ id: p.id, style: p.style, text: p.text, status: parsed ? 'parse-checked-only' : 'failed', checks: [['parses inside a block', parsed]] });
    continue;
  }
  const applicable = checks.filter(c => c.test(p));
  if (applicable.length !== 1) throw new Error(`piece ${p.id} ${JSON.stringify(p.text)} has ${applicable.length} check rules`);
  let outcome;
  try { outcome = applicable[0].fn(p); } catch (error) { outcome = [[`threw ${error.message}`, false]]; }
  results.push({ id: p.id, style: p.style, text: p.text, status: outcome.every(([, ok]) => ok) ? 'passed' : 'failed', checks: outcome });
}
const summary = results.reduce((acc, r) => ({ ...acc, [r.status]: (acc[r.status] || 0) + 1 }), {});
const receipt = { schema: 'gamma.matched80.component-qualification.v1', node: process.version, platform: `${process.platform}-${process.arch}`,
  pool_sha256: crypto.createHash('sha256').update(poolBytes).digest('hex'),
  harness_sha256: crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),
  scope: 'Author-written execution checks of each contract card in a minimal context. Not proof of interchangeable semantics in every program; independent review pending.',
  summary, checks_total: results.reduce((n, r) => n + r.checks.length, 0), results };
fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 1) + '\n');
console.log(JSON.stringify({ summary, checks_total: receipt.checks_total, node: process.version }));
for (const r of results.filter(r => r.status === 'failed')) console.log('FAILED', r.id, JSON.stringify(r.text), JSON.stringify(r.checks.filter(([, ok]) => !ok)));
