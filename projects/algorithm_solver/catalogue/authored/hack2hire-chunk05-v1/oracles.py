"""Author-frozen development references for explicitly inferred preview contracts.

No candidate imports or cross-language agreement. Small exhaustive constructions,
literal state models and rescanning replace candidate optimizations. Not a judge.
"""
from collections import Counter, deque
from fractions import Fraction
from itertools import permutations, product
import calendar


def reference(key, args):
    if key == 'passwords':
        s, = args
        return len({s[:i] + s[i:j][::-1] + s[j:] for i in range(len(s)) for j in range(i + 1, len(s) + 1)} or {s})
    if key == 'coverage':
        available, users = args
        cells = {(r, c) for r, row in enumerate(users) for c, x in enumerate(row) if x}
        total = 0
        while cells:
            component = {cells.pop()}
            while True:
                adjacent = {p for p in cells if any(abs(p[0]-q[0]) + abs(p[1]-q[1]) == 1 for q in component)}
                if not adjacent:
                    break
                cells -= adjacent
                component |= adjacent
            total += all(available[r][c] for r, c in component)
        return total
    if key == 'squares':
        queries, = args
        return [sum(1 for size in range(1, min(r, c)+1) for y in range(r-size+1) for x in range(c-size+1)) for r, c in queries]
    if key == 'date':
        for y, m, d in permutations(args):
            if 1 <= y <= 9999 and 1 <= m <= 12 and 1 <= d <= calendar.monthrange(y, m)[1]:
                return True
        return False
    if key == 'decode':
        text, = args
        x, y = [int(v.strip()) for v in text[0][1:-1].split(',')]
        return next(ch for row, line in enumerate(text[1:]) for col, ch in enumerate(line) if (col, row) == (x, y))
    if key == 'cluster':
        parents, = args
        if not parents:
            return {'count': 0, 'topology': ''}
        root = parents.index(-1)
        def describe(node):
            children = [i for i, p in enumerate(parents) if p == node]
            return str(node) + ('(' + ','.join(describe(c) for c in children) + ')' if children else '')
        def count(node):
            return 1 + sum(count(i) for i, p in enumerate(parents) if p == node)
        return {'count': count(root), 'topology': describe(root)}
    if key == 'goodness':
        values, = args
        outputs = {0}
        for mask in range(1, 1 << len(values)):
            subset = [v for i, v in enumerate(values) if mask >> i & 1]
            if all(a < b for a, b in zip(subset, subset[1:])):
                result = 0
                for value in subset:
                    result |= value
                outputs.add(result)
        return sorted(outputs)
    if key == 'products':
        primes, = args
        outputs = set()
        for mask in range(1, 1 << len(primes)):
            value = 1
            for i, p in enumerate(primes):
                if mask >> i & 1:
                    value *= p
            outputs.add(value)
        return sorted(outputs)
    if key == 'cars':
        grid, = args
        positions = {x: (r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x in 'abAB'}
        start = (positions['a'], positions['b'])
        goal = (positions['A'], positions['B'])
        frontier = {start}
        seen = {start}
        distance = 0
        def moves(p):
            return [(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] != '#' and abs(r-p[0])+abs(c-p[1]) <= 1]
        while frontier:
            if goal in frontier:
                return distance
            following = set()
            for a, b in frontier:
                for x, y in product(moves(a), moves(b)):
                    if x != y and not (x == b and y == a) and (x, y) not in seen:
                        following.add((x, y))
            seen |= following
            frontier = following
            distance += 1
        return -1
    if key == 'earliest':
        x, y, tx, ty, directions = args
        states = {(x, y)}
        if (tx, ty) in states:
            return 0
        for t, char in enumerate(directions, 1):
            dx, dy = {'E': (1, 0), 'W': (-1, 0), 'N': (0, 1), 'S': (0, -1)}[char]
            states |= {(a+dx, b+dy) for a, b in list(states)}
            if (tx, ty) in states:
                return t
        return -1
    if key == 'adjacent':
        s, = args
        costs = {None: 0}
        for char in s:
            costs = {c: min(cost + (char != c) for last, cost in costs.items() if last != c) for c in 'abcdefghijklmnopqrstuvwxyz'}
        return min(costs.values())
    if key == 'referrals':
        sources, targets = args
        adjacency = {}
        for a, b in zip(sources, targets):
            adjacency.setdefault(a, []).append(b)
        def descendants(node):
            return sum(1 + descendants(child) for child in adjacency.get(node, []))
        return [[name, descendants(name)] for name in sorted(adjacency, key=lambda n: (-descendants(n), n))[:3]]
    if key == 'timeline':
        rows, = args
        names = list(dict.fromkeys(row[0] for row in rows))
        times = sorted({v for name, start, end in rows for v in (start, end)})
        result = []
        for start, end in zip(times, times[1:]):
            working = [name for name in names if any(who == name and a <= start and end <= b for who, a, b in rows)]
            if not working:
                continue
            if result and result[-1][1] == start and result[-1][2] == working:
                result[-1][1] = end
            else:
                result.append([start, end, working])
        return result
    if key == 'retry':
        outcomes, attempts, delay, multiplier = args
        waits = []
        for i in range(attempts):
            entry = outcomes[i] if i < len(outcomes) else {'error': 'exhausted'}
            if 'ok' in entry:
                return {'value': entry['ok'], 'error': None, 'attempts': i+1, 'delays': waits}
            if i+1 == attempts:
                return {'value': None, 'error': entry['error'], 'attempts': i+1, 'delays': waits}
            waits.append(delay * multiplier**i)
    return trace_reference(key, *args)


def trace_reference(key, operations, arguments):
    """Intentionally literal sequential models; actual concurrency is not asserted."""
    state = {}
    initial = arguments[0]
    if key == 'ratings':
        state = {'rows': []}
    elif key == 'access':
        state = {'parents': initial[0], 'grants': {}}
    elif key in ('orders', 'crypto'):
        state = {}
    elif key == 'ip':
        state = {'number': sum(int(n) * 256**(3-i) for i, n in enumerate(initial[0].split('.')))}
    elif key == 'meeting':
        state = {room: [] for room in initial[0]}
    elif key == 'pagination':
        pages = initial[0]
        data = []
        for page in pages:
            if not page:
                break
            data += page
        state = {'pages': pages, 'data': data, 'offset': 0, 'calls': 0, 'fetched': 0, 'eof': False}
    elif key == 'path':
        state = {'/': 'root'}
    elif key == 'radix':
        state = {}
    elif key == 'rate':
        state = {'rules': initial[0], 'accepted': []}
    elif key == 'lru':
        state = {'capacity': initial[0], 'pairs': []}
    elif key == 'trading':
        state = {'rows': [], 'sequence': 0}
    else:
        raise ValueError('Unknown frozen reference: ' + key)
    results = [None]
    for op, params in zip(operations[1:], arguments[1:]):
        out = None
        if key == 'ratings':
            if op == 'record':
                state['rows'].append(tuple(params))
            else:
                month, = params
                groups = {}
                for agent, score, seen_month in state['rows']:
                    if month is None or month == seen_month:
                        groups.setdefault(agent, []).append(score)
                order = sorted(groups, key=lambda name: (-Fraction(sum(groups[name]), len(groups[name])), name))
                out = [[name, Fraction(sum(groups[name]), len(groups[name])).numerator, Fraction(sum(groups[name]), len(groups[name])).denominator] for name in order]
        elif key == 'access':
            advertiser, region = params
            granted = state['grants'].setdefault(advertiser, set())
            if op == 'canAccess':
                out = region in granted
            else:
                subtree = set()
                for node in state['parents']:
                    current = node
                    while current is not None:
                        if current == region:
                            subtree.add(node)
                            break
                        current = state['parents'][current]
                if op == 'grant':
                    granted |= subtree
                else:
                    granted -= subtree
        elif key == 'orders':
            if op == 'status':
                row = state.get(params[0])
                out = dict(row) if row else None
            else:
                oid, side, symbol, quantity, event = [x.strip() for x in params[0].split(',')]
                quantity = int(quantity)
                row = state.get(oid)
                if event == 'NEW':
                    out = quantity > 0 and (row is None or (row['operation'], row['symbol'], row['total']) == (side, symbol, quantity))
                    if out and row is None:
                        state[oid] = {'id': oid, 'operation': side, 'symbol': symbol, 'total': quantity, 'filled': 0, 'remaining': quantity}
                else:
                    out = row is not None and side == row['operation'] and symbol == row['symbol'] and 0 < quantity <= row['remaining']
                    if out:
                        row['filled'] += quantity
                        row['remaining'] -= quantity
        elif key == 'crypto':
            if op == 'place':
                oid, currency, amount, timestamp, side = params
                out = oid not in state
                if out:
                    state[oid] = {'id': oid, 'currency': currency, 'amount': amount, 'timestamp': timestamp, 'type': side, 'state': 'live'}
            elif op == 'listLive':
                out = [dict(row) for row in sorted(state.values(), key=lambda r: (r['timestamp'], r['id'])) if row['state'] == 'live' and (params[0] is None or row['currency'] == params[0])]
            else:
                row = state.get(params[0]); old = row['state'] if row else None
                allowed = {'pause': ('live',), 'resume': ('paused',), 'cancel': ('live', 'paused'), 'complete': ('live',)}
                out = old in allowed[op]
                if out:
                    row['state'] = {'pause': 'paused', 'resume': 'live', 'cancel': 'canceled', 'complete': 'completed'}[op]
        elif key == 'ip':
            if op == 'hasNext':
                out = state['number'] <= 2**32-1
            elif state['number'] <= 2**32-1:
                out = '.'.join(str(state['number'] // 256**i % 256) for i in (3, 2, 1, 0))
                state['number'] += 1
        elif key == 'meeting':
            if op == 'schedule':
                out = [list(v) for v in sorted(state[params[0]])]
            else:
                start, end = params
                for room, rows in state.items():
                    if all(end <= a or b <= start for a, b in rows):
                        rows.append((start, end)); out = room; break
        elif key == 'pagination':
            if op == 'fetchCount':
                out = state['calls']
            else:
                size, = params
                wanted = min(len(state['data']), state['offset']+size)
                while not state['eof'] and state['fetched'] < wanted:
                    page = state['pages'][state['calls']] if state['calls'] < len(state['pages']) else []
                    state['calls'] += 1; state['fetched'] += len(page)
                    if not page:
                        state['eof'] = True
                if size > len(state['data'])-state['offset'] and not state['eof']:
                    state['calls'] += 1; state['eof'] = True
                out = state['data'][state['offset']:wanted]; state['offset'] = wanted
        elif key == 'path':
            path = params[0]
            if op == 'get':
                out = state.get(path)
            elif op == 'create':
                parent = path.rsplit('/', 1)[0] or '/'; out = path not in state and parent in state
                if out: state[path] = params[1]
            elif op == 'set':
                out = path != '/' and path in state
                if out: state[path] = params[1]
            elif op == 'delete':
                out = path != '/' and path in state and not any(other.startswith(path+'/') for other in state)
                if out: del state[path]
        elif key == 'radix':
            seq = tuple(params[0])
            if op == 'insert': state[seq] = params[1]
            else: out = state.get(seq)
        elif key == 'rate':
            t, = params
            out = all(sum(t-window < previous <= t for previous in state['accepted']) < limit for limit, window in state['rules'])
            if out: state['accepted'].append(t)
        elif key == 'lru':
            pairs = state['pairs']
            if op == 'get':
                found = next((i for i, (k, v) in enumerate(pairs) if k == params[0]), None)
                out = -1 if found is None else pairs[found][1]
                if found is not None: pairs.append(pairs.pop(found))
            elif op == 'put':
                pairs[:] = [p for p in pairs if p[0] != params[0]]; pairs.append(tuple(params))
            else:
                state['capacity'] = params[0]
            while len(pairs) > state['capacity']: pairs.pop(0)
        elif key == 'trading':
            if op == 'addListing':
                state['rows'].append([*params, state['sequence']]); state['sequence'] += 1
            else:
                item, budget = params
                candidates = [r for r in state['rows'] if r[1] == item and r[2] <= budget]
                if candidates:
                    row = min(candidates, key=lambda r: (r[2], r[3])); state['rows'].remove(row); out = [row[0], row[2]]
        results.append(out)
    return results
