import unittest
from algsolve.input_fixed_width import fit
from algsolve.input_vocabulary import encode


class FixedWidthInputTests(unittest.TestCase):
    def test_training_only_shortcuts_and_exact_byte_cost(self):
        text = ' '.join(f'common{i}' for i in range(123))
        rows = [{'family':str(i),'split':'train','text':text} for i in range(3)]
        rows += [{'family':'one','split':'train','text':'privateIdentifier ' * 1000},
                 {'family':'dev','split':'development','text':'developmentLeak ' * 1000}]
        for language in ('javascript','python'):
            profile=fit(rows,language)
            self.assertEqual(len(profile['tokens']),256)
            self.assertNotIn('privateIdentifier',profile['tokens'])
            self.assertNotIn('developmentLeak',profile['tokens'])
            book={token:f'{index:08b}' for index,token in enumerate(profile['tokens'])}
            for n in range(128):
                self.assertEqual(book[chr(n)],f'{n:08b}')
            presses,counts=encode('common0 common1',book)
            self.assertEqual(presses,24)
            self.assertEqual(sum(counts.values()),3)

    def test_does_not_invent_filler_entries(self):
        with self.assertRaises(ValueError):
            fit([{'family':'one','split':'train','text':'return value'}],'python')
