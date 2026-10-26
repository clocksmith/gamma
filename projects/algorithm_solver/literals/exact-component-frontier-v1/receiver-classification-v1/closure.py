"""Aggregate fixed metadata call closure, never a semantic admission predicate."""
CORE={'member/array_literal/'+m for m in ('push','pop')}|{'member/new_Map/'+m for m in ('get','set','has')}|{'member/new_Set/'+m for m in ('add','has','delete')}
MATH={'member/global_Math/min','member/global_Math/max'}
GLOBALS={'Math','Map','Set','undefined','Infinity','NaN'}
def container_shape_upper_bound(row):
 c=row['counts'];calls={k for k in c if k.startswith(('member/','direct/','call/'))}
 return bool(calls&CORE) and calls<=CORE|MATH and not any(k.startswith('risk/')for k in c) and not any(k.startswith('constructor/') and k not in {'constructor/new_Map','constructor/new_Set'}for k in c) and not any(k.startswith('global_reference/')and k.split('/')[1]not in GLOBALS for k in c)
def aggregate(rows):
 selected=[r for r in rows if container_shape_upper_bound(r)]
 return dict(variants=len(selected),owners=len({r['problem_id']for r in selected}),source_bytes=sum(r['source_bytes']for r in selected),source_identities=[{k:r[k]for k in ('key','problem_id','source_sha256','source_bytes')}for r in selected],admitted=0,initializer_dominance_measured=False,limitation='Requiring an actual container call excludes Math-only rows; initializer shape is not a type/definite-initialization/alias proof. Source-specific review required.')
