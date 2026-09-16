"""Independent calculus checks for the prospective final-bit learner."""
import math
import unittest


def objective(theta, events):
    return sum(y * theta * x - math.log1p(p * math.expm1(theta * x))
               for p, y, x in events)


class FinalBitMath(unittest.TestCase):
    events = [(0.01, 0, .4), (.9, 1, -.7), (.4, 1, .8), (.6, 0, .2)]

    def test_likelihood_identity(self):
        for p, y, x in self.events:
            for theta in (-4., -.1, 0., .1, 4.):
                e = math.exp(theta*x)
                q = p*e/(1-p+p*e)
                direct = math.log((q if y else 1-q)/(p if y else 1-p))
                self.assertAlmostEqual(direct, objective(theta, [(p,y,x)]), places=12)

    def test_gradient_matches_independent_difference(self):
        for theta in (-3., -.1, 0., .1, 3.):
            gradient = 0.
            for p,y,x in self.events:
                e = math.exp(theta*x)
                q = p*e/(1-p+p*e)
                gradient += (y-q)*x
            h = 1e-5
            difference = (objective(theta+h,self.events)-objective(theta-h,self.events))/(2*h)
            self.assertAlmostEqual(gradient, difference, places=9)

    def test_hessian_and_supporting_plane(self):
        for theta in (-3., -.1, 0., .1, 3.):
            gradient = hessian = 0.
            for p,y,x in self.events:
                e = math.exp(theta*x)
                q = p*e/(1-p+p*e)
                gradient += (y-q)*x
                hessian -= q*(1-q)*x*x
            self.assertLessEqual(hessian, 0)
            for other in (-4., -1., 0., 1., 4.):
                self.assertLessEqual(objective(other,self.events),
                                     objective(theta,self.events)+gradient*(other-theta)+1e-12)

    def test_binary_prefix_partition(self):
        visited = set()
        for byte in range(256):
            prefix = 1
            for bit in range(8):
                visited.add(prefix-1)
                prefix = 2*prefix + ((byte >> (7-bit)) & 1)
            self.assertEqual(prefix-256, byte)
        self.assertEqual(visited, set(range(255)))


if __name__ == '__main__':
    unittest.main()
