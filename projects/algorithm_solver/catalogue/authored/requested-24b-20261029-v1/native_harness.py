"""Fixed native-class development observer. No solve fallback or constructor injection."""
import copy

def observe(module, pid, args):
    name = {1622:'Fancy',1656:'OrderedStream'}[pid]
    native = getattr(module,name)
    assert isinstance(native,type)
    before = copy.deepcopy(args)
    operations,rows = args
    receiver = native(*rows[0])
    assert type(receiver) is native
    outputs=[None];retained=[]
    for operation,row in zip(operations[1:],rows[1:]):
        method=getattr(native,operation)
        value=method(receiver,*row)
        if pid==1622 and operation!='getIndex':assert value is None
        elif pid==1622:assert type(value) is int
        else:
            assert type(value) is list and all(type(v) is str for v in value)
            assert not any(value is previous for previous in retained)
            retained.append(value)
        outputs.append(value)
    assert args==before
    return outputs
