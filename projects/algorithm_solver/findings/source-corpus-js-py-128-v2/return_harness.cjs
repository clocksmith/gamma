// Only inputs and parameter shapes enter this sandbox. Expected values stay outside.
const fs = require('node:fs');
const calls = JSON.parse(fs.readFileSync('calls.json', 'utf8'));
const source = fs.readFileSync('candidate.cjs', 'utf8');
class ListNode { constructor(val = 0, next = null) { this.val = val; this.next = next; } }
class TreeNode { constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; } }
function input(value, type) {
  if (value && typeof value === 'object' && '__list_node__' in value) {
    value = value.__list_node__;
    let head = null;
    for (const val of [...(value || [])].reverse()) head = new ListNode(val, head);
    return head;
  }
  if (value && typeof value === 'object' && '__tree_node__' in value) {
    value = value.__tree_node__;
    if (!value?.length || value[0] === null) return null;
    const root = new TreeNode(value[0]), queue = [root];
    let i = 1;
    for (let n = 0; n < queue.length && i < value.length; n++) {
      for (const field of ['left', 'right']) {
        const val = value[i++];
        if (val != null) { queue[n][field] = new TreeNode(val); queue.push(queue[n][field]); }
      }
    }
    return root;
  }
  if (Array.isArray(value)) return value.map(item => input(item, ''));
  return value;
}
function output(value, ancestors = new Set()) {
  if (value instanceof ListNode) {
    const result = [], seen = new Set();
    while (value) {
      if (seen.has(value)) throw Error('Cycle in returned list');
      seen.add(value); result.push(output(value.val, ancestors)); value = value.next;
    }
    return {__list_node__: result};
  }
  if (value instanceof TreeNode) {
    const result = [], queue = [value], seen = new Set();
    for (let i = 0; i < queue.length; i++) {
      const node = queue[i];
      if (!node) { result.push(null); continue; }
      if (seen.has(node)) throw Error('Cycle in returned tree');
      seen.add(node); result.push(output(node.val, ancestors)); queue.push(node.left, node.right);
    }
    while (result.at(-1) === null) result.pop();
    return {__tree_node__: result};
  }
  if (value === undefined || value === null) return null;
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw Error('Non-finite result');
    return value;
  }
  if (typeof value === 'string' || typeof value === 'boolean') return value;
  if (typeof value !== 'object' || (!Array.isArray(value) && Object.getPrototypeOf(value) !== Object.prototype && Object.getPrototypeOf(value) !== null)) throw Error('Unsupported result type');
  if (ancestors.has(value)) throw Error('Cycle in result');
  ancestors.add(value);
  try {
    if (Array.isArray(value)) return value.map(item => output(item, ancestors));
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, output(item, ancestors)]));
  } finally { ancestors.delete(value); }
}
const emit = record => process.stdout.write(JSON.stringify(record) + '\n');
try {
  // Candidate console output goes to stderr, outside the judge result protocol.
  const quietConsole = { log: (...args) => process.stderr.write(args.join(' ') + '\n') };
  for (let i = 0; i < calls.calls.length; i++) {
    try {
      const fn = new Function('ListNode', 'TreeNode', 'console', source + `\n;return ${calls.method};`)(ListNode, TreeNode, quietConsole);
      if (typeof fn !== 'function') throw Error('Expected a named function');
      const args = calls.calls[i].args.map((value, n) => input(value, calls.params[n]?.[1] || ''));
      const result = fn(...args);
      if (result && typeof result.then === 'function') throw Error('Async solutions are not supported');
      emit({ i, result: output(result), args_after: calls.calls[i].capture_args ? args.map(value => output(value)) : [] });
    } catch (e) { emit({ i, error: e.name, detail: String(e.message).slice(0,500) }); }
  }
  emit({done:calls.calls.length});
} catch(e) { emit({load_error:String(e)}); process.exitCode = 1; }
