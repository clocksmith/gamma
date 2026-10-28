import unittest,json
from native import judge

class NativeObserverControls(unittest.TestCase):
 def test_good_and_bad_native_effects(self):
  values=[{'args':[[0,1,0]],'expected':[0,0,1]}];meta={'exit_code':0,'timed_out':False,'output_limit_exceeded':False};base={'i':0,'result':None,'result_type':'NoneType','args_before':[[0,1,0]],'args_after':[[0,0,1]],'same_input_object':True}
  def raw(row,done=1):return(json.dumps(row)+'\n'+json.dumps({'done':done})+'\n').encode()
  self.assertEqual(judge('python',values,[0],meta,raw(base)),[])
  js=dict(base,result_type='undefined');self.assertEqual(judge('javascript',values,[0],meta,raw(js)),[])
  for changes,reason in [({'result':[0,0,1],'result_type':'list'},'native_void_return'),({'args_after':[[0,1,0]]},'native_in_place_result'),({'same_input_object':False},'native_input_object_identity')]:
   row=dict(base,**changes);self.assertIn(reason,judge('python',values,[0],meta,raw(row))[0]['reasons'])
  self.assertEqual(judge('python',values,[0],meta,raw(base,True))[0]['reason'],'observation_protocol')
  self.assertEqual(judge('python',values,[0],meta,raw(dict(base,extra=True)))[0]['reason'],'observation_protocol')
if __name__=='__main__':unittest.main()
