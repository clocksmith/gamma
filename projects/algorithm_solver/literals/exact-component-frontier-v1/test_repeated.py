import time
import unittest
import repeated as r
import frontier as f

class RepeatedControls(unittest.TestCase):
    def test_suffix_inventory_matches_exhaustive_without_materialization(self):
        for a,b in [('ababa','babab'),('aaaa','aaaaa'),('ééaé','aééa')]:
            inv,limits,alpha,legal=r.complete_inventory([a,b],time.monotonic()+2)
            brute={a[i:j] for i in range(len(a)) for j in range(i+2,len(a)+1) if a[i:j] in b}
            self.assertEqual(inv['shared_multichar_entries'],len(brute))
            self.assertEqual(inv['legal_shared_multichar_entries'],sum(legal(s) for s in brute))
            self.assertEqual(r.suffix_array(a),sorted(range(len(a)),key=lambda i:a[i:]))
            for text,lim in zip((a,b),limits):
                cost,pieces=r.relaxed_path(text,lim,legal,time.monotonic()+2)
                dictionary=sorted(set(alpha)|{s for s in brute if legal(s)})
                self.assertEqual(cost,f.exact_path(text,dictionary)[:2])
                self.assertEqual(''.join(pieces),text)

    def test_residual_retires_used_characters_after_merge(self):
        variants={'p':{'v':'ababab'},'q':{'v':'abababab'}}
        states,ledger,count,complete=r.residual_frontier(variants,('a','b'),[('ab',)],time.monotonic()+2)
        self.assertTrue(complete)
        self.assertGreater(count,0)
        for row in states.values():
            self.assertEqual(row['dictionary'],('ab',))
            self.assertEqual(row['metrics']['characters'],0)
            self.assertEqual(row['metrics']['coverage'],2)
        self.assertTrue(ledger)

    def test_singleton_whole_source_cannot_bypass_body_guard(self):
        legal=r.legal_guard(['a','abaa'])
        self.assertFalse(legal('a'))
        self.assertTrue(legal('b'))

    def test_all_U_whole_singleton_source_remains_unreachable(self):
        inv,limits,alpha,legal=r.complete_inventory(['a','abaa'],time.monotonic()+2)
        self.assertNotIn('a',alpha)
        self.assertEqual(r.relaxed_path('a',limits[0],legal,time.monotonic()+2),(None,[]))

    def test_fixed_basis_capacity_not_hidden(self):
        a='abcdefghijklmnopq'
        variants={'p':{'v':a+a},'q':{'v':a+a+a}}
        states,_,_,complete=r.residual_frontier(variants,tuple(a),[],time.monotonic()+2)
        self.assertTrue(complete)
        self.assertIsNone(states[16])
        self.assertEqual(states[32]['metrics']['entries'],17)

    def test_deadline_is_incomplete_not_impossibility(self):
        states,_,_,complete=r.residual_frontier({'p':{'v':'aaa'}},('a',),[],time.monotonic()-1)
        self.assertFalse(complete)
        self.assertFalse(any(states.values()))

if __name__=='__main__':unittest.main()
