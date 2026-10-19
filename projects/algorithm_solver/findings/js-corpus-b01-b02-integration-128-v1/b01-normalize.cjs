const fs = require('node:fs');
const babel = require('/usr/share/nodejs/@babel/core');
const traverse = require('/usr/share/nodejs/@babel/traverse').default;
const generate = require('/usr/share/nodejs/@babel/generator').default;
const t = require('/usr/share/nodejs/@babel/types');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const names = {"1": {"seen": "seenIndices", "i": "index"}, "3": {"left": "leftIndex", "longest": "maximumLength", "previous": "previousIndex"}, "4": {"a": "shortValues", "b": "longValues", "m": "shortLength", "n": "longLength", "low": "lowerBound", "high": "upperBound", "i": "shortPartition", "j": "longPartition", "aLeft": "shortLeftValue", "aRight": "shortRightValue", "bLeft": "longLeftValue", "bRight": "longRightValue"}, "6": {"row": "rowIndex"}, "7": {"limit": "magnitudeLimit", "result": "reversedValue"}, "8": {"limit": "magnitudeLimit", "result": "parsedValue"}, "9": {}, "10": {"m": "patternLength", "j": "patternIndex", "previous": "previousMatches", "current": "currentMatches"}, "11": {"left": "leftIndex", "right": "rightIndex", "best": "maximumArea"}, "12": {"result": "romanNumeral"}, "14": {"first": "firstCharacters", "length": "prefixLength", "i": "stringIndex", "j": "characterIndex", "current": "currentCharacters"}, "15": {"a": "leftValue", "b": "rightValue", "i": "firstIndex", "left": "leftIndex", "right": "rightIndex"}, "16": {"a": "leftValue", "b": "rightValue", "i": "firstIndex", "left": "leftIndex", "right": "rightIndex", "best": "closestSum"}, "17": {"phone": "phoneLetters", "next": "nextCombinations"}, "18": {"a": "leftValue", "b": "rightValue", "n": "valueCount", "i": "firstIndex", "j": "secondIndex", "left": "leftIndex", "right": "rightIndex"}, "19": {"dummy": "sentinelNode", "fast": "leadingNode", "slow": "precedingNode", "i": "stepIndex"}, "20": {"closing": "closingCharacters", "expected": "expectedClosers"}, "21": {"dummy": "sentinelNode", "tail": "tailNode"}, "22": {"visit": "searchParentheses", "open": "openedCount", "closed": "closedCount"}, "23": {"heap": "headHeap", "left": "leftChildIndex", "right": "rightChildIndex", "smallest": "smallestIndex", "i": "parentIndex", "dummy": "sentinelNode", "tail": "tailNode", "node": "nextNode", "last": "lastHead"}, "24": {"dummy": "sentinelNode", "prev": "previousNode", "a": "firstNode", "b": "secondNode"}, "25": {"dummy": "sentinelNode", "before": "beforeNode", "kth": "groupEndNode", "after": "afterNode", "prev": "previousNode", "cur": "currentNode", "next": "nextNode", "oldHead": "previousHead", "i": "stepIndex"}, "28": {"lps": "prefixLengths", "i": "index", "j": "prefixLength"}, "29": {"MIN": "minimumInteger", "MAX": "maximumInteger", "a": "remainingDividend", "b": "divisorMagnitude", "result": "quotient", "value": "chunkValue", "multiple": "chunkMultiplier"}, "30": {"width": "wordWidth", "needed": "neededCounts", "window": "windowCounts", "count": "matchedCount", "left": "leftIndex", "right": "rightIndex"}, "33": {"left": "leftIndex", "right": "rightIndex", "mid": "midpoint"}, "34": {"left": "leftIndex", "right": "rightIndex", "mid": "midpoint"}, "35": {"left": "leftIndex", "right": "rightIndex", "mid": "midpoint"}, "36": {"rows": "rowValues", "cols": "columnValues", "boxes": "boxValues", "r": "rowIndex", "c": "columnIndex", "v": "cellValue", "box": "boxIndex"}, "38": {"result": "sequence", "next": "nextSequence", "i": "index", "j": "runEnd", "step": "termIndex"}, "39": {"values": "candidateValues", "path": "combination", "dfs": "searchCombinations", "start": "startIndex", "remaining": "remainingSum", "i": "candidateIndex", "a": "leftValue", "b": "rightValue"}, "40": {"values": "candidateValues", "path": "combination", "dfs": "searchCombinations", "start": "startIndex", "remaining": "remainingSum", "i": "candidateIndex", "a": "leftValue", "b": "rightValue"}, "41": {"n": "arrayLength", "i": "index", "j": "destinationIndex"}, "42": {"left": "leftIndex", "right": "rightIndex", "leftMax": "leftMaximum", "rightMax": "rightMaximum", "water": "trappedWater"}, "43": {"m": "firstLength", "n": "secondLength", "i": "firstIndex", "j": "secondIndex", "digits": "productDigits", "sum": "digitSum"}, "44": {"i": "stringIndex", "j": "patternIndex", "star": "starIndex", "matched": "starMatchEnd"}, "45": {"jumps": "jumpCount", "end": "currentReach", "farthest": "furthestReach", "i": "index"}, "50": {}, "51": {"cols": "usedColumns", "diag1": "descendingDiagonals", "diag2": "ascendingDiagonals", "row": "rowIndex", "col": "columnIndex", "dfs": "searchBoards"}, "52": {"cols": "usedColumns", "diag1": "descendingDiagonals", "diag2": "ascendingDiagonals", "row": "rowIndex", "col": "columnIndex", "dfs": "countBoards"}};
const ast = babel.parseSync(input.source, {sourceType:'script',babelrc:false,configFile:false});
let entry;
const bindings = new Set();
traverse(ast, {Scope(path) {for (const binding of Object.values(path.scope.bindings)) bindings.add(binding);}, FunctionDeclaration(path) {if (path.node.id.name === input.method) entry = path;}});
if (!entry || JSON.stringify(entry.node.params.map(p=>p.name)) !== JSON.stringify(input.params)) throw Error('Public signature mismatch');
const fixed = new Set([entry.scope.getBinding(input.method), ...input.params.map(p=>entry.scope.getBinding(p))]);
const renames = [...bindings].filter(b=>!fixed.has(b)).sort((a,b)=>a.identifier.start-b.identifier.start).map((binding,index)=>{
  const old = binding.identifier.name;
  let name = names[input.id][old] || old;
  if (input.id === 72 && old === 'i' && binding.kind === 'param') name = 'columnIndex';
  return {binding,old,name,temp:`__B01temporary${index}`,start:binding.identifier.start};
});
const identifiers = new Set();
traverse(ast,{Identifier(path){identifiers.add(path.node.name);}});
for (const r of renames) if (identifiers.has(r.temp)) throw Error('Temporary collision');
// Distinct bound identifiers are renamed through fresh names. Afterward verify
// every reference still resolves to the same Babel binding, catching capture.
const references = renames.flatMap(r=>r.binding.referencePaths.map(path=>({path,binding:r.binding})));
for (const r of renames) r.binding.scope.rename(r.old,r.temp);
for (const r of renames) r.binding.scope.rename(r.temp,r.name);
for (const {path,binding} of references) if (path.scope.getBinding(path.node.name) !== binding) throw Error('Binding capture');
let blocks = 0;
function block(node) {
  if (t.isBlockStatement(node)) return node;
  if (t.isFunctionDeclaration(node) || t.isVariableDeclaration(node) && node.kind !== 'var') throw Error('Unsafe block conversion');
  blocks++;
  return t.blockStatement([node]);
}
traverse(ast,{Loop(path){path.node.body=block(path.node.body);},IfStatement(path){path.node.consequent=block(path.node.consequent);if(path.node.alternate&&!t.isIfStatement(path.node.alternate))path.node.alternate=block(path.node.alternate);}});
if (entry.node.id.name !== input.method || JSON.stringify(entry.node.params.map(p=>p.name)) !== JSON.stringify(input.params)) throw Error('Signature changed');
const source = generate(ast,{comments:true,compact:false}).code+'\n';
process.stdout.write(JSON.stringify({source,tools:{babel:babel.version},entry:input.method,params:input.params,renames:renames.map(({old,name,start})=>({old,name,start})),explicit_blocks_added:blocks}));
