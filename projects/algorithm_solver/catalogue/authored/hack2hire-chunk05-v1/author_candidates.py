"""Original candidate authoring, after the recorded reference freeze. No judging."""
from pathlib import Path
import hashlib
import json
import textwrap
from prepare_reference import FUNCTIONS, CLASSES

HERE = Path(__file__).resolve().parent

PYTHON = {
'passwords': '''
def countDistinctPasswords(password):
    seen = 0
    counts = {}
    result = 1
    for ch in password:
        result += seen - counts.get(ch, 0)
        counts[ch] = counts.get(ch, 0) + 1
        seen += 1
    return result
''',
'coverage': '''
def countFullyCoveredClusters(availability, users):
    if not users:
        return 0
    rows, cols = len(users), len(users[0])
    visited = set()
    result = 0
    for r in range(rows):
        for c in range(cols):
            if not users[r][c] or (r, c) in visited:
                continue
            queue = [(r, c)]
            visited.add((r, c))
            covered = True
            head = 0
            while head < len(queue):
                x, y = queue[head]
                head += 1
                covered = covered and bool(availability[x][y])
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b = x + dx, y + dy
                    if 0 <= a < rows and 0 <= b < cols and users[a][b] and (a, b) not in visited:
                        visited.add((a, b))
                        queue.append((a, b))
            result += covered
    return result
''',
'squares': '''
def countGridSquares(queries):
    result = []
    for rows, cols in queries:
        m = min(rows, cols)
        result.append(m * (rows + 1) * (cols + 1) - (rows + cols + 2) * m * (m + 1) // 2 + m * (m + 1) * (2 * m + 1) // 6)
    return result
''',
'ratings': '''
from math import gcd
from functools import cmp_to_key

class CustomerSupportSystem:
    def __init__(self):
        self.all = {}
        self.months = {}

    def record(self, agentId, score, month):
        for target in (self.all, self.months.setdefault(month, {})):
            total, count = target.get(agentId, (0, 0))
            target[agentId] = (total + score, count + 1)

    def rank(self, month):
        rows = self.all if month is None else self.months.get(month, {})
        def compare(a, b):
            x, nx = rows[a]
            y, ny = rows[b]
            difference = x * ny - y * nx
            return -1 if difference > 0 else 1 if difference < 0 else (a > b) - (a < b)
        result = []
        for agent in sorted(rows, key=cmp_to_key(compare)):
            total, count = rows[agent]
            divisor = gcd(total, count)
            result.append([agent, total // divisor, count // divisor])
        return result
''',
'date': '''
from itertools import permutations

def isValidDate(a, b, c):
    for year, month, day in permutations((a, b, c)):
        if not (1 <= year <= 9999 and 1 <= month <= 12 and day >= 1):
            continue
        leap = year % 400 == 0 or year % 4 == 0 and year % 100 != 0
        lengths = (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
        if day <= lengths[month - 1]:
            return True
    return False
''',
'decode': '''
def decodePassword(text):
    x, y = (int(v.strip()) for v in text[0].strip()[1:-1].split(','))
    return text[y + 1][x]
''',
'access': '''
from bisect import bisect_right

class AccessSystem:
    def __init__(self, parents):
        children = {name: [] for name in parents}
        root = None
        for name, parent in parents.items():
            if parent is None:
                root = name
            else:
                children[parent].append(name)
        self.bounds = {}
        counter = 0
        stack = [(root, False)]
        while stack:
            name, leaving = stack.pop()
            if leaving:
                self.bounds[name][1] = counter
            else:
                self.bounds[name] = [counter, None]
                counter += 1
                stack.append((name, True))
                for child in reversed(children[name]):
                    stack.append((child, False))
        self.allowed = {}

    def grant(self, advertiser, region):
        intervals = sorted(self.allowed.get(advertiser, []) + [tuple(self.bounds[region])])
        merged = []
        for left, right in intervals:
            if merged and left <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], right))
            else:
                merged.append((left, right))
        self.allowed[advertiser] = merged

    def revoke(self, advertiser, region):
        low, high = self.bounds[region]
        result = []
        for left, right in self.allowed.get(advertiser, []):
            if right <= low or high <= left:
                result.append((left, right))
            else:
                if left < low:
                    result.append((left, low))
                if high < right:
                    result.append((high, right))
        self.allowed[advertiser] = result

    def canAccess(self, advertiser, region):
        position = self.bounds[region][0]
        intervals = self.allowed.get(advertiser, [])
        index = bisect_right(intervals, (position, float('inf'))) - 1
        return index >= 0 and position < intervals[index][1]
''',
'cluster': '''
from collections import deque

def clusterSummary(parents):
    n = len(parents)
    if not n:
        return {'count': 0, 'topology': ''}
    children = [[] for _ in parents]
    root = parents.index(-1)
    for node, parent in enumerate(parents):
        if parent >= 0:
            children[parent].append(node)
    pending = [len(row) for row in children]
    queue = deque(i for i in range(n) if not pending[i])
    counts = [1] * n
    topology = [''] * n
    while queue:
        node = queue.popleft()
        topology[node] = str(node) + ('(' + ','.join(topology[c] for c in children[node]) + ')' if children[node] else '')
        parent = parents[node]
        if parent >= 0:
            counts[parent] += counts[node]
            pending[parent] -= 1
            if pending[parent] == 0:
                queue.append(parent)
    return {'count': counts[root], 'topology': topology[root]}
''',
'orders': '''
class CryptoOrderManager:
    def __init__(self):
        self.orders = {}

    def apply(self, message):
        parts = [v.strip() for v in message.split(',')]
        if len(parts) != 5:
            return False
        oid, side, symbol, raw, event = parts
        if not raw.isascii() or not raw.isdecimal() or event not in ('NEW', 'FILLED'):
            return False
        quantity = int(raw)
        if quantity <= 0:
            return False
        row = self.orders.get(oid)
        if event == 'NEW':
            if row is not None:
                return (row['operation'], row['symbol'], row['total']) == (side, symbol, quantity)
            self.orders[oid] = {'id': oid, 'operation': side, 'symbol': symbol, 'total': quantity, 'filled': 0, 'remaining': quantity}
            return True
        if row is None or row['operation'] != side or row['symbol'] != symbol or quantity > row['remaining']:
            return False
        row['filled'] += quantity
        row['remaining'] -= quantity
        return True

    def status(self, orderId):
        row = self.orders.get(orderId)
        return dict(row) if row is not None else None
''',
'crypto': '''
class CryptoTradingSystem:
    def __init__(self):
        self.orders = {}

    def place(self, id, currency, amount, timestamp, type):
        if id in self.orders:
            return False
        self.orders[id] = {'id': id, 'currency': currency, 'amount': amount, 'timestamp': timestamp, 'type': type, 'state': 'live'}
        return True

    def _transition(self, id, allowed, target):
        row = self.orders.get(id)
        if row is None or row['state'] not in allowed:
            return False
        row['state'] = target
        return True

    def pause(self, id):
        return self._transition(id, ('live',), 'paused')

    def resume(self, id):
        return self._transition(id, ('paused',), 'live')

    def cancel(self, id):
        return self._transition(id, ('live', 'paused'), 'canceled')

    def complete(self, id):
        return self._transition(id, ('live',), 'completed')

    def listLive(self, currency):
        return [dict(row) for row in sorted(self.orders.values(), key=lambda r: (r['timestamp'], r['id'])) if row['state'] == 'live' and (currency is None or row['currency'] == currency)]
''',
'ip': '''
class IPRangeIterator:
    def __init__(self, start):
        self.current = 0
        for part in start.split('.'):
            self.current = self.current * 256 + int(part)

    def hasNext(self):
        return self.current < 4294967296

    def next(self):
        if not self.hasNext():
            return None
        number = self.current
        self.current += 1
        octets = []
        for _ in range(4):
            octets.append(str(number % 256))
            number //= 256
        return '.'.join(reversed(octets))

    def __iter__(self):
        return self

    def __next__(self):
        value = self.next()
        if value is None:
            raise StopIteration
        return value
''',
'meeting': '''
from bisect import bisect_left

class MeetingScheduler:
    def __init__(self, rooms):
        self.rooms = list(rooms)
        self.bookings = {room: [] for room in rooms}

    def book(self, start, end):
        for room in self.rooms:
            rows = self.bookings[room]
            index = bisect_left(rows, (start,))
            if index and rows[index - 1][1] > start:
                continue
            if index < len(rows) and rows[index][0] < end:
                continue
            rows.insert(index, (start, end))
            return room
        return None

    def schedule(self, room):
        return [list(row) for row in self.bookings[room]]
''',
'pagination': '''
class PaginationAPI:
    def __init__(self, external):
        self.external = external
        self.buffer = []
        self.offset = 0
        self.page = 0
        self.calls = 0
        self.eof = False

    def read(self, count):
        result = []
        while len(result) < count:
            if self.offset < len(self.buffer):
                result.append(self.buffer[self.offset])
                self.offset += 1
            elif self.eof:
                break
            else:
                self.buffer = list(self.external.getPage(self.page))
                self.page += 1
                self.calls += 1
                self.offset = 0
                if not self.buffer:
                    self.eof = True
        return result

    def fetchCount(self):
        return self.calls

class _ExternalPageFixture:
    def __init__(self, pages):
        self.pages = [list(page) for page in pages]

    def getPage(self, page):
        return list(self.pages[page]) if page < len(self.pages) else []
''',
'path': '''
class PathKeyValueStore:
    def __init__(self):
        self.values = {'/': 'root'}
        self.children = {'/': 0}

    def create(self, path, value):
        parent = path.rsplit('/', 1)[0] or '/'
        if path in self.values or parent not in self.values:
            return False
        self.values[path] = value
        self.children[path] = 0
        self.children[parent] += 1
        return True

    def set(self, path, value):
        if path == '/' or path not in self.values:
            return False
        self.values[path] = value
        return True

    def get(self, path):
        return self.values.get(path)

    def delete(self, path):
        if path == '/' or path not in self.values or self.children[path]:
            return False
        parent = path.rsplit('/', 1)[0] or '/'
        self.children[parent] -= 1
        del self.values[path]
        del self.children[path]
        return True
''',
'radix': '''
def _node():
    return {'edges': {}, 'terminal': False, 'value': None}

class RadixCache:
    def __init__(self):
        self.root = _node()

    def insert(self, sequence, value):
        key = list(sequence)
        node, position = self.root, 0
        while position < len(key):
            edge = node['edges'].get(key[position])
            if edge is None:
                leaf = _node()
                leaf.update(terminal=True, value=value)
                node['edges'][key[position]] = (key[position:], leaf)
                return
            label, child = edge
            common = 0
            while common < len(label) and position + common < len(key) and label[common] == key[position + common]:
                common += 1
            if common == len(label):
                node = child
                position += common
                continue
            middle = _node()
            middle['edges'][label[common]] = (label[common:], child)
            node['edges'][label[0]] = (label[:common], middle)
            position += common
            if position == len(key):
                middle.update(terminal=True, value=value)
            else:
                leaf = _node()
                leaf.update(terminal=True, value=value)
                middle['edges'][key[position]] = (key[position:], leaf)
            return
        node.update(terminal=True, value=value)

    def get(self, sequence):
        node, position = self.root, 0
        while position < len(sequence):
            edge = node['edges'].get(sequence[position])
            if edge is None:
                return None
            label, child = edge
            if list(sequence[position:position + len(label)]) != label:
                return None
            position += len(label)
            node = child
        return node['value'] if node['terminal'] else None
''',
'rate': '''
from collections import deque

class RateLimiter:
    def __init__(self, rules):
        self.rules = [(limit, window, deque()) for limit, window in rules]

    def allow(self, timestamp):
        allowed = True
        for limit, window, queue in self.rules:
            while queue and queue[0] <= timestamp - window:
                queue.popleft()
            if len(queue) >= limit:
                allowed = False
        if allowed:
            for limit, window, queue in self.rules:
                queue.append(timestamp)
        return allowed
''',
'retry': '''
from copy import deepcopy

def retry(function, maxAttempts, initialDelay=0, multiplier=1, onDelay=None):
    if maxAttempts < 1:
        raise ValueError('maxAttempts must be positive')
    delay = initialDelay
    for attempt in range(maxAttempts):
        try:
            return function()
        except Exception:
            if attempt + 1 == maxAttempts:
                raise
        if onDelay is not None:
            onDelay(delay)
        delay *= multiplier

def retryOperation(outcomes, maxAttempts, initialDelay, multiplier):
    count = 0
    delays = []
    def operation():
        nonlocal count
        entry = outcomes[count] if count < len(outcomes) else {'error': 'exhausted'}
        count += 1
        if 'ok' in entry:
            return deepcopy(entry['ok'])
        raise RuntimeError(entry['error'])
    try:
        value = retry(operation, maxAttempts, initialDelay, multiplier, delays.append)
        return {'value': value, 'error': None, 'attempts': count, 'delays': delays}
    except RuntimeError as error:
        return {'value': None, 'error': str(error), 'attempts': count, 'delays': delays}
''',
'trading': '''
from heapq import heappush, heappop

class TradingSystem:
    def __init__(self):
        self.items = {}
        self.sequence = 0

    def addListing(self, seller, item, price):
        heappush(self.items.setdefault(item, []), (price, self.sequence, seller))
        self.sequence += 1

    def buy(self, item, budget):
        queue = self.items.get(item, [])
        if not queue or queue[0][0] > budget:
            return None
        price, sequence, seller = heappop(queue)
        return [seller, price]
''',
'goodness': '''
def distinctGoodnessValues(arr):
    tails = {0: -1}
    for value in arr:
        for mask, last in list(tails.items()):
            if last < value:
                combined = mask | value
                if combined not in tails or value < tails[combined]:
                    tails[combined] = value
    return sorted(tails)
''',
'products': '''
def distinctPrimeProducts(primes):
    products = {1}
    for prime in primes:
        products.update([value * prime for value in products])
    products.discard(1)
    return sorted(products)
''',
'cars': '''
from collections import deque

def dualCarDestinations(grid):
    rows, cols = len(grid), len(grid[0])
    positions = {}
    neighbors = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == '#':
                continue
            cell = r * cols + c
            if value in 'abAB':
                positions[value] = cell
            neighbors[cell] = []
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = r + dx, c + dy
                if 0 <= a < rows and 0 <= b < cols and grid[a][b] != '#':
                    neighbors[cell].append(a * cols + b)
    start = (positions['a'], positions['b'])
    target = (positions['A'], positions['B'])
    seen = {start}
    queue = deque([(start[0], start[1], 0)])
    while queue:
        a, b, distance = queue.popleft()
        if (a, b) == target:
            return distance
        for x in neighbors[a]:
            for y in neighbors[b]:
                if x == y or x == b and y == a or (x, y) in seen:
                    continue
                seen.add((x, y))
                queue.append((x, y, distance + 1))
    return -1
''',
'lru': '''
from collections import OrderedDict
from copy import deepcopy

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.values = OrderedDict()

    def _evict(self):
        while len(self.values) > self.capacity:
            self.values.popitem(last=False)

    def get(self, key):
        if key not in self.values:
            return -1
        self.values.move_to_end(key)
        return deepcopy(self.values[key])

    def put(self, key, value):
        self.values[key] = deepcopy(value)
        self.values.move_to_end(key)
        self._evict()

    def resize(self, capacity):
        self.capacity = capacity
        self._evict()
''',
'earliest': '''
def earliestReachableTime(startX, startY, targetX, targetY, directions):
    dx, dy = targetX - startX, targetY - startY
    if dx == dy == 0:
        return 0
    for time, direction in enumerate(directions, 1):
        if direction == 'E' and dx > 0:
            dx -= 1
        elif direction == 'W' and dx < 0:
            dx += 1
        elif direction == 'N' and dy > 0:
            dy -= 1
        elif direction == 'S' and dy < 0:
            dy += 1
        if dx == dy == 0:
            return time
    return -1
''',
'adjacent': '''
def eliminateAdjacentDuplicates(text):
    previous, run, changes = None, 0, 0
    for char in text:
        if char == previous:
            run += 1
        else:
            previous, run = char, 1
        if run % 2 == 0:
            changes += 1
    return changes
''',
'referrals': '''
from collections import deque

def referralLeaderboard(referrers, referrals):
    parent = dict(zip(referrals, referrers))
    nodes = set(referrers) | set(referrals)
    pending = {node: 0 for node in nodes}
    totals = {node: 0 for node in nodes}
    for source in referrers:
        pending[source] += 1
    queue = deque(node for node in nodes if pending[node] == 0)
    while queue:
        node = queue.popleft()
        if node not in parent:
            continue
        target = parent[node]
        totals[target] += 1 + totals[node]
        pending[target] -= 1
        if pending[target] == 0:
            queue.append(target)
    ranked = sorted(set(referrers), key=lambda name: (-totals[name], name))[:3]
    return [[name, totals[name]] for name in ranked]
''',
'timeline': '''
from collections import defaultdict

def shiftTimeline(schedules):
    order = list(dict.fromkeys(row[0] for row in schedules))
    events = defaultdict(lambda: defaultdict(int))
    for name, start, end in schedules:
        events[start][name] += 1
        events[end][name] -= 1
    times = sorted(events)
    counts = defaultdict(int)
    result = []
    for i, start in enumerate(times[:-1]):
        for name, delta in events[start].items():
            counts[name] += delta
        working = [name for name in order if counts[name] > 0]
        if not working:
            continue
        end = times[i + 1]
        if result and result[-1][1] == start and result[-1][2] == working:
            result[-1][1] = end
        else:
            result.append([start, end, working])
    return result
'''
}

JAVASCRIPT = {
'passwords': '''
function countDistinctPasswords(password) {
  let seen = 0, result = 1;
  const counts = new Map();
  for (const ch of password) {
    result += seen - (counts.get(ch) || 0);
    counts.set(ch, (counts.get(ch) || 0) + 1);
    seen++;
  }
  return result;
}
''',
'coverage': '''
function countFullyCoveredClusters(availability, users) {
  if (!users.length) return 0;
  const rows = users.length, cols = users[0].length, seen = new Set();
  let result = 0;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const id = r * cols + c;
    if (!users[r][c] || seen.has(id)) continue;
    const queue = [[r, c]]; seen.add(id);
    let covered = true;
    for (let head = 0; head < queue.length; head++) {
      const [x, y] = queue[head];
      if (!availability[x][y]) covered = false;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const a = x + dx, b = y + dy, next = a * cols + b;
        if (a >= 0 && a < rows && b >= 0 && b < cols && users[a][b] && !seen.has(next)) {
          seen.add(next); queue.push([a, b]);
        }
      }
    }
    if (covered) result++;
  }
  return result;
}
''',
'squares': '''
function countGridSquares(queries) {
  return queries.map(([rows, cols]) => {
    const r = BigInt(rows), c = BigInt(cols), m = r < c ? r : c;
    return m * (r + 1n) * (c + 1n) - (r + c + 2n) * m * (m + 1n) / 2n + m * (m + 1n) * (2n * m + 1n) / 6n;
  });
}
''',
'ratings': '''
class CustomerSupportSystem {
  constructor() { this.all = new Map(); this.months = new Map(); }
  record(agentId, score, month) {
    if (!this.months.has(month)) this.months.set(month, new Map());
    for (const target of [this.all, this.months.get(month)]) {
      const [sum, count] = target.get(agentId) || [0n, 0n];
      target.set(agentId, [sum + BigInt(score), count + 1n]);
    }
  }
  rank(month) {
    const table = month === null ? this.all : this.months.get(month) || new Map();
    const names = [...table.keys()].sort((a, b) => {
      const [x, nx] = table.get(a), [y, ny] = table.get(b), difference = x * ny - y * nx;
      return difference > 0n ? -1 : difference < 0n ? 1 : a < b ? -1 : a > b ? 1 : 0;
    });
    return names.map(name => {
      const [sum, count] = table.get(name);
      let a = sum < 0n ? -sum : sum, b = count;
      while (b) [a, b] = [b, a % b];
      return [name, sum / a, count / a];
    });
  }
}
''',
'date': '''
function isValidDate(a, b, c) {
  for (const [year, month, day] of [[a,b,c], [a,c,b], [b,a,c], [b,c,a], [c,a,b], [c,b,a]]) {
    if (year < 1 || year > 9999 || month < 1 || month > 12 || day < 1) continue;
    const leap = year % 400 === 0 || year % 4 === 0 && year % 100 !== 0;
    const lengths = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    if (day <= lengths[month - 1]) return true;
  }
  return false;
}
''',
'decode': '''
function decodePassword(text) {
  const coordinates = text[0].trim().slice(1, -1).split(',').map(v => Number(v.trim()));
  return text[coordinates[1] + 1][coordinates[0]];
}
''',
'access': '''
class AccessSystem {
  constructor(parents) {
    const children = new Map(Object.keys(parents).map(name => [name, []]));
    let root;
    for (const [name, parent] of Object.entries(parents)) {
      if (parent === null) root = name; else children.get(parent).push(name);
    }
    this.bounds = new Map(); this.allowed = new Map();
    const stack = [[root, false]]; let counter = 0;
    while (stack.length) {
      const [name, leaving] = stack.pop();
      if (leaving) this.bounds.get(name)[1] = counter;
      else {
        this.bounds.set(name, [counter++, null]); stack.push([name, true]);
        const row = children.get(name);
        for (let i = row.length - 1; i >= 0; i--) stack.push([row[i], false]);
      }
    }
  }
  grant(advertiser, region) {
    const ranges = [...(this.allowed.get(advertiser) || []), this.bounds.get(region)].sort((a,b) => a[0]-b[0]);
    const merged = [];
    for (const [left, right] of ranges) {
      if (merged.length && left <= merged[merged.length-1][1]) merged[merged.length-1][1] = Math.max(merged[merged.length-1][1], right);
      else merged.push([left, right]);
    }
    this.allowed.set(advertiser, merged);
  }
  revoke(advertiser, region) {
    const [low, high] = this.bounds.get(region), result = [];
    for (const [left, right] of this.allowed.get(advertiser) || []) {
      if (right <= low || high <= left) result.push([left, right]);
      else {
        if (left < low) result.push([left, low]);
        if (high < right) result.push([high, right]);
      }
    }
    this.allowed.set(advertiser, result);
  }
  canAccess(advertiser, region) {
    const x = this.bounds.get(region)[0], ranges = this.allowed.get(advertiser) || [];
    let low = 0, high = ranges.length;
    while (low < high) { const mid = Math.floor((low+high)/2); if (ranges[mid][0] <= x) low = mid+1; else high = mid; }
    return low > 0 && x < ranges[low-1][1];
  }
}
''',
'cluster': '''
function clusterSummary(parents) {
  const n = parents.length;
  if (!n) return {count: 0, topology: ''};
  const children = Array.from({length:n}, () => []), counts = Array(n).fill(1), topology = Array(n).fill('');
  let root;
  parents.forEach((p, node) => { if (p === -1) root = node; else children[p].push(node); });
  const pending = children.map(row => row.length), queue = [];
  for (let i = 0; i < n; i++) if (!pending[i]) queue.push(i);
  for (let head = 0; head < queue.length; head++) {
    const node = queue[head], parent = parents[node];
    topology[node] = String(node) + (children[node].length ? '(' + children[node].map(c => topology[c]).join(',') + ')' : '');
    if (parent >= 0) { counts[parent] += counts[node]; if (--pending[parent] === 0) queue.push(parent); }
  }
  return {count: counts[root], topology: topology[root]};
}
''',
'orders': '''
class CryptoOrderManager {
  constructor() { this.orders = new Map(); }
  apply(message) {
    const parts = message.split(',').map(v => v.trim());
    if (parts.length !== 5) return false;
    const [id, side, symbol, raw, event] = parts;
    if (!/^[0-9]+$/.test(raw) || !['NEW','FILLED'].includes(event)) return false;
    const quantity = BigInt(raw), row = this.orders.get(id);
    if (quantity <= 0n) return false;
    if (event === 'NEW') {
      if (row) return row.operation === side && row.symbol === symbol && row.total === quantity;
      this.orders.set(id, {id, operation: side, symbol, total: quantity, filled: 0n, remaining: quantity}); return true;
    }
    if (!row || row.operation !== side || row.symbol !== symbol || quantity > row.remaining) return false;
    row.filled += quantity; row.remaining -= quantity; return true;
  }
  status(orderId) { const row = this.orders.get(orderId); return row ? {...row} : null; }
}
''',
'crypto': '''
class CryptoTradingSystem {
  constructor() { this.orders = new Map(); }
  place(id, currency, amount, timestamp, type) {
    if (this.orders.has(id)) return false;
    this.orders.set(id, {id, currency, amount, timestamp, type, state:'live'}); return true;
  }
  _transition(id, allowed, target) {
    const row = this.orders.get(id);
    if (!row || !allowed.includes(row.state)) return false;
    row.state = target; return true;
  }
  pause(id) { return this._transition(id, ['live'], 'paused'); }
  resume(id) { return this._transition(id, ['paused'], 'live'); }
  cancel(id) { return this._transition(id, ['live','paused'], 'canceled'); }
  complete(id) { return this._transition(id, ['live'], 'completed'); }
  listLive(currency) {
    const compareId = (left, right) => {
      const a = Array.from(left, ch => ch.codePointAt(0)), b = Array.from(right, ch => ch.codePointAt(0));
      for (let i = 0; i < Math.min(a.length,b.length); i++) if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
      return a.length-b.length;
    };
    return [...this.orders.values()].filter(row => row.state === 'live' && (currency === null || row.currency === currency))
      .sort((a,b) => a.timestamp-b.timestamp || compareId(a.id,b.id)).map(row => ({...row}));
  }
}
''',
'ip': '''
class IPRangeIterator {
  constructor(start) { this.current = start.split('.').reduce((n, part) => n*256 + Number(part), 0); }
  hasNext() { return this.current < 4294967296; }
  next() {
    if (!this.hasNext()) return null;
    let value = this.current++; const parts = [];
    for (let i = 0; i < 4; i++) { parts.push(String(value % 256)); value = Math.floor(value/256); }
    return parts.reverse().join('.');
  }
}
''',
'meeting': '''
class MeetingScheduler {
  constructor(rooms) { this.rooms = rooms.slice(); this.bookings = new Map(rooms.map(r => [r, []])); }
  book(start, end) {
    for (const room of this.rooms) {
      const rows = this.bookings.get(room); let low = 0, high = rows.length;
      while (low < high) { const mid = Math.floor((low+high)/2); if (rows[mid][0] < start) low = mid+1; else high = mid; }
      if (low && rows[low-1][1] > start || low < rows.length && rows[low][0] < end) continue;
      rows.splice(low, 0, [start, end]); return room;
    }
    return null;
  }
  schedule(room) { return this.bookings.get(room).map(row => row.slice()); }
}
''',
'pagination': '''
class PaginationAPI {
  constructor(external) { this.external = external; this.buffer = []; this.offset = 0; this.page = 0; this.calls = 0; this.eof = false; }
  read(count) {
    const result = [];
    while (result.length < count) {
      if (this.offset < this.buffer.length) result.push(this.buffer[this.offset++]);
      else if (this.eof) break;
      else {
        this.buffer = this.external.getPage(this.page++).slice(); this.calls++; this.offset = 0;
        if (!this.buffer.length) this.eof = true;
      }
    }
    return result;
  }
  fetchCount() { return this.calls; }
}
class _ExternalPageFixture {
  constructor(pages) { this.pages = pages.map(page => page.slice()); }
  getPage(page) { return page < this.pages.length ? this.pages[page].slice() : []; }
}
''',
'path': '''
class PathKeyValueStore {
  constructor() { this.values = new Map([['/','root']]); this.children = new Map([['/',0]]); }
  _parent(path) { return path.slice(0, path.lastIndexOf('/')) || '/'; }
  create(path, value) {
    const parent = this._parent(path);
    if (this.values.has(path) || !this.values.has(parent)) return false;
    this.values.set(path, value); this.children.set(path, 0); this.children.set(parent, this.children.get(parent)+1); return true;
  }
  set(path, value) { if (path === '/' || !this.values.has(path)) return false; this.values.set(path, value); return true; }
  get(path) { return this.values.has(path) ? this.values.get(path) : null; }
  delete(path) {
    if (path === '/' || !this.values.has(path) || this.children.get(path)) return false;
    const parent = this._parent(path); this.children.set(parent, this.children.get(parent)-1); this.values.delete(path); this.children.delete(path); return true;
  }
}
''',
'radix': '''
function _node() { return {edges: new Map(), terminal:false, value:null}; }
class RadixCache {
  constructor() { this.root = _node(); }
  insert(sequence, value) {
    const key = sequence.slice(); let node = this.root, position = 0;
    while (position < key.length) {
      const edge = node.edges.get(key[position]);
      if (!edge) { const leaf = _node(); leaf.terminal = true; leaf.value = value; node.edges.set(key[position], [key.slice(position), leaf]); return; }
      const [label, child] = edge; let common = 0;
      while (common < label.length && position+common < key.length && label[common] === key[position+common]) common++;
      if (common === label.length) { node = child; position += common; continue; }
      const middle = _node(); middle.edges.set(label[common], [label.slice(common), child]); node.edges.set(label[0], [label.slice(0,common), middle]); position += common;
      if (position === key.length) { middle.terminal = true; middle.value = value; }
      else { const leaf = _node(); leaf.terminal = true; leaf.value = value; middle.edges.set(key[position], [key.slice(position), leaf]); }
      return;
    }
    node.terminal = true; node.value = value;
  }
  get(sequence) {
    let node = this.root, position = 0;
    while (position < sequence.length) {
      const edge = node.edges.get(sequence[position]); if (!edge) return null;
      const [label, child] = edge;
      if (position+label.length > sequence.length || label.some((v,i) => v !== sequence[position+i])) return null;
      position += label.length; node = child;
    }
    return node.terminal ? node.value : null;
  }
}
''',
'rate': '''
class RateLimiter {
  constructor(rules) { this.rules = rules.map(([limit, window]) => ({limit, window, times:[], head:0})); }
  allow(timestamp) {
    let allowed = true;
    for (const rule of this.rules) {
      while (rule.head < rule.times.length && rule.times[rule.head] <= timestamp-rule.window) rule.head++;
      if (rule.times.length-rule.head >= rule.limit) allowed = false;
      if (rule.head > 1024 && rule.head*2 > rule.times.length) { rule.times = rule.times.slice(rule.head); rule.head = 0; }
    }
    if (allowed) for (const rule of this.rules) rule.times.push(timestamp);
    return allowed;
  }
}
''',
'retry': '''
function retry(operation, maxAttempts, initialDelay=0, multiplier=1, onDelay=null) {
  if (maxAttempts < 1) throw new Error('maxAttempts must be positive');
  let delay = initialDelay;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try { return operation(); } catch (error) { if (attempt+1 === maxAttempts) throw error; }
    if (onDelay) onDelay(delay);
    delay *= multiplier;
  }
}
function retryOperation(outcomes, maxAttempts, initialDelay, multiplier) {
  let count = 0; const delays = [];
  const operation = () => {
    const entry = count < outcomes.length ? outcomes[count] : {error:'exhausted'}; count++;
    if (Object.prototype.hasOwnProperty.call(entry,'ok')) return structuredClone(entry.ok);
    throw new Error(entry.error);
  };
  try { const value = retry(operation, maxAttempts, initialDelay, multiplier, delay => delays.push(delay)); return {value, error:null, attempts:count, delays}; }
  catch (error) { return {value:null, error:error.message, attempts:count, delays}; }
}
''',
'trading': '''
class TradingSystem {
  constructor() { this.items = new Map(); this.sequence = 0; }
  _less(a,b) { return a[0] < b[0] || a[0] === b[0] && a[1] < b[1]; }
  addListing(seller, item, price) {
    if (!this.items.has(item)) this.items.set(item, []);
    const heap = this.items.get(item), entry = [price, this.sequence++, seller]; heap.push(entry);
    let i = heap.length-1;
    while (i) { const p = Math.floor((i-1)/2); if (!this._less(heap[i],heap[p])) break; [heap[i],heap[p]] = [heap[p],heap[i]]; i = p; }
  }
  buy(item, budget) {
    const heap = this.items.get(item);
    if (!heap || !heap.length || heap[0][0] > budget) return null;
    const top = heap[0], last = heap.pop();
    if (heap.length) {
      heap[0] = last; let i = 0;
      while (true) {
        let best = i, left = i*2+1, right = left+1;
        if (left < heap.length && this._less(heap[left],heap[best])) best = left;
        if (right < heap.length && this._less(heap[right],heap[best])) best = right;
        if (best === i) break;
        [heap[i],heap[best]] = [heap[best],heap[i]]; i = best;
      }
    }
    return [top[2],top[0]];
  }
}
''',
'goodness': '''
function distinctGoodnessValues(arr) {
  const tails = new Map([[0n,-1]]);
  for (const value of arr) for (const [mask,last] of [...tails]) if (last < value) {
    const combined = mask | BigInt(value);
    if (!tails.has(combined) || value < tails.get(combined)) tails.set(combined, value);
  }
  return [...tails.keys()].map(Number).sort((a,b) => a-b);
}
''',
'products': '''
function distinctPrimeProducts(primes) {
  const values = new Set([1n]);
  for (const prime of primes) for (const value of [...values]) values.add(value * BigInt(prime));
  values.delete(1n);
  return [...values].sort((a,b) => a < b ? -1 : a > b ? 1 : 0);
}
''',
'cars': '''
function dualCarDestinations(grid) {
  const rows = grid.length, cols = grid[0].length, size = rows*cols, positions = {}, neighbors = new Map();
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const value = grid[r][c], cell = r*cols+c; if (value === '#') continue;
    if ('abAB'.includes(value)) positions[value] = cell;
    const next = [];
    for (const [dx,dy] of [[0,0],[1,0],[-1,0],[0,1],[0,-1]]) { const a = r+dx, b = c+dy; if (a >= 0 && a < rows && b >= 0 && b < cols && grid[a][b] !== '#') next.push(a*cols+b); }
    neighbors.set(cell,next);
  }
  const queue = [[positions.a,positions.b,0]], seen = new Set([positions.a*size+positions.b]);
  for (let head = 0; head < queue.length; head++) {
    const [a,b,distance] = queue[head]; if (a === positions.A && b === positions.B) return distance;
    for (const x of neighbors.get(a)) for (const y of neighbors.get(b)) {
      const id = x*size+y;
      if (x === y || x === b && y === a || seen.has(id)) continue;
      seen.add(id); queue.push([x,y,distance+1]);
    }
  }
  return -1;
}
''',
'lru': '''
class LRUCache {
  constructor(capacity) { this.capacity = capacity; this.values = new Map(); }
  _evict() { while (this.values.size > this.capacity) this.values.delete(this.values.keys().next().value); }
  get(key) { if (!this.values.has(key)) return -1; const value = this.values.get(key); this.values.delete(key); this.values.set(key,value); return structuredClone(value); }
  put(key,value) { this.values.delete(key); this.values.set(key,structuredClone(value)); this._evict(); }
  resize(capacity) { this.capacity = capacity; this._evict(); }
}
''',
'earliest': '''
function earliestReachableTime(startX,startY,targetX,targetY,directions) {
  let dx = targetX-startX, dy = targetY-startY;
  if (dx === 0 && dy === 0) return 0;
  for (let i = 0; i < directions.length; i++) {
    const ch = directions[i];
    if (ch === 'E' && dx > 0) dx--; else if (ch === 'W' && dx < 0) dx++;
    else if (ch === 'N' && dy > 0) dy--; else if (ch === 'S' && dy < 0) dy++;
    if (dx === 0 && dy === 0) return i+1;
  }
  return -1;
}
''',
'adjacent': '''
function eliminateAdjacentDuplicates(text) {
  let previous = null, run = 0, changes = 0;
  for (const ch of text) { if (ch === previous) run++; else { previous = ch; run = 1; } if (run % 2 === 0) changes++; }
  return changes;
}
''',
'referrals': '''
function referralLeaderboard(referrers,referrals) {
  const parent = new Map(), nodes = new Set([...referrers,...referrals]), pending = new Map([...nodes].map(n => [n,0])), totals = new Map([...nodes].map(n => [n,0]));
  referrers.forEach((source,i) => { parent.set(referrals[i],source); pending.set(source,pending.get(source)+1); });
  const queue = [...nodes].filter(n => pending.get(n) === 0);
  for (let head = 0; head < queue.length; head++) {
    const node = queue[head]; if (!parent.has(node)) continue;
    const target = parent.get(node); totals.set(target,totals.get(target)+1+totals.get(node)); pending.set(target,pending.get(target)-1); if (!pending.get(target)) queue.push(target);
  }
  return [...new Set(referrers)].sort((a,b) => totals.get(b)-totals.get(a) || (a < b ? -1 : a > b ? 1 : 0)).slice(0,3).map(name => [name,totals.get(name)]);
}
''',
'timeline': '''
function shiftTimeline(schedules) {
  const order = [...new Set(schedules.map(row => row[0]))], events = new Map(), counts = new Map(), result = [];
  const add = (time,name,delta) => { if (!events.has(time)) events.set(time,new Map()); const row = events.get(time); row.set(name,(row.get(name)||0)+delta); };
  for (const [name,start,end] of schedules) { add(start,name,1); add(end,name,-1); }
  const times = [...events.keys()].sort((a,b) => a-b);
  for (let i = 0; i+1 < times.length; i++) {
    const start = times[i], end = times[i+1];
    for (const [name,delta] of events.get(start)) counts.set(name,(counts.get(name)||0)+delta);
    const working = order.filter(name => (counts.get(name)||0) > 0); if (!working.length) continue;
    const last = result[result.length-1];
    if (last && last[1] === start && last[2].length === working.length && last[2].every((v,j) => v === working[j])) last[1] = end;
    else result.push([start,end,working]);
  }
  return result;
}
'''
}


def main():
    frozen = json.loads((HERE/'pre-source-reference-freeze.json').read_text())
    for name, digest in frozen['files'].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest() != digest:
            raise SystemExit('Frozen reference changed: '+name)
    rows = json.loads((HERE/'contracts.json').read_text())['problems']
    for row in rows:
        key = row['key']
        if key is None:
            continue
        for language, extension, collection in [('python','py',PYTHON),('javascript','js',JAVASCRIPT)]:
            directory = HERE/language
            directory.mkdir(exist_ok=True)
            code = textwrap.dedent(collection[key]).strip()+'\n'
            if key in FUNCTIONS:
                function, params = FUNCTIONS[key]
                if language == 'python':
                    code += '\nsolve = '+function+'\n\nclass Solution:\n    '+function+' = staticmethod('+function+')\n'
                else:
                    code += '\nconst solve = '+function+';\nmodule.exports = solve;\nmodule.exports.'+function+' = '+function+';\nmodule.exports.Solution = class { '+function+'(...args) { return '+function+'(...args); } };\n'
                    if key == 'retry': code += 'module.exports.retry = retry;\n'
            else:
                classname, constructor, methods = CLASSES[key]
                if language == 'python':
                    init = classname+'(*argument_lists[0])' if key != 'pagination' else classname+'(_ExternalPageFixture(argument_lists[0][0]))'
                    code += '\ndef solve(operation_names, argument_lists):\n    if len(operation_names) != len(argument_lists) or not operation_names or operation_names[0] != '+repr(classname)+':\n        raise ValueError("exact constructor trace required")\n    instance = '+init+'\n    result = [None]\n    for name, arguments in zip(operation_names[1:], argument_lists[1:]):\n        if name not in '+repr(tuple(methods))+':\n            raise ValueError("unknown method")\n        result.append(getattr(instance, name)(*arguments))\n    return result\n'
                else:
                    init = 'new '+classname+'(...argumentLists[0])' if key != 'pagination' else 'new '+classname+'(new _ExternalPageFixture(argumentLists[0][0]))'
                    code += '\nfunction solve(operationNames, argumentLists) {\n  if (!operationNames.length || operationNames.length !== argumentLists.length || operationNames[0] !== '+json.dumps(classname)+') throw new Error("exact constructor trace required");\n  const instance = '+init+', result = [null], allowed = new Set('+json.dumps(list(methods))+');\n  for (let i = 1; i < operationNames.length; i++) { if (!allowed.has(operationNames[i])) throw new Error("unknown method"); result.push(instance[operationNames[i]](...argumentLists[i]) ?? null); }\n  return result;\n}\nmodule.exports = solve;\nmodule.exports.'+classname+' = '+classname+';\n'
            header = ('"""' if language == 'python' else '// ')+'Original '+row['uid']+'; inferred public-preview contract; qualification unknown.'+('"""\n' if language == 'python' else '\n"use strict";\n')
            (directory/(row['variant_id']+'.'+extension)).write_text(header+code)
    print('Wrote 36 original Python/JavaScript pairs; no qualification claimed.')


if __name__ == '__main__':
    main()
