"""Trusted flat integer-array observer; expected outputs are never supplied."""
import json
packet=json.load(open('inputs.json'));namespace={'__name__':'candidate'}
exec(compile(open('program.py').read(),'program.py','exec'),namespace)
for i,call in enumerate(packet['calls']):
 try:
  args=call['args'];before=[list(args[0])];held=args[0]
  value=namespace['Solution']().duplicateZeros(args[0])
  record={'i':i,'result':value,'result_type':type(value).__name__,'args_before':before,'args_after':args,'same_input_object':args[0]is held}
 except Exception as error:record={'i':i,'error':type(error).__name__+': '+str(error)[:300]}
 print(json.dumps(record,allow_nan=False,separators=(',',':')))
print(json.dumps({'done':len(packet['calls'])}))
