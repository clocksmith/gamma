"""Independent definition-based references; never imports a delivered program."""
from collections import Counter, deque
from functools import lru_cache
from itertools import combinations, groupby, permutations, product
import ipaddress
import math
import re

IDS = (402, 403, 406, 408, 410, 413, 416, 417, 418, 419, 421, 423,
       424, 433, 435, 436, 438, 440, 442, 443, 446, 447, 451, 452,
       453, 454, 456, 457, 458, 462, 464, 467, 468, 473, 474, 475,
       477, 481, 486, 491, 493, 494, 495, 498, 502, 503)
DIGITS = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')
DEFINITION_FAILURES = {408: 'Official public definition unavailable (premium); local cases are prepared evidence only',
                       418: 'Official public definition unavailable (premium); local cases are prepared evidence only'}
MANDATORY_FAILURES = {(442, language): 'Counts map has input-sized auxiliary memory; mandatory O(1) auxiliary space excluding output is unmet'
                      for language in ('python', 'javascript')}
MANDATORY_FAILURES.update({(443, language): 'Original API returns a separate compressed array; mandatory input mutation and new-length return are absent'
                           for language in ('python', 'javascript')})


def subset_indices(n):
    for mask in range(1 << n):
        yield [i for i in range(n) if mask >> i & 1]


def components(board, symbol='X'):
    unseen = {(r, c) for r, row in enumerate(board) for c, value in enumerate(row) if value == symbol}
    result = []
    while unseen:
        node = unseen.pop(); group = {node}; queue = [node]
        for r, c in queue:
            for neighbor in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                if neighbor in unseen:
                    unseen.remove(neighbor); group.add(neighbor); queue.append(neighbor)
        result.append(group)
    return result


def word_digits(s):
    """Exact multiset cover, independent of unique-letter elimination."""
    alphabet = ''.join(sorted(set(''.join(DIGITS))))
    counts = tuple(s.count(c) for c in alphabet)
    words = [tuple(word.count(c) for c in alphabet) for word in DIGITS]

    @lru_cache(None)
    def cover(remaining):
        if not any(remaining):
            return ()
        letter = min((i for i,v in enumerate(remaining) if v),
                     key=lambda i: sum(w[i] > 0 for w in words))
        for digit, word in enumerate(words):
            if word[letter] and all(a >= b for a,b in zip(remaining,word)):
                result = cover(tuple(a-b for a,b in zip(remaining,word)))
                if result is not None:
                    return tuple(sorted((digit, *result)))
        return None
    answer = cover(counts)
    if answer is None:
        raise ValueError('invalid spelled-digit input')
    return ''.join(map(str, answer))


@lru_cache(None)
def magical_prefix(n):
    # Expand whole run-length descriptions until their fixed prefix covers n.
    text = '122'
    while len(text) < n:
        expanded = ''.join(('1' if i % 2 == 0 else '2') * int(c)
                           for i, c in enumerate(text))
        assert expanded.startswith(text)
        text = expanded
    return text[:n]


def expected(pid, args):
    x = args[0]
    if pid == 402:
        width = len(x) - args[1]
        return str(min((int(''.join(x[i] for i in positions)) if positions else 0)
                       for positions in combinations(range(len(x)), width)))
    if pid == 403:
        queue = deque([(0, 0)]); seen = {(0,0)}; positions = set(x)
        while queue:
            position, jump = queue.popleft()
            if position == x[-1]: return True
            for step in (jump-1,jump,jump+1):
                target = position+step
                if step > 0 and target in positions and (target,step) not in seen:
                    seen.add((target,step)); queue.append((target,step))
        return False
    if pid == 406:
        return sorted(map(tuple, x))  # Parameter to the complete output predicate.
    if pid == 408:
        pieces = re.findall(r'[0-9]+|[a-z]', args[1])
        if ''.join(pieces) != args[1] or any(p[0] == '0' for p in pieces if p[0].isdigit()): return False
        pattern = ''.join('.{' + str(int(p)) + '}' if p[0].isdigit() else re.escape(p) for p in pieces)
        return re.fullmatch(pattern, x) is not None
    if pid == 410:
        return min(max(sum(x[a:b]) for a,b in zip((0,*cuts),(*cuts,len(x))))
                   for cuts in combinations(range(1,len(x)), args[1]-1))
    if pid == 413:
        return sum(all(x[k]-x[k-1] == x[i+1]-x[i] for k in range(i+2,j))
                   for i in range(len(x)) for j in range(i+3,len(x)+1))
    if pid == 416:
        total = sum(x)
        return total % 2 == 0 and any(2*sum(x[i] for i in indices) == total for indices in subset_indices(len(x)))
    if pid == 417:
        rows, cols = len(x), len(x[0]); answer = []
        for r in range(rows):
            for c in range(cols):
                visited = {(r,c)}; queue = [(r,c)]
                for i,j in queue:
                    for nr,nc in ((i-1,j),(i+1,j),(i,j-1),(i,j+1)):
                        if (0 <= nr < rows and 0 <= nc < cols and x[nr][nc] <= x[i][j]
                                and (nr,nc) not in visited):
                            visited.add((nr,nc)); queue.append((nr,nc))
                if any(i == 0 or j == 0 for i,j in visited) and any(i == rows-1 or j == cols-1 for i,j in visited):
                    answer.append([r,c])
        return answer
    if pid == 418:
        words, rows, cols = args; offset = 0
        for _ in range(rows):
            cursor = 0
            while cursor + len(words[offset % len(words)]) <= cols:
                cursor += len(words[offset % len(words)]) + 1; offset += 1
        return offset // len(words)
    if pid == 419: return len(components(x))
    if pid == 421: return max(a ^ b for a,b in product(x, repeat=2))
    if pid == 423: return word_digits(x)
    if pid == 424:
        return max(j-i for i in range(len(x)) for j in range(i+1,len(x)+1)
                   if j-i-max(Counter(x[i:j]).values()) <= args[1])
    if pid == 433:
        start, end, bank = args; vertices = sorted(set(bank) | {start})
        if start == end: return 0
        if end not in vertices: return -1
        n = len(vertices); distance = [[0 if i == j else 1 if sum(a!=b for a,b in zip(vertices[i],vertices[j])) == 1 else n+1
                                       for j in range(n)] for i in range(n)]
        for k in range(n):
            for i in range(n):
                for j in range(n): distance[i][j] = min(distance[i][j],distance[i][k]+distance[k][j])
        value = distance[vertices.index(start)][vertices.index(end)]
        return value if value <= n else -1
    if pid == 435:
        return len(x)-max(len(indices) for indices in subset_indices(len(x))
                          if all(a[1] <= b[0] for a,b in zip(sorted(x[i] for i in indices),sorted(x[i] for i in indices)[1:])))
    if pid == 436:
        return [min(((a,i) for i,(a,_) in enumerate(x) if a >= end),default=(0,-1))[1] for _,end in x]
    if pid == 438:
        return [i for i in range(len(x)-len(args[1])+1) if sorted(x[i:i+len(args[1])]) == sorted(args[1])]
    if pid == 440: return sorted(range(1,x+1),key=str)[args[1]-1]
    if pid == 442: return sorted({v for v in x if x.count(v) == 2})
    if pid == 443:
        answer = []
        for value, group in groupby(x):
            count = sum(1 for _ in group); answer.append(value)
            if count > 1: answer.extend(str(count))
        return answer
    if pid == 446:
        return sum(len(indices) >= 3 and len({x[b]-x[a] for a,b in zip(indices,indices[1:])}) == 1
                   for indices in subset_indices(len(x)))
    if pid == 447:
        return sum((a[0]-b[0])**2+(a[1]-b[1])**2 == (a[0]-c[0])**2+(a[1]-c[1])**2
                   for a,b,c in permutations(x,3))
    if pid == 451:
        return ''.join(c*n for c,n in sorted(Counter(x).items(),key=lambda p:(-p[1],p[0])))
    if pid == 452:
        points = sorted({end for _,end in x})
        return min(len(indices) for indices in subset_indices(len(points))
                   if all(any(start <= points[i] <= end for i in indices) for start,end in x))
    if pid == 453: return sum(x)-len(x)*min(x)
    if pid == 454: return sum(sum(values) == 0 for values in product(*args))
    if pid == 456: return any(a < c < b for a,b,c in combinations(x,3))
    if pid == 457:
        for start in range(len(x)):
            order = {}; current = start
            while current not in order and (x[current] > 0) == (x[start] > 0):
                order[current] = len(order); current = (current+x[current]) % len(x)
            if current in order and len(order)-order[current] > 1: return True
        return False
    if pid == 458:
        states = args[2] // args[1] + 1
        return next(p for p in range(11) if states**p >= x)
    if pid == 462: return min(sum(abs(v-target) for v in x) for target in set(x))
    if pid == 464:
        maximum, desired = args
        if desired == 0: return True
        if maximum*(maximum+1)//2 < desired: return False
        @lru_cache(None)
        def won(available, remaining):
            return any(v >= remaining or not won(tuple(a for a in available if a != v),remaining-v)
                       for v in available)
        return won(tuple(range(1,maximum+1)),desired)
    if pid == 467:
        alphabet = 'abcdefghijklmnopqrstuvwxyz' * (len(x)//26+2)
        return len({x[i:j] for i in range(len(x)) for j in range(i+1,len(x)+1)
                    if x[i:j] == alphabet[ord(x[i])-97:ord(x[i])-97+j-i]})
    if pid == 468:
        if re.fullmatch(r'[0-9]+(?:\.[0-9]+){3}',x):
            try: ipaddress.IPv4Address(x); return 'IPv4'
            except ipaddress.AddressValueError: return 'Neither'
        if re.fullmatch(r'[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4}){7}',x):
            return 'IPv6'
        return 'Neither'
    if pid == 473:
        if sum(x) % 4: return False
        target = sum(x)//4; full = (1 << len(x))-1
        groups = [mask for mask in range(1,full+1) if sum(v for i,v in enumerate(x) if mask >> i & 1) == target]
        @lru_cache(None)
        def partition(mask):
            if not mask: return True
            first = mask & -mask
            return any(group & first and group & mask == group and partition(mask ^ group) for group in groups)
        return partition(full)
    if pid == 474:
        return max([0]+[len(indices) for indices in subset_indices(len(x))
                        if sum(x[i].count('0') for i in indices) <= args[1]
                        and sum(x[i].count('1') for i in indices) <= args[2]])
    if pid == 475: return max(min(abs(h-t) for t in args[1]) for h in x)
    if pid == 477: return sum((a ^ b).bit_count() for a,b in combinations(x,2))
    if pid == 481: return magical_prefix(x).count('1')
    if pid == 486:
        @lru_cache(None)
        def game(values):
            if not values: return 0
            return max(values[0]-game(values[1:]),values[-1]-game(values[:-1]))
        return game(tuple(x)) >= 0
    if pid == 491:
        return sorted({tuple(x[i] for i in indices) for indices in subset_indices(len(x))
                       if len(indices) >= 2 and all(x[a] <= x[b] for a,b in zip(indices,indices[1:]))})
    if pid == 493: return sum(x[i] > 2*x[j] for i,j in combinations(range(len(x)),2))
    if pid == 494: return sum(sum(v*s for v,s in zip(x,signs)) == args[1] for signs in product((-1,1),repeat=len(x)))
    if pid == 495: return len({t for start in x for t in range(start,start+args[1])})
    if pid == 498:
        cells = sorted(((r,c) for r,row in enumerate(x) for c in range(len(row))),key=lambda p:(sum(p),p[0] if sum(p)%2 else -p[0]))
        return [x[r][c] for r,c in cells]
    if pid == 502:
        k,w,profits,capital = args; reachable = {0}; best = w
        for _ in range(min(k,len(profits))):
            nxt = set()
            for mask in reachable:
                cash = w+sum(p for i,p in enumerate(profits) if mask >> i & 1); best = max(best,cash)
                for i,c in enumerate(capital):
                    if not mask >> i & 1 and c <= cash: nxt.add(mask | 1 << i)
            reachable = nxt
        return max([best]+[w+sum(p for i,p in enumerate(profits) if mask >> i & 1) for mask in reachable])
    if pid == 503:
        return [next((x[(i+step)%len(x)] for step in range(1,len(x)) if x[(i+step)%len(x)] > value),-1)
                for i,value in enumerate(x)]
    raise ValueError('unregistered problem')


def exact(a,b):
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a == b


def int_matrix(value, width=None):
    return type(value) is list and all(type(row) is list and (width is None or len(row) == width)
                                        and all(type(v) is int for v in row) for row in value)


def matches(pid,args,value,want):
    if pid == 406:
        return (int_matrix(value,2) and sorted(map(tuple,value)) == want
                and all(sum(p[0] >= h for p in value[:i]) == k for i,(h,k) in enumerate(value)))
    if pid == 451:
        if type(value) is not str or Counter(value) != Counter(args[0]): return False
        groups = [(c,len(list(g))) for c,g in groupby(value)]
        return len({c for c,_ in groups}) == len(groups) and all(a >= b for (_,a),(_,b) in zip(groups,groups[1:]))
    if pid == 417:
        return int_matrix(value,2) and sorted(map(tuple,value)) == sorted(map(tuple,want))
    if pid == 442:
        return type(value) is list and all(type(v) is int for v in value) and sorted(value) == want
    if pid == 491:
        return int_matrix(value) and sorted(map(tuple,value)) == want
    return exact(value,want)


def compare(pid,args,want,record,language):
    if 'error' in record: return False,'candidate_error'
    kind = list if pid in (406,491) else type(want)
    kinds = {'python':{list:'list',int:'int',bool:'bool',str:'str'},
             'javascript':{list:'object',int:'number',bool:'boolean',str:'string'}}
    if record.get('result_type') != kinds[language][kind]: return False,'result_type'
    if not matches(pid,args,record.get('result'),want): return False,'result_value'
    if not exact(record.get('args_before'),args) or not exact(record.get('args_after'),args): return False,'input_effects'
    if not exact(record.get('alias_edges'),[]): return False,'mutable_return_alias'
    return True,None
