// Additive runtime for statically validated typed-program v2/vector-v1 graphs.
// The emitter owns graph/type validation and expression, statement and loop
// charges. These helpers add only the frozen Python primitive internal charges.
// All language integers are BigInt; bounded storage indices use Number.
// No imports, source evaluation, I/O, or shared mutable resource instances.
class _twInvalid extends Error {
  constructor(message) { super(message); this.name = 'Invalid'; }
}
class _twBudgetExceeded extends _twInvalid {
  constructor(message) { super(message); this.name = 'BudgetExceeded'; }
}
function _twRequire(ok, message) {
  if (!ok) throw new _twInvalid(message);
}
const _twMaxCollection = 20000;
const _twIntegerLimit = 1n << 128n;
function _twInteger(value) {
  _twRequire(typeof value === 'bigint' && value > -_twIntegerLimit &&
    value < _twIntegerLimit, 'Expected bounded integer');
  return value;
}
function _twCount(value) {
  _twRequire(typeof value === 'bigint' ||
    (typeof value === 'number' && Number.isSafeInteger(value)), 'Invalid operation count');
  return BigInt(value);
}
class _twBudget {
  constructor(remaining = 100000) {
    this.remaining = _twCount(remaining);
    _twRequire(this.remaining > 0n, 'Invalid execution budget');
  }
  spend(amount = 1) {
    amount = _twCount(amount);
    _twRequire(amount >= 0n, 'Invalid operation count');
    this.remaining -= amount;
    if (this.remaining < 0n)
      throw new _twBudgetExceeded('Execution operation budget exhausted');
  }
}
function _twCheck(value, type) {
  if (type === 'int') _twInteger(value);
  else if (type === 'bool') _twRequire(typeof value === 'boolean', 'Expected boolean');
  else if (type === 'unit') _twRequire(value === null, 'Expected unit');
  else if (Array.isArray(type)) {
    _twRequire(Array.isArray(value) && value.length <= _twMaxCollection,
      'Expected bounded collection');
    _twRequire(type.length >= 2 && (type[0] === 'tuple' ||
      (type[0] === 'list' && type.length === 2)), 'Invalid type constructor');
    if (type[0] === 'list') {
      for (const item of value) _twCheck(item, type[1]);
    } else {
      _twRequire(value.length === type.length - 1, 'Tuple width mismatch');
      for (let i = 0; i < value.length; i++) _twCheck(value[i], type[i + 1]);
    }
  } else throw new _twInvalid('Resource values cannot cross the program boundary');
}
function _twCopy(value) {
  if (Array.isArray(value)) return value.map(_twCopy);
  _twRequire(value === null || typeof value === 'boolean' || typeof value === 'bigint',
    'Expected ordinary value');
  return value;
}
function _twArity(args, count) {
  _twRequire(Array.isArray(args) && args.length === count, 'Wrong primitive arity');
}
function _twList(value) {
  _twRequire(Array.isArray(value) && value.length <= _twMaxCollection,
    'Expected bounded collection');
  return value;
}
function _twIndex(index, length) {
  _twInteger(index);
  _twRequire(index >= 0n && index < BigInt(length), 'Field index outside tuple');
  return Number(index);
}
function _twBitLength(n) { return n === 0 ? 0 : Math.floor(Math.log2(n)) + 1; }
function _twPure(op, args, budget) {
  if (op === 'tuple') {
    _twRequire(Array.isArray(args) && args.length > 0 && args.length <= _twMaxCollection,
      'Invalid tuple');
    return args.slice();
  }
  if (op === 'empty_ints') { _twArity(args, 0); return []; }
  const binary = ['add', 'sub', 'mul', 'eq', 'lt', 'field', 'append'];
  _twArity(args, op === 'sort_by' ? 3 : binary.includes(op) ? 2 : 1);
  const a = args[0], b = args[1];
  if (op === 'add' || op === 'sub' || op === 'mul') {
    _twInteger(a); _twInteger(b);
    return _twInteger(op === 'add' ? a + b : op === 'sub' ? a - b : a * b);
  }
  if (op === 'eq' || op === 'lt') {
    _twRequire(typeof a === typeof b &&
      (typeof a === 'bigint' || typeof a === 'boolean'), 'Invalid comparison');
    if (typeof a === 'bigint') { _twInteger(a); _twInteger(b); }
    return op === 'eq' ? a === b : a < b;
  }
  if (op === 'not') { _twCheck(a, 'bool'); return !a; }
  if (op === 'neg') return _twInteger(-_twInteger(a));
  if (op === 'field') {
    const value = _twList(a)[_twIndex(b, a.length)];
    return typeof value === 'bigint' ? _twInteger(value) : value;
  }
  if (op === 'len') return BigInt(_twList(a).length);
  _twRequire(['range', 'append', 'sort_by'].includes(op), 'Unknown operation');
  const n = op === 'range' ? _twInteger(a) : BigInt(_twList(a).length + (op === 'append' ? 1 : 0));
  _twRequire(n >= 0n && n <= BigInt(_twMaxCollection), 'Collection size limit exceeded');
  const size = Number(n);
  budget.spend(op === 'sort_by' ? size * Math.max(1, _twBitLength(size)) : size);
  if (op === 'range') return Array.from({length: size}, (_, i) => BigInt(i));
  if (op === 'append') return [...a, b];
  _twCheck(args[2], 'bool');
  // Native stable sort preserves the order of equal keys in both directions,
  // as Python sorted(reverse=...) does. Never coerce BigInt differences.
  return a.slice().sort((left, right) => {
    const x = left[_twIndex(b, left.length)], y = right[_twIndex(b, right.length)];
    const order = x < y ? -1 : x > y ? 1 : 0;
    return args[2] ? -order : order;
  });
}
class _twResource {
  constructor(kind, data) { this.kind = kind; this.data = data; }
}
function _twOwned(value, kind) {
  _twRequire(value instanceof _twResource && value.kind === kind, 'Resource type mismatch');
  return value.data;
}
function _twEffect(op, args, budget) {
  const signatures = {
    'vector.new': 0, 'vector.append': 2, 'vector.snapshot': 1,
    'dsu.new': 1, 'dsu.find': 2, 'dsu.union': 3,
    'heap.new': 0, 'heap.push': 2, 'heap.pop': 1,
    'queue.new': 0, 'queue.push': 2, 'queue.pop': 1, 'queue.size': 1,
    'map.new': 0, 'map.has': 2, 'map.get': 3, 'map.set': 3
  };
  _twRequire(Object.prototype.hasOwnProperty.call(signatures, op), 'Unknown effect');
  _twArity(args, signatures[op]);
  const [kind, action] = op.split('.');
  if (action === 'new') {
    if (kind === 'dsu') {
      const n = _twInteger(args[0]);
      _twRequire(n >= 0n && n <= BigInt(_twMaxCollection), 'Invalid disjoint-set size');
      budget.spend(n);
      return new _twResource(kind, {
        parent: Array.from({length: Number(n)}, (_, i) => i), sizes: Array(Number(n)).fill(1n)
      });
    }
    return new _twResource(kind, kind === 'map' ? new Map() :
      kind === 'queue' ? {items: [], head: 0} : []);
  }
  const obj = _twOwned(args[0], kind);
  for (let i = 1; i < args.length; i++) _twInteger(args[i]);
  if (kind === 'vector') {
    if (action === 'snapshot') { budget.spend(obj.length); return obj.slice(); }
    _twRequire(obj.length < _twMaxCollection, 'Resource capacity exceeded');
    budget.spend(); obj.push(args[1]); return null;
  }
  if (kind === 'dsu') {
    const root = value => {
      _twRequire(value >= 0n && value < BigInt(obj.parent.length), 'Vertex outside disjoint sets');
      let i = Number(value);
      while (obj.parent[i] !== i) { budget.spend(); i = obj.parent[i]; }
      return i;
    };
    let x = root(args[1]);
    if (action === 'find') return BigInt(x);
    let y = root(args[2]);
    if (x === y) return false;
    if (obj.sizes[x] < obj.sizes[y]) [x, y] = [y, x];
    obj.parent[y] = x; obj.sizes[x] += obj.sizes[y]; return true;
  }
  const size = kind === 'map' ? obj.size : kind === 'queue' ? obj.items.length - obj.head : obj.length;
  if (action === 'push' || op === 'map.set')
    _twRequire(size < _twMaxCollection || (kind === 'map' && obj.has(args[1])), 'Resource capacity exceeded');
  if (kind === 'heap') {
    budget.spend(Math.max(1, _twBitLength(size)));
    if (action === 'push') {
      const value = args[1];
      let i = obj.length;
      obj.push(value);
      while (i > 0) {
        const p = Math.floor((i - 1) / 2);
        if (obj[p] <= value) break;
        obj[i] = obj[p]; i = p;
      }
      obj[i] = value; return null;
    }
    _twRequire(size > 0, 'Pop from empty heap');
    const result = obj[0], value = obj.pop();
    if (obj.length > 0) {
      let i = 0;
      while (2 * i + 1 < obj.length) {
        let child = 2 * i + 1;
        if (child + 1 < obj.length && obj[child + 1] < obj[child]) child++;
        if (value <= obj[child]) break;
        obj[i] = obj[child]; i = child;
      }
      obj[i] = value;
    }
    return result;
  }
  if (kind === 'queue') {
    if (action === 'push') { obj.items.push(args[1]); return null; }
    if (action === 'size') return BigInt(size);
    _twRequire(size > 0, 'Pop from empty queue');
    const value = obj.items[obj.head];
    obj.items[obj.head++] = null;
    if (obj.head * 2 >= obj.items.length) {
      obj.items = obj.items.slice(obj.head); obj.head = 0;
    }
    return value;
  }
  if (action === 'has') return obj.has(args[1]);
  if (action === 'get') return obj.has(args[1]) ? obj.get(args[1]) : args[2];
  obj.set(args[1], args[2]); return null;
}
