"""Bounded development checks, not hidden-judge or catalogue qualification."""
import collections
import copy
import functools
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import random
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parents[1]
RNG = random.Random(252001)
CASES = []


def case(pid, args, expected, category='independent_small_oracle'):
    CASES.append({'id': pid, 'args': args, 'expected': expected, 'category': category})


@functools.lru_cache(None)
def moving_ones(s):
    best = 0
    for i in range(len(s) - 1):
        if s[i:i+2] == '10':
            j = i + 1
            while j < len(s) and s[j] == '0':
                j += 1
            best = max(best, 1 + moving_ones(s[:i] + s[i+1:j] + '1' + s[j:]))
    return best


def clipped_disks(width, height, circles):
    """Independent small-coordinate arrangement witness oracle.

    Intersection of two clipped disks has an extreme witness at a center,
    corner, circle/circle crossing, or circle/rectangle crossing. Small integer
    cases use tolerance only to retain exactly tangent geometric witnesses.
    Large integer fixtures use analytically specified expected answers instead.
    """
    eps = 1e-8
    corners = [(0, 0), (width, 0), (0, height), (width, height)]
    def inside(point, disk):
        x, y = point
        a, b, r = disk
        return -eps <= x <= width+eps and -eps <= y <= height+eps and (x-a)**2+(y-b)**2 <= r*r+eps
    def sides(disk):
        x, y, r = disk
        points = []
        for vertical in (True, False):
            for limit in (0, width if vertical else height):
                delta = limit - (x if vertical else y)
                if delta*delta <= r*r:
                    shift = math.sqrt(r*r-delta*delta)
                    for sign in (-1, 1):
                        points.append((limit, y+sign*shift) if vertical else (x+sign*shift, limit))
        return points
    def crossings(a, b):
        x, y, r = a
        u, v, s = b
        dx, dy = u-x, v-y
        distance = math.hypot(dx, dy)
        if distance == 0 or distance > r+s+eps or distance < abs(r-s)-eps:
            return []
        along = (r*r-s*s+distance*distance)/(2*distance)
        across = math.sqrt(max(0, r*r-along*along))
        px, py = x+along*dx/distance, y+along*dy/distance
        return [(px-across*dy/distance, py+across*dx/distance),
                (px+across*dy/distance, py-across*dx/distance)]
    n = len(circles)
    graph = [set() for _ in range(n+2)]
    witnesses = [sides(disk) for disk in circles]
    def connect(a, b):
        graph[a].add(b)
        graph[b].add(a)
    for i, disk in enumerate(circles):
        if inside((0, 0), disk) or inside((width, height), disk):
            return False
        for x, y in witnesses[i] + corners:
            if inside((x, y), disk):
                if abs(x) < eps or abs(y-height) < eps:
                    connect(i, n)
                if abs(y) < eps or abs(x-width) < eps:
                    connect(i, n+1)
        for j in range(i):
            candidates = corners + [disk[:2], circles[j][:2]] + witnesses[i] + witnesses[j] + crossings(disk, circles[j])
            if any(inside(point, disk) and inside(point, circles[j]) for point in candidates):
                connect(i, j)
    reached = {n}
    queue = [n]
    for node in queue:
        for other in graph[node] - reached:
            reached.add(other)
            queue.append(other)
    return n+1 not in reached


def task_model(operations, arguments):
    tasks = {}
    result = []
    for name, args in zip(operations, arguments):
        answer = None
        if name == 'TaskManager':
            tasks = {task: (user, priority) for user, task, priority in args[0]}
        elif name == 'add':
            user, task, priority = args
            tasks[task] = (user, priority)
        elif name == 'edit':
            task, priority = args
            tasks[task] = (tasks[task][0], priority)
        elif name == 'rmv':
            del tasks[args[0]]
        elif name == 'execTop':
            if tasks:
                task = max(tasks, key=lambda key: (tasks[key][1], key))
                answer = tasks.pop(task)[0]
            else:
                answer = -1
        result.append(answer)
    return result


def array_partition_maximum(nums):
    answer = 0
    for mask in range(1 << (len(nums)-1)):
        values, start = [], 0
        for end in range(1, len(nums)+1):
            if end == len(nums) or mask >> (end-1) & 1:
                values.append(max(nums[start:end]))
                start = end
        if values == sorted(values):
            answer = max(answer, len(values))
    return answer


def grid_partition(grid):
    rows, columns = len(grid), len(grid[0])
    cells = {(r, c) for r in range(rows) for c in range(columns)}
    def connected(section):
        if not section:
            return False
        seen = {next(iter(section))}
        queue = list(seen)
        for r, c in queue:
            for point in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if point in section and point not in seen:
                    seen.add(point)
                    queue.append(point)
        return seen == section
    for axis, length in ((0, rows), (1, columns)):
        for cut in range(1, length):
            a = {point for point in cells if point[axis] < cut}
            b = cells-a
            sa = sum(grid[r][c] for r,c in a)
            sb = sum(grid[r][c] for r,c in b)
            if sa == sb:
                return True
            section, diff = (a,sa-sb) if sa > sb else (b,sb-sa)
            for r,c in section:
                if grid[r][c] == diff and connected(section-{(r,c)}):
                    return True
    return False


def stock_oracle(prices, k):
    @functools.lru_cache(None)
    def best(start, count):
        if count == 0:
            return 0
        result = 0
        for i in range(start, len(prices)):
            for j in range(i+1, len(prices)):
                result = max(result, abs(prices[i]-prices[j]) + best(j+1,count-1))
        return result
    return best(0, k)


def partitions_oracle(nums, k):
    @functools.lru_cache(None)
    def ways(start):
        if start == len(nums):
            return 1
        return sum(ways(end) for end in range(start+1, len(nums)+1)
                   if max(nums[start:end])-min(nums[start:end]) <= k)
    return ways(0) % 1_000_000_007


def median_oracle(n, edges, queries):
    graph = [[] for _ in range(n)]
    for a,b,w in edges:
        graph[a].append((b,w))
        graph[b].append((a,w))
    result = []
    for a,b in queries:
        queue = [a]
        paths = {a: [(a,0)]}
        for node in queue:
            for other, weight in graph[node]:
                if other not in paths:
                    paths[other] = paths[node]+[(other,weight)]
                    queue.append(other)
        total = sum(weight for _,weight in paths[b])
        current = 0
        for node,weight in paths[b]:
            current += weight
            if 2*current >= total:
                result.append(node)
                break
    return result


def string_partition(s):
    seen, result, current = set(), [], ''
    for letter in s:
        current += letter
        if current not in seen:
            seen.add(current)
            result.append(current)
            current = ''
    return result


def power_oracle(c, connections, queries):
    graph = [set() for _ in range(c+1)]
    for a,b in connections:
        graph[a].add(b)
        graph[b].add(a)
    offline, result = set(), []
    for kind,x in queries:
        if kind == 2:
            offline.add(x)
        elif x not in offline:
            result.append(x)
        else:
            seen, queue = {x}, [x]
            for node in queue:
                for other in graph[node]-seen:
                    seen.add(other)
                    queue.append(other)
            result.append(min(seen-offline, default=-1))
    return result


def process_literal(s):
    value = ''
    for letter in s:
        if letter == '*': value = value[:-1]
        elif letter == '#': value *= 2
        elif letter == '%': value = value[::-1]
        else: value += letter
    return value


def generate():
    examples = {
        3215: [([[1],[2],[3]],1), ([[1,1],[2,3],[1,5]],4)],
        3228: [(['1001101'],4), (['00111'],0)],
        3235: [([3,4,[[2,1,1]]],True), ([3,3,[[1,1,2]]],False), ([3,3,[[2,1,1],[1,2,1]]],False), ([4,4,[[5,5,1]]],True)],
        3408: [([['TaskManager','add','edit','execTop','rmv','add','execTop'],[[[[1,101,10],[2,102,20],[3,103,15]]],[4,104,5],[102,8],[],[101],[5,105,15],[]]],[None,None,None,3,None,None,5])],
        3514: [([[1,3]],2), ([[6,7,8,9]],4)],
        3523: [([[4,2,5,3,5]],3), ([[1,2,3]],3)],
        3528: [([[[0,1,2],[1,2,3]]],[1,2,6])],
        3537: [([0],[[0]]), ([1],[[3,0],[2,1]]), ([2],[[15,12,3,0],[14,13,2,1],[11,8,7,4],[10,9,6,5]])],
        3548: [([[[1,4],[2,3]]],True),([[[1,2],[3,4]]],True),([[[1,2,4],[2,3,5]]],False),([[[4,1,8],[3,2,6]]],False)],
        3558: [([[[1,2]]],1),([[[1,2],[1,3],[3,4],[3,5]]],2)],
        3566: [([[3,1,6,8,4],24],True),([[2,5,3,7],15],False)],
        3573: [([[1,7,9,8,2],2],14),([[12,16,19,19,8,1,19,13,9],3],36)],
        3578: [([[9,4,1,3,7],4],6),([[3,3,4],0],2)],
        3585: [([2,[[0,1,7]],[[1,0],[0,1]]],[0,1]),([3,[[0,1,2],[2,0,4]],[[0,1],[2,0],[1,2]]],[1,0,2]),([5,[[0,1,2],[0,2,5],[1,3,1],[2,4,3]],[[3,4],[1,2]]],[2,2])],
        3597: [(['abbccccd'],['a','b','bc','c','cc','d']),(['aaaa'],['a','aa'])],
        3607: [([5,[[1,2],[2,3],[3,4],[4,5]],[[1,3],[2,1],[1,1],[2,2],[1,2]]],[3,2,3]),([3,[],[[1,1],[2,1],[1,1]]],[1,-1])],
        3614: [(['a#b%*',1],'a'),(['cd%#*#',3],'d'),(['z*#',0],'.')]
    }
    for pid, values in examples.items():
        for args, expected in values:
            case(pid,args,expected,'public_example')
    for _ in range(80):
        arrays = [[RNG.randrange(32) for _ in range(RNG.randrange(1,7))] for _ in range(3)]
        case(3215,arrays,sum((a^b^c).bit_count()%2==0 for a,b,c in itertools.product(*arrays)))
        s = ''.join(RNG.choice('01') for _ in range(RNG.randrange(1,11)))
        case(3228,[s],moving_ones(s))
        nums = [RNG.randrange(1,32) for _ in range(RNG.randrange(1,9))]
        case(3514,[nums],len({nums[i]^nums[j]^nums[k] for i in range(len(nums)) for j in range(i,len(nums)) for k in range(j,len(nums))}))
        nums = [RNG.randrange(1,8) for _ in range(RNG.randrange(1,9))]
        case(3523,[nums],array_partition_maximum(nums))
        n = RNG.randrange(2,15)
        conversion = [[RNG.randrange(i),i,RNG.choice([1,2,9,999999999,1000000000])] for i in range(1,n)]
        parents = {b:(a,w) for a,b,w in conversion}
        expected = []
        for node in range(n):
            product = 1
            while node:
                node,factor = parents[node]
                product *= factor
            expected.append(product%1_000_000_007)
        RNG.shuffle(conversion)
        case(3528,[conversion],expected)
        rows, columns = RNG.randrange(1,5), RNG.randrange(1,5)
        if rows*columns == 1: columns = 2
        grid = [[RNG.randrange(1,8) for _ in range(columns)] for _ in range(rows)]
        case(3548,[grid],grid_partition(grid))
        n = RNG.randrange(2,10)
        edges = [[RNG.randrange(1,i),i] for i in range(2,n+1)]
        graph = collections.defaultdict(list)
        for a,b in edges: graph[a].append(b); graph[b].append(a)
        depth = {1:0}; queue = [1]
        for node in queue:
            for other in graph[node]:
                if other not in depth: depth[other]=depth[node]+1; queue.append(other)
        d = max(depth.values())
        case(3558,[edges],sum(sum(weights)%2 for weights in itertools.product([1,2], repeat=d)))
        nums = RNG.sample(range(1,16),RNG.randrange(3,9))
        target = RNG.randrange(1,400)
        if RNG.random() < .5:
            target = math.prod(nums[:len(nums)//2])
        expected = any(math.prod(nums[i] for i in range(len(nums)) if mask>>i&1)==target and math.prod(nums[i] for i in range(len(nums)) if not(mask>>i&1))==target for mask in range(1,(1<<len(nums))-1))
        case(3566,[nums,target],expected)
        prices = [RNG.randrange(1,21) for _ in range(RNG.randrange(2,9))]
        k = RNG.randrange(1,len(prices)//2+1)
        case(3573,[prices,k],stock_oracle(prices,k))
        nums = [RNG.randrange(1,10) for _ in range(RNG.randrange(2,10))]; k = RNG.randrange(10)
        case(3578,[nums,k],partitions_oracle(nums,k))
        n = RNG.randrange(2,15)
        edges = [[RNG.randrange(i),i,RNG.choice([1,2,3,1000000000])] for i in range(1,n)]
        queries = [[RNG.randrange(n),RNG.randrange(n)] for _ in range(15)]
        case(3585,[n,edges,queries],median_oracle(n,edges,queries))
        s = ''.join(RNG.choice('abc') for _ in range(RNG.randrange(1,50)))
        case(3597,[s],string_partition(s))
        c = RNG.randrange(1,12)
        edges = [[a,b] for a in range(1,c+1) for b in range(a+1,c+1) if RNG.random()<.2]
        queries = [[RNG.randrange(1,3),RNG.randrange(1,c+1)] for _ in range(25)]
        case(3607,[c,edges,queries],power_oracle(c,edges,queries))
        s = ''.join(RNG.choice('ab*#%') for _ in range(RNG.randrange(1,15)))
        literal = process_literal(s)
        for k in {0,len(literal)//2,max(0,len(literal)-1),len(literal)}:
            case(3614,[s,k],literal[k] if k<len(literal) else '.')
    for _ in range(240):
        width,height = RNG.randrange(3,16),RNG.randrange(3,16)
        disks = [[RNG.randrange(1,22),RNG.randrange(1,22),RNG.randrange(1,9)] for _ in range(RNG.randrange(1,7))]
        case(3235,[width,height,disks],clipped_disks(width,height,disks))
    for _ in range(40):
        operations, arguments = ['TaskManager'],[[[[1,1,3]]]]
        active = {1}
        for step in range(60):
            name = RNG.choice(['add','edit','rmv','execTop'])
            if name == 'add':
                choices = list(set(range(1,21))-active)
                if not choices: continue
                task = RNG.choice(choices); active.add(task)
                args = [RNG.randrange(6),task,RNG.randrange(8)]
            elif name in ('edit','rmv'):
                if not active: continue
                task = RNG.choice(sorted(active))
                args = [task,RNG.randrange(8)] if name=='edit' else [task]
                if name=='rmv': active.remove(task)
            else:
                args = []
                # Reconstruct active identity through a direct dictionary replay.
                state = {}
                for op,arg in zip(operations,arguments):
                    if op=='TaskManager': state={t:(u,p) for u,t,p in arg[0]}
                    elif op=='add': state[arg[1]]=(arg[0],arg[2])
                    elif op=='edit': state[arg[0]]=(state[arg[0]][0],arg[1])
                    elif op=='rmv': del state[arg[0]]
                    elif state: del state[max(state,key=lambda t:(state[t][1],t))]
                if state: active.remove(max(state,key=lambda t:(state[t][1],t)))
            operations.append(name); arguments.append(args)
        case(3408,[operations,arguments],task_model(operations,arguments))
    for n in range(7):
        expected = []
        for row in range(1<<n):
            line = []
            for col in range(1<<n):
                value = 0
                for bit in range(n-1,-1,-1):
                    r,c = row>>bit&1,col>>bit&1
                    value = 4*value + ([[3,0],[2,1]][r][c])
                line.append(value)
            expected.append(line)
        case(3537,[n],expected)
    for length in range(3, 7):
        for nums_tuple in itertools.combinations(range(1, 10), length):
            target = math.isqrt(math.prod(nums_tuple))
            if target * target != math.prod(nums_tuple):
                continue
            nums = list(nums_tuple)
            expected = any(math.prod(nums[i] for i in range(length) if mask >> i & 1) == target
                           for mask in range(1, (1 << length) - 1))
            case(3566, [nums, target], expected, 'independent_square_product_oracle')
    # Analytic numeric/shape probes remain distinct from independent random oracles.
    case(3215,[[0]*100000,[0]*100000,[0]*100000],10**15,'numeric_edge')
    case(3235,[10**9,10**9,[[500000000,500000000,500000000]]],False,'numeric_edge')
    case(3235,[10**9,10**9,[[500000000,500000000,499999999]]],True,'numeric_edge')
    case(3235,[3,3,[[5,1,2],[1,5,2]]],True,'outside_only_contacts')
    case(3235,[3,3,[[5,1,3],[1,5,3]]],False,'corner_covered')
    case(3514,[list(range(1,1501))],2048,'structured_shape')
    case(3523,[list(range(5000,0,-1))],1,'structured_shape')
    case(3558,[[[i,i+1] for i in range(1,5001)]],pow(2,4999,1000000007),'structured_shape')
    case(3566,[[15,20,27,31,78,37,3,100,9,93,39,74],724674600],True,'numeric_edge')
    case(3573,[[1,10**9,1,10**9,1,10**9],3],3*(10**9-1),'numeric_edge')
    case(3578,[[7]*5000,0],pow(2,4999,1000000007),'structured_shape')
    case(3614,['ab'+'#'*48,2**49-1],'b','numeric_edge')
    case(3614,['ab'+'#'*48+'%',2**49-1],'a','numeric_edge')


def main():
    started = time.monotonic()
    generate()
    ids = sorted({row['id'] for row in CASES})
    modules = {}
    source_hashes = {}
    for pid in ids:
        path = BASE/'python'/f'{pid}.py'
        compile(path.read_bytes(),str(path),'exec')
        spec = importlib.util.spec_from_file_location(f'candidate_{pid}',path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules[pid] = module
        subprocess.run(['node','--check',str(BASE/'javascript'/f'{pid}.js')],check=True,capture_output=True,timeout=10)
        source_hashes[str(pid)] = {language:hashlib.sha256((BASE/language/f'{pid}.{extension}').read_bytes()).hexdigest() for language,extension in [('python','py'),('javascript','js')]}
    for row in CASES:
        args = copy.deepcopy(row['args'])
        actual = modules[row['id']].solve(*args)
        assert actual == row['expected'], ('python',row['id'],row['args'],row['expected'],actual)
        assert args == row['args'], ('python input mutation',row['id'])
    runner = Path(__file__).with_name('runner.js')
    result = subprocess.run(['node',str(runner)],input=json.dumps(CASES),text=True,capture_output=True,timeout=60)
    if result.returncode:
        raise AssertionError(result.stderr)
    actuals = json.loads(result.stdout)
    assert len(actuals)==len(CASES)
    for row,actual in zip(CASES,actuals):
        assert actual == row['expected'], ('javascript',row['id'],row['args'],row['expected'],actual)
    # Direct native class exercise (the common tape is not the only interface).
    manager = modules[3408].TaskManager([[9,1,7]])
    manager.edit(1,7); manager.rmv(1); manager.add(5,1,7)
    assert manager.execTop()==5 and manager.execTop()==-1
    counts = {str(pid):dict(collections.Counter(row['category'] for row in CASES if row['id']==pid)) for pid in ids}
    receipt = dict(schema='gamma.authored-candidate-development-tests.v1',seed=252001,problem_count=len(ids),cases_per_language=len(CASES),language_assertions=2*len(CASES),syntax_checks=2*len(ids),native_direct_checks=4,passed=True,source_sha256=source_hashes,per_id=counts,seconds=round(time.monotonic()-started,3),qualification=False,protected_cases_accessed=False)
    Path(__file__).with_name('test-results.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('source_sha256','per_id')},indent=2))


if __name__=='__main__':
    main()
