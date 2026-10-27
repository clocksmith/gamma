"""Bounded public-spec state-machine references; never loads candidates.

The [operations, arguments] wire is oracle-only, not an invented solve interface.
Constructor and state continuity need existing observer/adapter review later.
"""
from itertools import product
import json
import random
import string

from . import imported_qualification as q
from .request_git_queue03_oracles import integer, ints

IDS=(2227,2241,2276,2286,2296,2336,2349,2353)
CLASSES={2227:'Encrypter',2241:'ATM',2276:'CountIntervals',2286:'BookMyShow',2296:'TextEditor',
         2336:'SmallestInfiniteSet',2349:'NumberContainers',2353:'FoodRatings'}
TITLES={2227:'Encrypt and Decrypt Strings',2241:'Design an ATM Machine',2276:'Count Integers in Intervals',
        2286:'Booking Concert Tickets in Groups',2296:'Design a Text Editor',2336:'Smallest Number in Infinite Set',
        2349:'Design a Number Container System',2353:'Design a Food Rating System'}
DEFINITION_SHA256={2227:'6307ead38a32cacb2b99a3dbe2d074fd28d63896a3f209f0daa0fce7bdadc671',
2241:'cd23b1c902ac95e257c0b21a44ae8d110b1630e9703d2b2c6e334688b79949e7',
2276:'b6ba09220feaf1c379b5161a35c560c5272bff15f6b0b1f3384db465c22ab449',
2286:'010d271431dde9a17b099ee436d5eb62997ef09f60948670f64ee98ddb62d97c',
2296:'b08317434d5008e94f0a664934352a77e54ad1d803d21c78ca88dddcc47f48a4',
2336:'325d8fd7f96777c2705f097ab7567289abeacf4e57699713226be26f345d5078',
2349:'900ba2cae345c3d196c0eeaa19a846fba330168107d656039a3be1eaeeae2fd5',
2353:'1e843e9dfd896d1c8c040122982049843865ca41a9286d1999dcd5ffa882cf26'}
METHODS={2227:{'encrypt':('word1',),'decrypt':('word2',)},2241:{'deposit':('banknotesCount',),'withdraw':('amount',)},
2276:{'add':('left','right'),'count':()},2286:{'gather':('k','maxRow'),'scatter':('k','maxRow')},
2296:{'addText':('text',),'deleteText':('k',),'cursorLeft':('k',),'cursorRight':('k',)},
2336:{'popSmallest':(),'addBack':('num',)},2349:{'change':('index','number'),'find':('number',)},
2353:{'changeRating':('food','newRating'),'highestRated':('cuisine',)}}
CONSTRUCTOR_PARAMETERS={2227:('keys','values','dictionary'),2241:(),2276:(),2286:('n','m'),2296:(),2336:(),2349:(),2353:('foods','cuisines','ratings')}
MAX_CALLS={2227:200,2241:5000,2276:100000,2286:50000,2296:20000,2336:1000,2349:100000,2353:20000}
SCOPE={
 'evidence':'Exposed-development bounded public-spec references, not fresh confirmation, source qualification, or a new execution engine.',
 'wire':'[operations, arguments] includes exactly one constructor at index0 and ordered method arguments. Outputs include constructor/void null. This is an oracle serialization only; actual candidate interface remains unresolved.',
 'effects':'Internal state evolution and failed-operation rollback are normative where specified. No caller-input preservation or returned-object alias requirement is inferred from statements. Native instance isolation, receiver, method dispatch, intermediate snapshots, result aliasing and no external IO require an explicit frozen observer policy later.',
 'numeric':'All numeric wire values are exact ints excluding bool; state counts/seat capacity at most5e13, all within JS safe integers. Methods returning bool must remain bool. Strings use the exact lowercase ASCII domain; no Unicode extrapolation.',
 'complexity':'Small literal set/seat/string/dictionary models are bounded independently of complete normative domain validators. Large cases use analytic witnesses. No candidate time/space/asymptotic guarantee follows.',
 'observer_gap':'Existing stateful observer/adapter support not established. Do not feed oracle wire arguments to any candidate without separately reviewed interface authorization.',
 'transport':'Unchanged q.encoded/batches/LIMITS/MAX_FILE/MAX_PACKET. Some maximum operation streams exceed packet cap; omitted shapes stay in the validator domain.',
}


def lower(value,minimum=1,maximum=100):
    return type(value) is str and minimum<=len(value)<=maximum and set(value)<=set(string.ascii_lowercase)


def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=2:
        raise ValueError('unsupported state-machine identity/wire')
    ops,argv=args
    if not(type(ops) is list and type(argv) is list and 1<=len(ops)==len(argv)<=MAX_CALLS[pid]+1
           and ops[0]==CLASSES[pid] and type(argv[0]) is list and len(argv[0])==len(CONSTRUCTOR_PARAMETERS[pid])):
        raise ValueError('constructor or operation-count domain')
    init=argv[0]
    if pid==2227:
        keys,values,dictionary=init
        ok=(type(keys) is list and 1<=len(keys)<=26 and all(lower(c,1,1) for c in keys) and len(set(keys))==len(keys)
            and type(values) is list and len(values)==len(keys) and all(lower(v,2,2) for v in values)
            and type(dictionary) is list and 1<=len(dictionary)<=100 and all(lower(w) for w in dictionary) and len(set(dictionary))==len(dictionary))
    elif pid==2286:
        ok=integer(init[0],1,50000) and integer(init[1],1,10**9)
    elif pid==2353:
        foods,cuisines,ratings=init
        ok=(type(foods) is list and 1<=len(foods)<=20000 and all(lower(f,1,10) for f in foods) and len(set(foods))==len(foods)
            and type(cuisines) is list and len(cuisines)==len(foods) and all(lower(c,1,10) for c in cuisines)
            and ints(ratings,1,10**8,len(foods),len(foods)))
    else:
        ok=True
    if not ok:
        raise ValueError('constructor domain')
    deposited=0
    for op,a in zip(ops[1:],argv[1:]):
        if type(op) is not str or op not in METHODS[pid] or type(a) is not list or len(a)!=len(METHODS[pid][op]):
            raise ValueError('method or ordered method arguments')
        if pid==2227:
            ok=(lower(a[0],1,2000) and set(a[0])<=set(keys) if op=='encrypt'
                else lower(a[0],2,200) and len(a[0])%2==0)
        elif pid==2241:
            if op=='deposit':
                ok=ints(a[0],0,10**9,5,5)
                if ok:
                    deposited+=sum(a[0])
                    ok=deposited<=10**9
            else:
                ok=integer(a[0],1,10**9)
        elif pid==2276:
            ok=not a or (integer(a[0],1,10**9) and integer(a[1],a[0],10**9))
        elif pid==2286:
            ok=integer(a[0],1,10**9) and integer(a[1],0,init[0]-1)
        elif pid==2296:
            ok=lower(a[0],1,40) if op=='addText' else integer(a[0],1,40)
        elif pid==2336:
            ok=not a or integer(a[0],1,1000)
        elif pid==2349:
            ok=all(integer(v,1,10**9) for v in a)
        else:
            ok=(type(a[0]) is str and a[0] in foods and integer(a[1],1,10**8) if op=='changeRating'
                else type(a[0]) is str and a[0] in cuisines)
        if not ok:
            raise ValueError('method argument domain')
    if pid==2241 and not {'deposit','withdraw'}<=set(ops[1:]):
        raise ValueError('statement requires both deposit and withdraw')
    if pid==2276 and 'count' not in ops[1:]:
        raise ValueError('statement requires a count call')


def expected(pid,args):
    validate(pid,args)
    ops,argv=args
    if len(ops)>101:
        raise ValueError('reference operation bound, not domain restriction')
    init=argv[0]
    if pid==2227:
        keys,values,dictionary=init
        if len(dictionary)>12 or any(len(w)>20 for w in dictionary) or any(len(a[0])>20 for a in argv[1:]):
            raise ValueError('reference string/dictionary bound')
        table=dict(zip(keys,values))
    elif pid==2241:
        inventory=[0]*5
    elif pid==2276:
        if any(op=='add' and a[1]-a[0]>1000 for op,a in zip(ops[1:],argv[1:])):
            raise ValueError('reference explicit integer-set bound')
        covered=set()
    elif pid==2286:
        n,m=init
        if n*m>100:
            raise ValueError('reference explicit seat-grid bound')
        seats=[[False]*m for _ in range(n)]
    elif pid==2296:
        text=[]
        cursor=0
    elif pid==2336:
        available=set(range(1,1002))
    elif pid==2349:
        containers={}
    else:
        foods,cuisines,ratings=init
        if len(foods)>30:
            raise ValueError('reference food population bound')
        ratings=ratings[:]
    output=[None]
    for op,a in zip(ops[1:],argv[1:]):
        answer=None
        if pid==2227:
            word=a[0]
            if op=='encrypt':
                answer=''.join(table[c] for c in word)
            else:
                answer=sum(len(word)==2*len(candidate) and all(table.get(c)==word[2*i:2*i+2] for i,c in enumerate(candidate)) for candidate in dictionary)
        elif pid==2241:
            if op=='deposit':
                inventory=[x+y for x,y in zip(inventory,a[0])]
            else:
                remaining=a[0]
                taken=[0]*5
                for i,denomination in reversed(list(enumerate((20,50,100,200,500)))):
                    taken[i]=min(inventory[i],remaining//denomination)
                    remaining-=taken[i]*denomination
                if remaining:
                    answer=[-1]
                else:
                    inventory=[x-y for x,y in zip(inventory,taken)]
                    answer=taken
        elif pid==2276:
            if op=='add':
                covered.update(range(a[0],a[1]+1))
            else:
                answer=len(covered)
        elif pid==2286:
            k,maxrow=a
            free=[(r,c) for r in range(maxrow+1) for c in range(m) if not seats[r][c]]
            if op=='scatter':
                answer=len(free)>=k
                if answer:
                    for r,c in free[:k]:
                        seats[r][c]=True
            else:
                answer=[]
                for r in range(maxrow+1):
                    for c in range(m-k+1):
                        if not any(seats[r][c:c+k]):
                            answer=[r,c]
                            for j in range(c,c+k):
                                seats[r][j]=True
                            break
                    if answer:
                        break
        elif pid==2296:
            if op=='addText':
                text[cursor:cursor]=list(a[0])
                cursor+=len(a[0])
            elif op=='deleteText':
                answer=min(a[0],cursor)
                del text[cursor-answer:cursor]
                cursor-=answer
            else:
                cursor=max(0,cursor-a[0]) if op=='cursorLeft' else min(len(text),cursor+a[0])
                answer=''.join(text[max(0,cursor-10):cursor])
        elif pid==2336:
            if op=='addBack':
                available.add(a[0])
            else:
                answer=min(available)
                available.remove(answer)
        elif pid==2349:
            if op=='change':
                containers[a[0]]=a[1]
            else:
                answer=min((i for i,n in containers.items() if n==a[0]),default=-1)
        else:
            if op=='changeRating':
                ratings[foods.index(a[0])]=a[1]
            else:
                answer=min((i for i,c in enumerate(cuisines) if c==a[0]),key=lambda i:(-ratings[i],foods[i]))
                answer=foods[answer]
        output.append(answer)
    return output


EXAMPLES={
2227: [([['Encrypter','encrypt','decrypt'],[[['a','b','c','d'],['ei','zf','ei','am'],['abcd','acbd','adbc','badc','dacb','cadb','cbda','abad']],['abcd'],['eizfeiam']]],[None,'eizfeiam',2])],
2241: [([['ATM','deposit','withdraw','deposit','withdraw','withdraw'],[[],[[0,0,1,2,1]],[600],[[0,1,0,1,1]],[600],[550]]],[None,None,[0,0,1,0,1],None,[-1],[0,1,0,0,1]])],
2276: [([['CountIntervals','add','add','count','add','count'],[[],[2,3],[7,10],[],[5,8],[]]],[None,None,None,6,None,8])],
2286: [([['BookMyShow','gather','gather','scatter','scatter'],[[2,5],[4,0],[2,0],[5,1],[5,1]]],[None,[0,0],[],True,False])],
2296: [([['TextEditor','addText','deleteText','addText','cursorRight','cursorLeft','deleteText','cursorLeft','cursorRight'],[[],['leetcode'],[4],['practice'],[3],[8],[10],[2],[6]]],[None,None,4,None,'etpractice','leet',4,'','practi'])],
2336: [([['SmallestInfiniteSet','addBack','popSmallest','popSmallest','popSmallest','addBack','popSmallest','popSmallest','popSmallest'],[[],[2],[],[],[],[1],[],[],[]]],[None,None,1,2,3,None,1,4,5])],
2349: [([['NumberContainers','find','change','change','change','change','find','change','find'],[[],[10],[2,10],[1,10],[3,10],[5,10],[10],[1,20],[10]]],[None,-1,None,None,None,None,1,None,2])],
2353: [([['FoodRatings','highestRated','highestRated','changeRating','highestRated','changeRating','highestRated'],[[['kimchi','miso','sushi','moussaka','ramen','bulgogi'],['korean','japanese','japanese','greek','japanese','korean'],[9,12,8,15,14,7]],['korean'],['japanese'],['sushi',16],['japanese'],['ramen',16],['japanese']]],[None,'kimchi','ramen',None,'sushi',None,'ramen'])],
}


def _generate_cases(pid):
    cases,categories=[],[]
    sentinel=object()
    rng=random.Random(202610271844+pid)
    def add(init,steps,category,answer=sentinel):
        args=[[CLASSES[pid]]+[op for op,_ in steps],[init]+[a for _,a in steps]]
        validate(pid,args)
        cases.append({'args':args,'expected':expected(pid,args) if answer is sentinel else answer,'compare':'return'})
        categories.append(category)
    for args,answer in EXAMPLES[pid]:
        if not q.exact(expected(pid,args),answer):
            raise AssertionError('public example mismatch')
        add(args[1][0],list(zip(args[0][1:],args[1][1:])),'pinned_public_example',answer)
    if pid==2227:
        for n in range(1,4):
            keys=list('abc'[:n])
            dictionary=[''.join(chars) for width in (1,2) for chars in product(keys,repeat=width)]
            for values in product(('aa','ab','bb'),repeat=n):
                steps=[('encrypt',[w]) for w in dictionary]+[('decrypt',[w]) for w in ('aa','ab','bb','aaaa','abab','bbbb')]
                add([keys,list(values),dictionary],steps,'exhaustive_small_collision_mappings')
        add([['a'],['aa'],['a','z','aa','az']],[('decrypt',['aa']),('decrypt',['aaaa']),('decrypt',['zz'])],'dictionary_unencodable_characters')
        keys=list(string.ascii_lowercase)
        init=[keys,[c*2 for c in keys],['a'*i for i in range(1,101)]]
        steps=[('encrypt',['z'*2000])]+[('decrypt',['a'*200])]*199
        add(init,steps,'analytic_maximum_constructor_strings_and_calls',[None,'z'*4000]+[1]*199)
    elif pid==2241:
        for counts in product((0,1),repeat=5):
            for amount in (1,20,30,50,60,70,100,120,200,300,500,550,600,700,870):
                add([],[('deposit',[list(counts)]),('withdraw',[amount]),('withdraw',[amount]),('withdraw',[20])],'exhaustive_small_inventory_forced_greedy_and_rollback')
        add([],[('deposit',[[0,0,0,3,1]]),('withdraw',[600]),('withdraw',[500]),('withdraw',[600])],'greedy_rejection_despite_alternative_and_rollback')
        steps=[('deposit',[[10**9,0,0,0,0]])]+[('withdraw',[20])]*4999
        add([],steps,'analytic_maximum_calls_deposited_total',[None,None]+[[1,0,0,0,0] for _ in range(4999)])
        add([],[('deposit',[[0,0,0,0,2000000]]),('withdraw',[10**9]),('withdraw',[1])],'analytic_maximum_amount',[None,None,[0,0,0,0,2000000],[-1]])
    elif pid==2276:
        intervals=((1,1),(1,2),(2,2),(2,4),(1,4),(4,5))
        for width in range(1,4):
            for chosen in product(intervals,repeat=width):
                steps=[('count',[])]+[s for pair in chosen for s in (('add',list(pair)),('count',[]))]
                add([],steps,'exhaustive_short_interval_histories')
        add([],[('count',[]),('add',[1,10**9]),('count',[]),('add',[2,10**9-1]),('count',[])],'analytic_full_coordinate_union',[None,0,None,10**9,None,10**9])
        add([],[('count',[])]*50000,'analytic_large_empty_count_stream',[None]+[0]*50000)
    elif pid==2286:
        for n,m in ((1,1),(2,3),(3,2)):
            actions=[('gather',[1,0]),('gather',[m,n-1]),('gather',[m+1,n-1]),('scatter',[1,n-1]),('scatter',[n*m,n-1])]
            for steps in product(actions,repeat=4):
                add([n,m],list(steps),'exhaustive_small_seat_allocation_histories')
        add([50000,10**9],[('gather',[10**9,49999]),('gather',[1,0]),('scatter',[10**9,49999]),('gather',[1,49999])],'analytic_maximum_capacity_and_failure_rollback',[None,[0,0],[],True,[2,0]])
        add([1,10**9],[('gather',[1,0])]*50000,'analytic_maximum_method_calls',[None]+[[0,i] for i in range(50000)])
    elif pid==2296:
        actions=[('addText',['a']),('addText',['bc']),('deleteText',[3]),('cursorLeft',[1]),('cursorRight',[1]),('cursorRight',[40])]
        for width in range(1,5):
            for steps in product(actions,repeat=width):
                add([],list(steps),'exhaustive_small_editor_histories')
        add([],[('addText',['a'*40])]+[('cursorLeft',[40]),('cursorRight',[40])]*9999+[('deleteText',[40])],'analytic_maximum_calls_and_text_argument',[None,None]+['','a'*10]*9999+[40])
    elif pid==2336:
        actions=[('popSmallest',[]),('addBack',[1]),('addBack',[2]),('addBack',[1000])]
        for width in range(1,6):
            for steps in product(actions,repeat=width):
                add([],list(steps),'exhaustive_small_infinite_set_histories')
        add([],[('popSmallest',[])]*1000,'analytic_maximum_pop_count',[None]+list(range(1,1001)))
        add([],[('popSmallest',[]),('addBack',[1])]*500,'analytic_repeated_addback_idempotence',[None]+[x for _ in range(500) for x in (1,None)])
    elif pid==2349:
        actions=[('change',[1,1]),('change',[1,2]),('change',[2,1]),('find',[1]),('find',[2])]
        for width in range(1,5):
            for steps in product(actions,repeat=width):
                add([],list(steps),'exhaustive_small_number_container_histories')
        add([],[('change',[10**9,10**9]),('change',[1,10**9]),('find',[10**9]),('change',[1,1]),('find',[10**9])],'analytic_maximum_index_and_number',[None,None,None,1,None,10**9])
        add([],[('find',[10**9])]*40000,'analytic_large_absent_find_stream',[None]+[-1]*40000)
    else:
        actions=[('changeRating',['a',1]),('changeRating',['aa',3]),('changeRating',['a',3]),('highestRated',['x']),('highestRated',['y'])]
        for ratings in product((1,3),repeat=3):
            for steps in product(actions,repeat=3):
                add([['a','aa','b'],['x','x','y'],list(ratings)],list(steps),'exhaustive_rating_ties_prefix_names_and_updates')
        foods=[''.join(string.ascii_lowercase[(i//26**power)%26] for power in (3,2,1,0)) for i in range(20000)]
        add([foods,['x']*20000,[10**8]*20000],[('highestRated',['x']),('changeRating',[foods[0],1]),('highestRated',['x'])],'analytic_maximum_food_population_rating_tie',[None,foods[0],None,foods[1]])
        add([['abcdefghij'],['klmnopqrst'],[10**8]],[('highestRated',['klmnopqrst'])]*20000,'analytic_maximum_calls_and_name_lengths',[None]+['abcdefghij']*20000)
    # Fixed seeded mixed histories cover longer interactions without source feedback.
    if pid in (2241,2276,2286,2296,2336,2349,2353):
        for _ in range(80):
            if pid==2241:
                init=[]
                steps=[('deposit',[[rng.randrange(4) for _ in range(5)]]),('withdraw',[rng.randrange(1,1001)])]
                steps += [rng.choice([('deposit',[[rng.randrange(4) for _ in range(5)]]),('withdraw',[rng.randrange(1,2001)])]) for _ in range(20)]
            elif pid==2276:
                init=[]
                steps=[('count',[])]+[rng.choice([('count',[]),('add',sorted([rng.randrange(1,51),rng.randrange(1,51)]))]) for _ in range(20)]
            elif pid==2286:
                init=[rng.randrange(1,6),rng.randrange(1,6)]
                steps=[(rng.choice(('gather','scatter')),[rng.randrange(1,15),rng.randrange(init[0])]) for _ in range(20)]
            elif pid==2353:
                init=[['a','aa','b'],['x','x','y'],[rng.randrange(1,10) for _ in range(3)]]
                steps=[rng.choice([('changeRating',[rng.choice(init[0]),rng.randrange(1,10)]),('highestRated',[rng.choice(('x','y'))])]) for _ in range(20)]
            else:
                init=[]
                steps=[rng.choice(actions) for _ in range(30)]
            add(init,steps,'seeded_longer_state_histories')
    return cases,categories


def build_cases(pid,statement):
    if pid not in IDS or type(statement) is not bytes or q.sha(statement)!=DEFINITION_SHA256[pid]:
        raise ValueError('exact freshly gated public definition required')
    definition=json.loads(statement)
    if definition['problem_id']!=pid or f'{pid}. {TITLES[pid]}' not in str(definition['web_result']):
        raise ValueError('definition identity mismatch')
    cases,categories=_generate_cases(pid)
    if len(q.encoded(cases))>q.MAX_FILE:
        raise ValueError('unchanged file cap exceeded')
    for _,batch in q.batches(cases):
        for language in ('python','javascript'):
            size=sum(len(q.encoded({'i':i,'result':c['expected'],'result_type':q.expected_type(c['expected'],language),
                                    'args_before':c['args'],'args_after':c['args'],'alias_edges':[]})) for i,c in enumerate(batch))
            if size+len(q.encoded({'done':len(batch)}))+1>q.LIMITS['max_output_bytes']:
                raise ValueError('unchanged output cap exceeded')
    return cases,categories
