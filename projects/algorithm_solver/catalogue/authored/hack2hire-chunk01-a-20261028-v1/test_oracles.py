import copy
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import time
import unittest
HERE = Path(__file__).parent


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, file); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


_o = _load('gamma_h2h01a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h01a_reference_test_cases', HERE / 'cases.py')
reference, validate_domain = _o.reference, _o.validate_domain
CONTRACTS = {row['uid']: row for row in json.loads((HERE / 'contracts.json').read_text())['problems']}


def stem(uid): return uid.split(':', 1)[1]


def exact(a, b):
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(map(exact, a, b))
    if type(a) is dict: return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    return a == b


def ops(name, ctor, calls): return _c._ops(name, ctor, calls)


class References(unittest.TestCase):
    def test_ads(self):
        ads = [{'adId': 'x', 'maxDisplay': 2}, {'adId': 'y', 'maxDisplay': 1}, {'adId': 'z', 'maxDisplay': 3}]
        self.assertEqual(reference(_o.ADS, [['p', 'q', 'r'], ads, {'x': 2, 'w': 9}, [1, 4, 0]]), ['z', 'y', None])

    def test_cameras(self):
        self.assertEqual(reference(_o.CAM1, [[1, 2, 5, 9, 10], [3, 5, 1, 7, 7], 3]), [[1, 2], [9, 10]])
        self.assertEqual(reference(_o.CAM2, [[1, 2, 5, 9, 10], [3, 5, 1, 7, 7], [2, 3, 9], [4, 0, 4], 3]), [[2, 2], [9, 9]])

    def test_pack(self):
        self.assertEqual(reference(_o.PACK, [[3, 5, 7]]), 3)
        self.assertEqual(reference(_o.PACK, [[0, 0]]), 0)
        self.assertEqual(reference(_o.PACK, [[4, 9]]), 1)

    def test_crawl(self):
        links = {'http://a.com/x': ['http://a.com/y', 'http://b.com/', 'http://sub.a.com/'], 'http://a.com/y': ['http://a.com/x', 'http://a.com']}
        self.assertEqual(reference(_o.CRAWL, ['http://a.com/x', links]), ['http://a.com', 'http://a.com/x', 'http://a.com/y'])

    def test_menu(self):
        leaf = lambda k, a: {'key': k, 'value': '', 'active': a, 'children': []}
        tree = {'key': 'r', 'value': '', 'active': True, 'children': [leaf('a', False), {'key': 'b', 'value': '1', 'active': True, 'children': [leaf('c', True)]}]}
        self.assertEqual(reference(_o.MENU, [tree]), {'key': 'r', 'value': '', 'active': True, 'children': [{'key': 'b', 'value': '1', 'active': True, 'children': [leaf('c', True)]}]})

    def test_island(self):
        self.assertEqual(reference(_o.ISLAND, [[['1', '1', '0'], ['0', '0', '1']]]), [[2, 3], [1, 2]])

    def test_flip(self):
        self.assertEqual(reference(_o.FLIP, ['0110', ['count:2', 'flip', 'count:3', 'count:0']]), [2, 2, 1])

    def test_forest(self):
        self.assertEqual(reference(_o.FOREST1, [[2, 2, 2, 0, 4], 0]), [-1, 2, 2, -1, 4])
        self.assertEqual(reference(_o.FOREST2, [[2, 2, 2, 0, 4], [3, 3, 4]]), [2, 2, 2, -1, -1])

    def test_delivery(self):
        t = ops('DeliverySystem', [], [('addDriver', 1, 1000), ('addDelivery', 1, 0, 5400), ('addDriver', 2, 1), ('addDelivery', 2, 0, 1800),
                                       ('getTotalCost',), ('payUpTo', 5399), ('getTotalCostUnpaid',), ('getMaxActiveDriversInLast24Hours', 86400)])
        self.assertEqual(reference(_o.DELIVERY3, t), [None] * 5 + ['15.01', None, '15.00', 2])
        t = ops('DeliverySystem', [], [('addDriver', 1, 1), ('addDelivery', 1, 0, 100), ('addDelivery', 1, 200, 300), ('getMaxActiveDriversInLast24Hours', 86500)])
        self.assertEqual(reference(_o.DELIVERY3, t)[-1], 1)
        t = ops('DeliverySystem', [], [('addDriver', 1, 1), ('addDelivery', 1, 0, 100), ('getMaxActiveDriversInLast24Hours', 86500)])
        self.assertEqual(reference(_o.DELIVERY3, t)[-1], 0)

    def test_deploy(self):
        recs = ['0,10,allowed', '5,20,allowed', '8,12,freeze', '30,40,freeze']
        self.assertEqual(reference(_o.DEPLOY1, [recs]), 16)
        self.assertEqual(reference(_o.DEPLOY2, [recs]), [[0, 8], [12, 20]])
        rng = random.Random(3)
        for _ in range(300):
            recs = [f'{a},{a + rng.randrange(1, 9)},{rng.choice(["allowed", "freeze"])}' for a in [rng.randrange(0, 40) for _ in range(rng.randrange(0, 6))]]
            self.assertTrue(_o._second_deploy_check(recs))

    def test_bank(self):
        D = _o.DAY_MS
        t = ops('BankingSystem', [], [('createAccount', 1, 'a'), ('createAccount', 2, 'b'), ('deposit', 3, 'a', 1000), ('pay', 4, 'a', 300),
                                      ('transfer', 5, 'a', 'b', 200), ('topSpenders', 6, 5), ('getPaymentStatus', 7, 'a', 'payment1'),
                                      ('mergeAccounts', 8, 'b', 'a'), ('getPaymentStatus', 9, 'a', 'payment1'), ('getPaymentStatus', 10, 'b', 'payment1'),
                                      ('getBalance', D + 4, 'b', 7), ('getBalance', D + 5, 'b', D + 4), ('getBalance', D + 6, 'a', 8), ('getBalance', D + 7, 'a', 7),
                                      ('createAccount', D + 8, 'a'), ('getBalance', D + 9, 'a', D + 8), ('topSpenders', D + 10, 2)])
        self.assertEqual(reference(_o.BANK4, t), [None, True, True, 1000, 'payment1', 500, ['a(500)', 'b(0)'], 'IN_PROGRESS', True, None,
                                                  'IN_PROGRESS', 200, 706, -1, 500, True, 0, ['b(500)', 'a(0)']])

    def test_cards(self):
        deck = _o.full_deck()
        self.assertEqual(reference(_o.CARD2, [deck, 3])[0][:2], [['CLUBS', 'A'], ['CLUBS', '4']])
        self.assertEqual(len(reference(_o.CARD2, [deck, 3])[0]), 17)
        wins = reference(_o.CARD3, [deck, 4]); self.assertEqual((len(wins), sum(wins)), (4, 13))

    def test_connect(self):
        t = ops('ConnectKGame', [3], [('placePiece', 'B', 0), ('placePiece', 'B', 1), ('placePiece', 'R', 2), ('placePiece', 'B', 2),
                                      ('placePiece', 'R', 0), ('placePiece', 'R', 1)])
        self.assertEqual(reference(_o.CONNECT, t), [None, False, False, False, True, False, False])
        diag = ops('ConnectKGame', [3], [('placePiece', 'B', 0), ('placePiece', 'B', 1), ('placePiece', 'R', 1), ('placePiece', 'B', 2),
                                         ('placePiece', 'R', 2), ('placePiece', 'B', 2)])
        self.assertEqual(reference(_o.CONNECT, diag), [None, False, False, False, False, False, True])

    def test_document(self):
        t = ops('Document', [], [('setProperty', 1, 'color', 'red'), ('setProperty', 1, 'color', 'blue'), ('undo',), ('getProperty', 1, 'color'),
                                 ('redo',), ('getProperty', 1, 'color'), ('removeProperty', 1, 'color'), ('getProperties', 1), ('undo',),
                                 ('getProperties', 1), ('removeProperty', 2, 'x'), ('redo',)])
        self.assertEqual(reference(_o.DOC3, t), [None, None, None, True, 'red', True, 'blue', True, [], True, [['color', 'blue']], False, True])

    def test_tennis(self):
        t = ops('TennisGame', [], [('pointTo', 'A')] * 3 + [('pointTo', 'B')] * 3 + [('getScore',), ('pointTo', 'B'), ('getScore',), ('pointTo', 'B'), ('getScore',),
                                                                                     ('pointTo', 'A'), ('getPoints',), ('getWinner',)])
        self.assertEqual(reference(_o.TENNIS1, t), [None] * 7 + ['Deuce', None, 'Advantage B', None, 'Game B', None, [3, 5], 'B'])
        t = ops('TennisSet', [], [('pointTo', 'A')] * 20 + [('pointTo', 'B')] * 20 + [('pointTo', 'A')] * 4 + [('pointTo', 'B')] * 4 +
                [('getGames',), ('getGameScore',)] + [('pointTo', 'A')] * 6 + [('pointTo', 'B')] * 8 + [('getGames',), ('getWinner',), ('getGameScore',)])
        out = reference(_o.TENNIS2, t)
        self.assertEqual(out[49:51], [[6, 6], 'Tiebreak 0-0'])
        self.assertEqual(out[-3:], [[6, 7], 'B', 'Set B'])

    def test_find(self):
        t = ops('FileSystem', [], [('addFile', '/a/f.txt', 5), ('addFile', '/a/b/fa.py', 50), ('addFile', '/ab/f.txt', 70),
                                   ('find', '/a', [['namePrefix', 'f']]), ('find', '/', [['sizeGreaterThan', 5], ['extension', 'txt']])])
        self.assertEqual(reference(_o.FIND1, t)[-2:], [['/a/b/fa.py', '/a/f.txt'], ['/ab/f.txt']])
        t = ops('FileSystem', [], [('addFile', '/a/f.txt', 5), ('addFile', '/a/b/fa.py', 50), ('addFile', '/ab/f.txt', 70),
                                   ('find', '/', ['or', [['not', ['extension', 'txt']], ['sizeGreaterThan', 60]]])])
        self.assertEqual(reference(_o.FIND2, t)[-1], ['/a/b/fa.py', '/ab/f.txt'])

    def test_domain(self):
        for uid, args in [(_o.FOREST1, [[1, 0], 0]), (_o.PACK, [[]]), (_o.FLIP, ['01', ['count:2']]), (_o.DEPLOY1, [['5,5,allowed']]),
                          (_o.BANK1, ops('BankingSystem', [], [('createAccount', 2, 'a'), ('createAccount', 2, 'b')])),
                          (_o.BANK1, ops('BankingSystem', [], [('topSpenders', 1, 1)])), (_o.CARD1, [_o.full_deck()[:51] + [['CLUBS', 'A']]]),
                          (_o.DELIVERY1, ops('DeliverySystem', [], [('addDelivery', 1, 0, 1)])), (_o.FIND1, ops('FileSystem', [], [('find', '/', [['or', []]])])),
                          (_o.CAM1, [[2, 2], [1, 1], 1])]:
            with self.assertRaises(ValueError, msg=str(args)[:60]): validate_domain(uid, args)

    def test_generated_cases_domain_valid(self):
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True): validate_domain(uid, row['args'])

    def test_contract_layouts_match_classes(self):
        for uid, row in CONTRACTS.items():
            if uid in _o.CLASSES:
                name, ctor, methods, voids = _o.CLASSES[uid]
                iface = row['inferred_interface']
                self.assertEqual(iface['classname'], name)
                self.assertEqual(len(iface['constructor']['params']), ctor)
                self.assertEqual({m['name']: len(m['params']) for m in iface['methods']}, methods)


JS_RUNNER = r'''
const fs=require('fs');const job=JSON.parse(fs.readFileSync(0,'utf8'));const mod=require(job.path);const out=[];
const cpu=(t)=>{const d=process.cpuUsage(t);return (d.user+d.system)/1e6;};
for(const args of job.cases){const before=JSON.stringify(args);let value,native=null;const t0=process.cpuUsage();
 value=mod(...args);const solveCpu=cpu(t0);const t1=process.cpuUsage();
 if(job.cls){const C=mod[job.cls];const r=new C(...args[1][0]);native=[null];
  for(let i=1;i<args[0].length;i++){let v=r[args[0][i]](...args[1][i]);if(job.voids.includes(args[0][i])){if(v!==undefined)throw Error('void returned value');v=null;}native.push(v);}}
 else native=mod[job.wrapper](...args);
 out.push({value,native,unchanged:JSON.stringify(args)===before,cpu:Math.max(solveCpu,cpu(t1))});}
process.stdout.write(JSON.stringify(out));'''
TIMES = {'python3': {}, 'node_jitless': {}}


class Candidates(unittest.TestCase):
    """Author-local self-check of own candidates against own generated cases; not isolated qualification."""
    def run_python(self, uid, rows):
        path = HERE / 'python' / f'{stem(uid)}.py'
        if not path.exists(): self.skipTest('candidate absent')
        module = _load(f'gamma_h2h01a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
        iface = CONTRACTS[uid]['inferred_interface']
        for row in rows:
            args = copy.deepcopy(row['args']); t0 = time.process_time(); value = module.solve(*args); t1 = time.process_time()
            if uid in _o.CLASSES:
                name, _, _, voids = _o.CLASSES[uid]
                receiver = getattr(module, name)(*args[1][0]); native = [None]
                for op, r in zip(args[0][1:], args[1][1:]):
                    v = getattr(receiver, op)(*r)
                    if op in voids: self.assertIsNone(v); v = None
                    native.append(v)
            else: native = getattr(module.Solution(), iface['name'])(*args)
            worst = max(worst, t1 - t0, time.process_time() - t1)  # one execution: trace adapter or direct class, whichever is slower
            self.assertTrue(exact(value, row['expected']) and exact(native, row['expected']), f'{uid} python {str(row["args"])[:100]}')
            self.assertEqual(args, row['args']); passed += 1
        TIMES['python3'][uid] = round(worst, 4)
        return passed

    def run_javascript(self, uid, rows):
        path = HERE / 'javascript' / f'{stem(uid)}.js'
        if not path.exists() or not shutil.which('node'): self.skipTest('candidate or node absent')
        cls = _o.CLASSES.get(uid)
        job = {'path': str(path), 'cases': [r['args'] for r in rows], 'cls': cls and cls[0], 'voids': list(cls[3]) if cls else [],
               'wrapper': None if cls else CONTRACTS[uid]['inferred_interface']['name']}
        flags = ['--jitless'] if os.environ.get('GAMMA_JITLESS', '1') == '1' else []
        res = subprocess.run(['node', *flags, '--stack-size=65500', '-e', JS_RUNNER], input=json.dumps(job), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr[-2000:])
        out = json.loads(res.stdout)
        for row, got in zip(rows, out):
            self.assertTrue(exact(got['value'], row['expected']) and exact(got['native'], row['expected']), f'{uid} javascript {str(row["args"])[:100]}')
            self.assertTrue(got['unchanged'])
        TIMES['node_jitless'][uid] = round(max(g['cpu'] for g in out), 4)
        self.assertEqual(len(out), len(rows)); return len(out)

    def test_candidates(self):
        only = os.environ.get('GAMMA_ONLY')
        for uid in _o.IDS:
            if only and only not in uid: continue
            rows = _c.build_cases(uid, include_maximum=True)
            for language, runner in [('python', self.run_python), ('javascript', self.run_javascript)]:
                with self.subTest(uid=uid, language=language):
                    print(f'{uid} {language} {runner(uid, rows)}/{len(rows)} passed', flush=True)
        print('HEAVIEST_CPU_SECONDS ' + json.dumps(TIMES), flush=True)


if __name__ == '__main__': unittest.main()
