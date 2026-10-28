"""Versioned Q native/effect checker; expected answers never enter the child."""
import importlib.util
from pathlib import Path

SPEC=importlib.util.spec_from_file_location('q_original_source_blind_reference',Path(__file__).resolve().parent.parent/'authored/continuation-q-20261028-v1/oracles.py')
reference=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(reference)
METHODS={126:'findLadders',129:'sumNumbers',132:'minCut',133:'cloneGraph',138:'copyRandomList',140:'wordBreak',141:'hasCycle',142:'detectCycle',143:'reorderList',144:'preorderTraversal'}
NATIVE={129,133,138,141,142,143,144}


def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    if type(a) is dict:return set(a)==set(b) and all(exact(a[k],b[k]) for k in a)
    return a==b


def expected(pid,args):
    reference.validate_domain(pid,args)
    if pid==126 and args[1] not in args[2]:return []
    if pid==132 and len(args[0])>17:
        text=args[0]
        if text==text[::-1]:return 0
        if len(set(text))==2 and all(text[i]==text[i%2] for i in range(len(text))):return 1
        raise ValueError('independent cut certificate unavailable for this large string')
    if pid==140 and len(args[0])>16 and len(args[1])==1:
        text,words=args;word=words[0]
        return [' '.join([word]*(len(text)//len(word)))] if len(text)%len(word)==0 and text==word*(len(text)//len(word)) else []
    return reference.reference(pid,args)


def original_pool(pid,packet):
    n=len(packet['values']);rows=[]
    for i,value in enumerate(packet['values']):
        row={'value':value}
        if pid in (129,144):row.update(left=packet['left'][i],right=packet['right'][i])
        elif pid==133:row['neighbors']=packet['neighbors'][i][:]
        else:
            row['next']=i+1 if i+1<n else packet['pos'] if pid in (141,142) and packet['pos']!=-1 else None
            if pid==138:row['random']=packet['random'][i]
        rows.append(row)
    return rows


def clone_corresponds(pid,before,root,clones,clone_root):
    n=len(before)
    if type(clones) is not list or len(clones)!=n:return False
    if not n:return clone_root is None and root is None
    if type(clone_root) is not int or not 0<=clone_root<n:return False
    fields={'value','neighbors'} if pid==133 else {'value','next','random'}
    def valid_index(value,nullable=True):return (nullable and value is None) or (type(value) is int and 0<=value<n)
    for row in clones:
        if type(row) is not dict or set(row)!=fields or type(row['value']) is not int:return False
        if pid==133:
            if type(row['neighbors']) is not list or any(not valid_index(v,False) for v in row['neighbors']):return False
        elif not valid_index(row['next']) or not valid_index(row['random']):return False
    if pid==133:
        # Labels are unique under the verified official graph domain. This
        # semantic successor permits output-neighbor permutations; the original
        # ordered reference remains one valid canonical witness, unchanged.
        values=[row['value'] for row in clones]
        if len(set(values))!=n or set(values)!={row['value'] for row in before}:return False
        mapping={row['value']:i for i,row in enumerate(clones)}
        if mapping[before[root]['value']]!=clone_root:return False
        inverse={i:j for j,row in enumerate(before) for i in [mapping[row['value']]]}
        for i,row in enumerate(before):
            actual=clones[mapping[row['value']]]['neighbors']
            wanted=row['neighbors']
            # Counts, not just set equality: no duplicate/missing edge repair.
            if len(actual)!=len(wanted) or sorted(inverse[j] for j in actual)!=sorted(wanted):return False
        return True
    forward={};reverse={};pending=[(root,clone_root)]
    for old,new in pending:
        if old is None or new is None:
            if old is not None or new is not None:return False
            continue
        if old in forward:
            if forward[old]!=new:return False
            continue
        if new in reverse:return False
        forward[old]=new;reverse[new]=old
        if before[old]['value']!=clones[new]['value']:return False
        pending.extend((before[old][field],clones[new][field]) for field in ('next','random'))
    return len(forward)==n and len(reverse)==n


def check_observation(pid,args,record,language):
    try:
        if type(pid) is not int or pid not in METHODS:raise ValueError('fixed identity')
        reference.validate_domain(pid,args)
        if language not in ('python','javascript') or type(record) is not dict or 'error' in record:return False,'observation_shape'
        kind='python-solution-method' if language=='python' else 'javascript-official-function'
        if record.get('entry_kind')!=kind or record.get('native_route')!='official-wrapper-q-v1' or type(record.get('problem_id')) is not int or record['problem_id']!=pid or record.get('method')!=METHODS[pid]:return False,'official_route'
        if not exact(record.get('args_before'),args):return False,'argument_before'
        if pid not in NATIVE:
            if not exact(record.get('args_after'),args) or not exact(record.get('alias_edges'),[]) or record.get('node_identity') is not None or record.get('node_integrity') is not None:return False,'ordinary_effects'
            wanted=expected(pid,args);result=record.get('result')
            if pid in (126,140):
                if record.get('result_type')!=('list' if language=='python' else 'object') or type(result) is not list:return False,'result_type'
                if pid==126:
                    if any(type(path) is not list or any(type(word) is not str for word in path) for path in result):return False,'result_type'
                    actual=[tuple(path) for path in result];desired=[tuple(path) for path in wanted]
                else:
                    if any(type(value) is not str for value in result):return False,'result_type'
                    actual=result;desired=wanted
                return (True,None) if len(set(actual))==len(actual) and set(actual)==set(desired) else (False,'unordered_distinct_result')
            return (True,None) if record.get('result_type')==('int' if language=='python' else 'number') and exact(result,wanted) else (False,'result_value')
        packet=args[0];before=original_pool(pid,packet);n=len(before);root=packet.get('root',0 if n else None)
        identity=record.get('node_identity')
        keys={'before','after','argument_root','original_node_count','result_original_index','clone_pool','clone_root','reordered'}
        if type(identity) is not dict or set(identity)!=keys or not exact(identity['before'],before) or not exact(identity['argument_root'],root) or type(identity['original_node_count']) is not int or identity['original_node_count']!=n:return False,'original_identity'
        after=[dict(row) for row in before];reordered=None
        if pid==143:
            reordered=expected(pid,args);order=reordered['original_identity_order']
            for i,index in enumerate(order):after[index]['next']=order[i+1] if i+1<n else None
        if not exact(identity['after'],after) or not exact(record.get('args_after'),[{'__native_pool__':after,'root':root}]):return False,'original_effects'
        integrity={'schema':'gamma.q-native-identity-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'clone_pool_disjoint':True if pid in (133,138) else None,'original_neighbor_containers_unchanged':True if pid==133 else None}
        if not exact(record.get('node_integrity'),integrity):return False,'physical_integrity'
        aliases=[];result_index=None
        if pid in (133,138):
            clones=identity['clone_pool'];clone_root=identity['clone_root']
            if not clone_corresponds(pid,before,root,clones,clone_root) or not exact(record.get('result'),{'__clone_pool__':clones,'root':clone_root}):return False,'deep_clone_topology'
            result_type=('Node' if n else 'NoneType') if language=='python' else 'object'
        else:
            if not exact(identity['clone_pool'],[]) or identity['clone_root'] is not None:return False,'unexpected_clone'
            wanted=expected(pid,args)
            if not exact(record.get('result'),wanted):return False,'result_value'
            if pid==142:
                result_index=wanted
                if result_index is not None:aliases=[['result',f'args.0.pool.{result_index}']]
                result_type=('ListNode' if result_index is not None else 'NoneType') if language=='python' else 'object'
            elif pid==143:result_type='NoneType' if language=='python' else 'undefined'
            elif pid==141:result_type='bool' if language=='python' else 'boolean'
            elif pid==144:result_type='list' if language=='python' else 'object'
            else:result_type='int' if language=='python' else 'number'
        if not exact(identity['result_original_index'],result_index) or not exact(identity['reordered'],reordered) or not exact(record.get('alias_edges'),aliases) or record.get('result_type')!=result_type:return False,'native_return_identity_type'
        return True,None
    except (ValueError,TypeError,KeyError,IndexError,OverflowError,RecursionError):return False,'invalid_or_unsupported_observation'
