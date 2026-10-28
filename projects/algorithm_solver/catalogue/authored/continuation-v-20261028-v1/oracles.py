"""V independent HOST-ONLY semantic/API property models. No child API or transport.
Fixtures/thresholds/expectedanswers remain on host; future API profiles pending.
"""
REQUESTED_IDS=(265,267,269,270,272,273,276,278,280,284)
IDS=(273,278,284)
BLOCKED_IDS=(265,267,269,270,272,276,280)
ITERATOR_MARKER={'official_api':'Iterator','fixture_id':'iterator0'}

def integer(x,lo,hi):return type(x) is int and lo<=x<=hi

def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    if type(a) is dict:return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
    return a==b

# Finite grammar generates every canonical under1000 phrase, independently of
# the candidate's prospective greedy recursive scale decomposition.
_SMALL=('', 'One','Two','Three','Four','Five','Six','Seven','Eight','Nine','Ten','Eleven','Twelve','Thirteen','Fourteen','Fifteen','Sixteen','Seventeen','Eighteen','Nineteen')
_TENS={20:'Twenty',30:'Thirty',40:'Forty',50:'Fifty',60:'Sixty',70:'Seventy',80:'Eighty',90:'Ninety'}
_CHUNKS={i:word for i,word in enumerate(_SMALL)}
for tens,word in _TENS.items():
    for unit in range(10):_CHUNKS[tens+unit]=word+(' '+_SMALL[unit] if unit else '')
for hundreds in range(1,10):
    for remainder in range(100):_CHUNKS[100*hundreds+remainder]=_SMALL[hundreds]+' Hundred'+(' '+_CHUNKS[remainder] if remainder else '')
_INVERSE={v:k for k,v in _CHUNKS.items()}
_SCALES={1000:'Thousand',1000000:'Million',1000000000:'Billion'}

def decode_english(text):
    if text=='Zero':return 0
    if type(text) is not str or not text or text!=' '.join(text.split(' ')):raise ValueError('canonicalspacing')
    tokens=text.split(' ');values={word:value for value,word in _SCALES.items()};previous=10**12;total=0;chunk=[]
    for token in tokens:
        if token in values:
            scale=values[token];phrase=' '.join(chunk)
            if scale>=previous or phrase not in _INVERSE or _INVERSE[phrase]==0:raise ValueError('canonicalscale/chunk')
            total+=_INVERSE[phrase]*scale;previous=scale;chunk=[]
        else:chunk.append(token)
    if chunk:
        phrase=' '.join(chunk)
        if phrase not in _INVERSE or _INVERSE[phrase]==0:raise ValueError('canonicalunits')
        total+=_INVERSE[phrase]
    if not 1<=total<=2**31-1:raise ValueError('range')
    return total

def validate(pid,args,host_api_fixture=None):
    if type(pid) is not int or pid not in IDS or type(args) is not list:raise ValueError('fixedactiveIDs;premiumexcluded')
    if pid==273:
        if len(args)!=1 or not integer(args[0],0,2**31-1) or host_api_fixture is not None:raise ValueError('numberToWordsdomain')
    elif pid==278:
        if len(args)!=1 or not integer(args[0],1,2**31-1) or type(host_api_fixture) is not dict or set(host_api_fixture)!={'first_bad'} or not integer(host_api_fixture['first_bad'],1,args[0]):raise ValueError('firstBadVersionONLYn +HOSTONLYoraclefixture')
    else:
        if len(args)!=2 or type(host_api_fixture) is not dict or set(host_api_fixture)!={'iterator0'}:raise ValueError('HOSTONLYIteratorfixture')
        values=host_api_fixture['iterator0']
        if type(values) is not list or not 1<=len(values)<=1000 or not all(integer(x,1,1000) for x in values):raise ValueError('iteratorvalues')
        ops,rows=args
        if type(ops) is not list or type(rows) is not list or not 1<=len(ops)<=1001 or len(ops)!=len(rows) or ops[0]!='PeekingIterator' or not exact(rows[0],[ITERATOR_MARKER]):raise ValueError('opaqueIteratorconstructor,norawlist')
        cursor=0
        for op,row in zip(ops[1:],rows[1:]):
            if type(op) is not str or op not in ('peek','next','hasNext') or not exact(row,[]):raise ValueError('iteratorofficialmethod/arity')
            if op in ('peek','next'):
                if cursor>=len(values):raise ValueError('invalidexhaustedoperation')
                cursor+=op=='next'
validate_domain=validate

def expected(pid,args,host_api_fixture=None):
    validate(pid,args,host_api_fixture)
    if pid==273:
        num=args[0]
        if num==0:return 'Zero'
        text=str(num);text='0'*((-len(text))%3)+text;groups=[int(text[i:i+3]) for i in range(0,len(text),3)];words=[];scales=('', 'Thousand','Million','Billion')
        for i,group in enumerate(groups):
            if group:words.append(_CHUNKS[group]+(' '+scales[len(groups)-1-i] if len(groups)-1-i else ''))
        return ' '.join(words)
    if pid==278:return host_api_fixture['first_bad']
    values=host_api_fixture['iterator0'];cursor=0;result=[None]
    for op in args[0][1:]:
        if op=='hasNext':value=cursor<len(values)
        else:value=values[cursor];cursor+=op=='next'
        result.append(value)
    return result

def accepts_result(pid,args,result,host_api_fixture=None):
    validate(pid,args,host_api_fixture)
    if pid==278:
        # Unique monotone boundary, independent of candidate binary search.
        return integer(result,1,args[0]) and result>=host_api_fixture['first_bad'] and(result==1 or result-1<host_api_fixture['first_bad'])
    return exact(result,expected(pid,args,host_api_fixture))

def check_api_trace(pid,args,host_api_fixture,trace):
    """HOSTONLY log verifier; genuineprofilemustcaptureevents,nottrustsolverclaims."""
    validate(pid,args,host_api_fixture)
    if type(trace) is not list:return False,'api_trace_type'
    if pid==278:
        n=args[0];limit=(n-1).bit_length()
        if len(trace)>limit or(n>1 and not trace):return False,'api_query_budget'
        for event in trace:
            if type(event) is not dict or set(event)!={'stage','version','result'} or event['stage']!='solver' or not integer(event['version'],1,n) or type(event['result']) is not bool or event['result']!=(event['version']>=host_api_fixture['first_bad']):return False,'api_query_or_response'
        return True,None
    if pid!=284:return (not trace,None if not trace else 'unexpected_api')
    values=host_api_fixture['iterator0'];cursor=0;previous=0;per_operation={};cursor_after={}
    for event in trace:
        if type(event) is not dict or set(event)!={'operation_index','method','result'}:return False,'iterator_trace_shape'
        index=event['operation_index'];method=event['method']
        if not integer(index,1,len(args[0])-1) or index<previous or method not in ('next','hasNext'):return False,'iterator_api_only'
        previous=index;per_operation[index]=per_operation.get(index,0)+1
        if per_operation[index]>1:return False,'selected_lazy_api_budget'
        client=args[0][index]
        if method=='hasNext':
            if client!='hasNext' or type(event['result']) is not bool or event['result']!=(cursor<len(values)):return False,'iterator_hasNext_response'
        else:
            if client not in ('peek','next') or cursor>=len(values) or type(event['result']) is not int or event['result']!=values[cursor]:return False,'iterator_next_response'
            cursor+=1
        cursor_after[index]=cursor
    actual=consumed=0;pending_peek=False
    for index,op in enumerate(args[0][1:],1):
        actual=cursor_after.get(index,actual)
        if op=='next':consumed+=1;pending_peek=False
        elif op=='peek':pending_peek=True
        if actual!=consumed+int(pending_peek):return False,'selected_lazy_iterator_consumption'
    if cursor>len(values):return False,'iterator_consumption'
    return True,None

def check_observation(pid,args,host_api_fixture,record,language):
    """Semantic/API/effectmodel ONLY; reviewedactualproxy/profile remainsrequired."""
    if not accepts_result(pid,args,record.get('result'),host_api_fixture):return False,'wrong_answer'
    if not exact(record.get('args_before'),args) or not exact(record.get('args_after'),args):return False,'input_effect'
    if pid in (278,284):return check_api_trace(pid,args,host_api_fixture,record.get('api_trace'))
    return True,None
