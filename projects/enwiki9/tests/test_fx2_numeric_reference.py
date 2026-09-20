import unittest
import numpy as np
from gamma_enwiki9.adapters.fx2_numeric_reference import first_difference,differences,loss_bits

class NumericAttributionTests(unittest.TestCase):
    def test_signed_zero_is_not_an_integer_bin_change(self):
        key=(0,'q.integer');order=[key]
        native={key:np.array([0,3],dtype='f4')};reference={key:np.array([-0.,4],dtype='f4')}
        self.assertEqual(first_difference(native,reference,order,suffix='.integer')['coordinate'],1)
        self.assertEqual(differences(native,reference,order)['integer_elements_different'],1)
        self.assertEqual(first_difference({(0,'q.input'):native[key]},{(0,'q.input'):reference[key]},[(0,'q.input')])['coordinate'],0)

    def test_loss_excludes_piece_end_and_unpaired_final_row(self):
        tokens=np.array([0,1,2,1,0]);markers=np.array([1,0,2,1,0])
        p=np.full((5,3),.25,dtype='f4');p[2]=0;p[4]=0
        report,truth=loss_bits(p,tokens,markers)
        self.assertEqual(report,{'bits':6.,'predictions':3})
        p[1,2]=0
        with self.assertRaises(ValueError):loss_bits(p,tokens,markers)

if __name__=='__main__':unittest.main()
