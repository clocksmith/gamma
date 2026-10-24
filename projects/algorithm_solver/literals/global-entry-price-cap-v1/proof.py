"""Item66 explicit tiny proof oracle; no loader, tuning or scalable kernel.

The unchanged item57 tiny oracle supplies only the comparison certificate and
relaxed path value. Global multiplicities and all-entry residual schedules are
constructed here from every allowed exact occurrence.
"""
import importlib.util
from pathlib import Path

_spec=importlib.util.spec_from_file_location('global66_parent57',Path(__file__).resolve().parents[1]/'owner-path-cap-v1/proof.py')
parent=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(parent)


def certificate(texts,banned,q,lambdas,capacity=256,denominator=1):
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(texts) is dict and texts
    assert all(type(pid) is str and type(text) is str and text for pid,text in texts.items())
    assert type(capacity) is int and capacity>=0
    assert type(denominator) is int and denominator>0
    assert type(lambdas) is list and lambdas
    assert all(type(value) is int and value>=0 for value in lambdas)
    assert lambdas==sorted(set(lambdas)) and lambdas[0]==0
    assert not isinstance(banned,(str,bytes))
    banned=set(banned);assert all(type(word) is str and word for word in banned)
    assert type(q) is dict
    for edge,value in q.items():
        assert type(edge) is tuple and len(edge)==3 and type(edge[0]) is str
        assert type(edge[1]) is type(edge[2]) is int
        assert type(value) is int and value>=0
    edges={(pid,start,end):text[start:end] for pid,text in sorted(texts.items())
           for start in range(len(text)) for end in range(start+1,len(text)+1)
           if text[start:end] not in banned}
    assert set(q)==set(edges),'q must contain exactly every allowed occurrence'
    counts={word:0 for word in sorted(set(edges.values()))}
    for word in edges.values():counts[word]+=1
    assert all(value>0 for value in counts.values())
    base=parent.certificate(texts,banned,q,capacity,denominator)
    incoming={pid:[[] for _ in range(len(text)+1)] for pid,text in sorted(texts.items())}
    arcs=[]
    for (pid,start,end),word in edges.items():
        residuals=[max(q[pid,start,end]-price//counts[word],0) for price in lambdas]
        arc={'pid':pid,'start':start,'end':end,'word':word,'q':q[pid,start,end],
             'multiplicity':counts[word],'residuals':residuals}
        arcs.append(arc);incoming[pid][end].append(arc)
    schedules={};caps={}
    for pid,text in sorted(texts.items()):
        schedules[pid]=[];caps[pid]=[]
        for index,price in enumerate(lambdas):
            values=[0]*(len(text)+1)
            for end in range(1,len(text)+1):
                values[end]=max([values[end-1]]+[values[a['start']]+a['residuals'][index] for a in incoming[pid][end]])
            schedules[pid].append(values);caps[pid].append(values[-1])
    price_rows=[]
    for index,price in enumerate(lambdas):
        residual_cap=sum(values[index] for values in caps.values())
        charge=price*capacity+residual_cap;numerator=base['L']-charge
        price_rows.append({'lambda':price,'residual_cap':residual_cap,'charge':charge,
                           'numerator':numerator,'integer_lower_bound':-(-numerator//denominator)})
    winner=min(range(len(price_rows)),key=lambda i:(price_rows[i]['charge'],lambdas[i]))
    global_row=dict(price_rows[winner],price_index=winner)
    rows=[]
    for old in base['rows']:
        charge=min(old['charge'],global_row['charge']);numerator=base['L']-charge
        rows.append({'k':old['k'],'charge':charge,'baseline57_charge':old['charge'],
                     'global_charge':global_row['charge'],'numerator':numerator,
                     'integer_lower_bound':-(-numerator//denominator),
                     'charge_reduction_vs57':old['charge']-charge})
    return {'base57':base,'capacity':capacity,'denominator':denominator,
            'lambda_family':list(lambdas),'entry_occurrence_counts':counts,
            'arcs':arcs,'price_schedules':schedules,'price_caps':caps,
            'price_rows':price_rows,'global':global_row,'rows':rows}
