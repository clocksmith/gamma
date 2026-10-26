import copy
import unittest

from algsolve.compare_bits_profiles import compare


class ComparisonTests(unittest.TestCase):
    def profile(self):
        index={name:'fixed' for name in ('keys_sha256','vectors_sha256','catalogue_sha256','packets_sha256','gate_sha256')}
        index['runtime']={'models':{role:{'manifest_sha256':'same'} for role in ('embedding','rerank')}}
        row={'query_sha256':'query','timings':{'total_ms':5},'diagnostics':{'evidence':[
            {'key':'a','document_sha256':'document','document_scope':'published-statement',
             'tokenIds':[1,2],'tokenCount':2,'trueLogit':1.,'falseLogit':0.}]}}
        return {'index':index},[row]

    def test_changed_execution_with_same_tokens_can_be_compared(self):
        baseline=self.profile();candidate=copy.deepcopy(baseline)
        candidate[1][0]['diagnostics']['evidence'][0]['trueLogit']+=.001
        result=compare(baseline,candidate)
        self.assertTrue(result['executed_tokens_identical'])
        self.assertFalse(result['recognition_qualified'])

    def test_input_changes_and_excessive_numeric_drift_cannot_pass(self):
        for field,value in [('tokenIds',[1,3]),('document_sha256','other'),('trueLogit',1.1)]:
            with self.subTest(field=field):
                baseline=self.profile();candidate=copy.deepcopy(baseline)
                candidate[1][0]['diagnostics']['evidence'][0][field]=value
                with self.assertRaises(ValueError):compare(baseline,candidate)
        baseline=self.profile();candidate=copy.deepcopy(baseline)
        candidate[0]['index']['vectors_sha256']='different'
        with self.assertRaises(ValueError):compare(baseline,candidate)


if __name__=='__main__':unittest.main()
