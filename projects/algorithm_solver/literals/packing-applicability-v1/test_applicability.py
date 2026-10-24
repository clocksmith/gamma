"""binding() against a brute-force n = min(m, N // len) < m count on random small texts."""
import random, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import applicability


def brute(text):
    N = len(text); subs = {text[i:j] for i in range(N) for j in range(i + 2, N + 1)}
    m = {s: sum(text.startswith(s, i) for i in range(N)) for s in subs}
    return sum(min(v, N // len(s)) < v for s, v in m.items()), max((v * len(s) / N for s, v in m.items()), default=0.0)


class Tests(unittest.TestCase):
    def test_matches_brute_force(self):
        rng = random.Random(76)
        for _ in range(300):
            t = ''.join(rng.choice(rng.choice(['ab', 'abc', 'a ', 'xyz{}'])) for _ in range(rng.randint(2, 30)))
            self.assertEqual(applicability.binding(t), brute(t))

    def test_known_cases(self):
        self.assertEqual(applicability.binding('aaaa')[0], 2)   # 'aa': m 3, N//2 = 2; 'aaa': m 2, N//3 = 1
        self.assertEqual(applicability.binding('abcd')[0], 0)
        self.assertEqual(applicability.binding('ababab')[0], 1)  # only 'abab': m 2, 6//4 = 1 ('ababa' occurs once)


if __name__ == '__main__':
    unittest.main()
