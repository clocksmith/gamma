import unittest
import protocol


class NativeContract(unittest.TestCase):
    def test_native_length_prefix_and_ignored_tail(self):
        args=[['a','a','a']];want=['a','3']
        record={'result_type':'dict','result':{'length':2,'prefix':want},'args_before':args,
                'args_after':[['a','3','z']],'alias_edges':[]}
        self.assertEqual(protocol.native_compare(args,want,record,'python'),(True,None))
        self.assertEqual(protocol.native_compare(args,want,dict(record,args_after=[['a','3']]),'python'),(True,None))
        self.assertEqual(protocol.native_compare(args,want,dict(record,args_after=args),'python'),(False,'native_prefix_mutation'))
        self.assertEqual(protocol.native_compare(args,want,dict(record,result={'length':True,'prefix':want}),'python'),(False,'native_result_value'))
        self.assertEqual(protocol.native_compare(args,want,dict(record,result={'bad_length_type':'list'}),'python'),(False,'native_result_value'))
        self.assertEqual(protocol.native_compare(args,want,dict(record,alias_edges=[['result.prefix','args.0']]),'python'),(False,'native_return_alias'))


if __name__=='__main__':unittest.main()
