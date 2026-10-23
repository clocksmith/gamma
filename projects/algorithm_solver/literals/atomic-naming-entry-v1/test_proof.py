import unittest
import proof


class ProofTests(unittest.TestCase):
    def test_paid_atomic_context_and_character_only_plateau_are_distinct(self):
        rows=proof.proof()['rows'];seed=rows['seed']
        self.assertTrue(all(r['entries']==256 for r in rows.values()))
        self.assertGreater(rows['rename_only']['N'],seed['N'])
        self.assertGreaterEqual(proof.lex(rows['label_only']),proof.lex(seed))
        self.assertGreaterEqual(proof.lex(rows['context_entries_only']),proof.lex(seed))
        self.assertEqual(rows['label_atomic']['N'],seed['N'])
        self.assertLess(rows['label_atomic']['C'],seed['C'])
        self.assertEqual(rows['label_atomic']['package_bytes'],seed['package_bytes'])
        self.assertGreater(rows['label_atomic']['source_bytes'],seed['source_bytes'])
        self.assertLess(rows['rename_plus_context_without_label']['N'],seed['N'])
        self.assertLess(rows['context_atomic']['N'],rows['rename_plus_context_without_label']['N'])
        self.assertLess(rows['context_atomic']['N'],seed['N'])
        self.assertLess(rows['context_atomic']['N'],rows['literal_two_entry_control']['N'])
        self.assertGreater(rows['context_atomic']['dictionary_bytes'],seed['dictionary_bytes'])
        self.assertLess(rows['context_atomic']['package_bytes'],seed['package_bytes'])
        self.assertEqual(rows['context_atomic']['decoder_bytes'],13010)

    def test_existing_capture_guard_rejects_new_name_collision(self):
        text='function solve(a){return a+aa;}'
        rec=proof.rewrite.records({'p':text})['p'];colors=[v['name'] for v in rec['variables']]
        target=next(v for v in rec['variables'] if v['name']=='a')
        colors[target['id']]='aa'
        self.assertFalse(proof.rewrite.legal(rec,colors))


if __name__=='__main__':unittest.main()
