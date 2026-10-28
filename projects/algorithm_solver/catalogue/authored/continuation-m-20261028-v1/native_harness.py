"""Fixed EventManager direct-class trace adapter for isolated execution only."""
import importlib.util
import json

def shape(pid,args):
    if type(pid) is not int or pid!=3885 or type(args) is not list or len(args)!=2:raise ValueError('fixed3885 trace required')
    operations,rows=args
    if type(operations) is not list or type(rows) is not list or not operations or len(operations)!=len(rows) or operations[0]!='EventManager' or type(rows[0]) is not list or len(rows[0])!=1 or type(rows[0][0]) is not list:raise ValueError('one initial EventManager(events) required')
    for name,row in zip(operations[1:],rows[1:]):
        if type(name) is not str or name not in ('updatePriority','pollHighest') or type(row) is not list or len(row)!=(2 if name=='updatePriority' else 0):raise ValueError('declared method/arity required')

def observe(namespace,pid,call,transport):
    if type(call) is not dict or set(call)!={'args'}:raise ValueError('argument-only call required')
    args=transport.decode(call['args']);shape(pid,args);native=namespace.get('EventManager')
    if type(native) is not type:raise TypeError('original named EventManager class required; no solve fallback/injected constructor')
    before=transport.encode(args);receiver=native(*args[1][0])
    if type(receiver) is not native:raise TypeError('original class instance required')
    outputs=[None];snapshots=[None];types=['constructed']
    for name,row in zip(args[0][1:],args[1][1:]):
        method=getattr(native,name);value=method(receiver,*row);types.append(type(value).__name__)
        normalized=None if name=='updatePriority' else value;snapshots.append(transport.encode(normalized));outputs.append(normalized)
    return {'result':transport.encode(outputs),'result_type':'list','args_before':before,'args_after':transport.encode(args),'alias_edges':transport.aliases(args,outputs),'native_route':'direct-event-manager-v1','native_class':'EventManager','native_receiver_count':1,'native_method_return_types':types,'native_method_snapshots':snapshots}

def main():
    with open('inputs.json') as stream:packet=json.load(stream)
    if type(packet) is not dict or set(packet)!={'schema','native_problem_id','calls'} or packet['schema']!='gamma.native-class-transport.v1' or type(packet['native_problem_id']) is not int or packet['native_problem_id']!=3885 or type(packet['calls']) is not list:raise ValueError('fixed native argument-only packet required')
    spec=importlib.util.spec_from_file_location('event_native_transport','transport.py');transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
    namespace={'__name__':'candidate'}
    with open('program.py') as stream:raw=stream.read()
    exec(compile(raw,'program.py','exec'),namespace)
    for i,call in enumerate(packet['calls']):
        try:record={'i':i,**observe(namespace,3885,call,transport)}
        except Exception as error:record={'i':i,'error':type(error).__name__+': '+str(error)[:300]}
        print(json.dumps(record,allow_nan=False,separators=(',',':')))
    print(json.dumps({'done':len(packet['calls'])}))
if __name__=='__main__':main()
