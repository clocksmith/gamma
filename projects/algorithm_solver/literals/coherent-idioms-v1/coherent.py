"""Bounded, exact-byte coherent idiom proposals. No input source is executed."""
import ast
from collections import defaultdict
import hashlib
import importlib.util
import json
import io
import tokenize
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('coherent_shapes', HERE.parent / 'macro-fragment-compare-v1/shapes.py')
_shapes = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_shapes)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_sources(records, language):
    if language not in ('python', 'javascript'):
        raise ValueError('language must be python or javascript')
    if not records or len(records) > 1024:
        raise ValueError('source count must be 1..1024')
    if sum(len(r['source'].encode()) for r in records.values()) > 8 * 1024 * 1024:
        raise ValueError('aggregate source byte budget exceeded')
    for key, r in records.items():
        raw = r['source'].encode('utf-8')
        if len(raw) > 262144 or r['sha256'] != digest(raw):
            raise ValueError('source size/hash mismatch: ' + key)
        # Receipts are caller-supplied bindings, not inferred judge acceptance.
        q = r.get('qualification')
        if q is not None and (q.get('source_sha256') != r['sha256'] or
                              not re.fullmatch('[0-9a-f]{64}', q.get('receipt_sha256', '')) or
                              not q.get('contract') or q.get('status') != 'passed'):
            raise ValueError('invalid qualification binding: ' + key)


def metadata(records, language):
    validate_sources(records, language)
    shapes, errors = _shapes.shapes({k: r['source'] for k, r in records.items()}, language)
    if errors:
        raise ValueError('parse failures: ' + repr(errors))
    if language == 'javascript':
        run = subprocess.run(['node','--expose-internals',str(HERE/'js_families.cjs')],
            input=json.dumps({k:r['source'] for k,r in records.items()}),text=True,
            capture_output=True,check=True,timeout=60)
        parsed=json.loads(run.stdout)
        for key, shape in shapes.items():
            shape['coherent_proposals']=parsed[key]['spans']
            shape['tokens']=sorted(shape['tokens']+parsed[key]['comments'])
    else:
        for key,shape in shapes.items():
            source=records[key]['source']; lines=_shapes.python_physical_lines(source); starts=[0]
            for line in lines: starts.append(starts[-1]+len(line.encode()))
            for token in tokenize.generate_tokens(io.StringIO(source).readline):
                if token.type != tokenize.COMMENT: continue
                def byte(pos): return starts[pos[0]-1]+len(lines[pos[0]-1][:pos[1]].encode())
                shape['tokens'].append((byte(token.start),byte(token.end)))
            shape['tokens'].sort()
    return shapes


def _proposals(raw, shape, language, extra=()):
    tokens = shape['tokens']
    nodes = shape['nodes']
    yield from extra
    for a, b, children, kind in nodes:
        if kind in ('ForStatement','ForOfStatement','ForInStatement','WhileStatement') and language == 'javascript':
            if children:
                body_start = children[-1][0]
                yield a, body_start + (raw[body_start:body_start+1] == b'{'), 'loop_opening'
        if language == 'python' and kind == 'AugAssign':
            yield a, b, 'accumulator_update'
        if language == 'javascript' and kind == 'ExpressionStatement':
            if any(x == a and y <= b and k == 'AssignmentExpression' for x,y,c,k in nodes):
                if re.match(rb'\s*[^;]+(?:\+=|-=|\*=|/=|%=)', raw[a:b]):
                    yield a, b, 'accumulator_update'
    if language == 'python':
        source = raw.decode('utf-8'); starts = [0]
        for line in _shapes.python_physical_lines(source): starts.append(starts[-1]+len(line.encode()))
        tree=ast.parse(source)
        token_pairs=set(map(tuple,tokens))
        def span(node):
            return starts[node.lineno-1]+node.col_offset, starts[node.end_lineno-1]+node.end_col_offset
        for node in ast.walk(tree):
            kinds = {ast.For:'loop_opening', ast.While:'loop_opening', ast.AsyncFor:'loop_opening',
                     ast.FunctionDef:'function_opening', ast.AsyncFunctionDef:'function_opening',
                     ast.If:'condition_opening', ast.With:'context_opening', ast.AsyncWith:'context_opening'}
            if type(node) not in kinds: continue
            a = starts[node.lineno-1]+node.col_offset
            first = node.body[0]; body_start = starts[first.lineno-1]+first.col_offset
            # The final colon preceding the first actual suite statement is the
            # opening colon, even with lambdas, slices or multiline headers.
            colons = [y for x,y in tokens if a<=x<body_start and raw[x:y]==b':']
            if colons: yield a,max(colons),kinds[type(node)]
        for node in ast.walk(tree):
            if not getattr(node,'end_lineno',None): continue
            a,b=span(node)
            if isinstance(node,(ast.Name,ast.Constant)) and (a,b) in token_pairs:
                if len(raw[a:b].decode())>=2: yield a,b,'lexical_operand'
            if isinstance(node,(ast.Return,ast.Raise,ast.Await,ast.Yield,ast.UnaryOp)):
                value=getattr(node,'value',None) or getattr(node,'exc',None) or getattr(node,'operand',None)
                if value: yield a,span(value)[0],'keyword_or_unary_opening'
            left=right=None
            if isinstance(node,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
                left=node.targets[-1] if isinstance(node,ast.Assign) else node.target
                right=node.value
            elif isinstance(node,ast.BinOp): left,right=node.left,node.right
            if left is not None and right is not None:
                yield a,span(right)[0],'operation_left_phrase'
                yield span(left)[1],b,'operation_right_phrase'
                yield span(left)[1],span(right)[0],'operation_operator'
            if isinstance(node,ast.Compare):
                operands=[node.left]+node.comparators
                for left,right in zip(operands,operands[1:]):
                    yield span(left)[0],span(right)[0],'comparison_left_phrase'
                    yield span(left)[1],span(right)[1],'comparison_right_phrase'
                    yield span(left)[1],span(right)[0],'comparison_operator'
            if isinstance(node,ast.BoolOp):
                for left,right in zip(node.values,node.values[1:]):
                    yield span(left)[1],span(right)[0],'boolean_operator'
            if isinstance(node,ast.Call):
                opening=next(((x,y) for x,y in tokens if x>=span(node.func)[1] and y<=b and raw[x:y]==b'('),None)
                if opening: yield a,opening[1],'call_opening'
                arguments=node.args+node.keywords
                if arguments: yield max(span(arg)[1] for arg in arguments),b,'call_closing'
            if isinstance(node,ast.Attribute): yield span(node.value)[1],b,'member_operation'
            if isinstance(node,ast.Subscript):
                yield a,span(node.slice)[0],'index_opening'
                yield span(node.slice)[1],b,'index_closing'
            if isinstance(node,(ast.If,ast.While)): yield a,span(node.test)[0],'condition_constructor'
            if isinstance(node,(ast.For,ast.AsyncFor)): yield a,span(node.iter)[0],'loop_constructor'
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                body_start=span(node.body[0])[0]
                opening=next(((x,y) for x,y in tokens if a<=x<body_start and raw[x:y]==b'('),None)
                colons=[y for x,y in tokens if a<=x<body_start and raw[x:y]==b':']
                if opening and colons:
                    yield a,opening[1],'function_constructor'
                    args=node.args.posonlyargs+node.args.args+node.args.kwonlyargs
                    args += [x for x in (node.args.vararg,node.args.kwarg) if x is not None]
                    if args:
                        yield min(span(arg)[0] for arg in args),max(colons),'parameter_bindings'
                        # Token-owned closing delimiters, excluding defaults/annotations.
                        depth=1
                        for x,y in tokens:
                            if x<opening[1] or x>=body_start: continue
                            if raw[x:y]==b'(': depth+=1
                            elif raw[x:y]==b')': depth-=1
                            if depth==0:
                                yield x,max(colons),'function_header_closing'
                                break
        families = {'Return':'return_statement','Assign':'declaration','AnnAssign':'declaration',
                    'Expr':'expression_statement','Raise':'throw_statement','Break':'control_statement',
                    'Continue':'control_statement','Call':'call_expression','BinOp':'binary_expression',
                    'BoolOp':'binary_expression','Compare':'binary_expression','IfExp':'conditional_expression',
                    'List':'collection_expression','Dict':'collection_expression','Set':'collection_expression',
                    'Tuple':'collection_expression','Subscript':'index_expression','Attribute':'member_expression'}
        for a,b,children,kind in nodes:
            if kind in families: yield a,b,families[kind]
    # Structural glue is explicitly separate from idioms; no lexical alphabet.
    # It includes standalone delimiters and exact whitespace runs, charged as entries.
    for a,b in tokens:
        if raw[a:b] in (b'{',b'}',b'(',b')',b'[',b']',b',',b';',b':'):
            yield a,b,'structural_glue'
    pos = 0
    for a,b in tokens:
        if a > pos and raw[pos:a].isspace(): yield pos,a,'structural_glue'
        pos = b
    if pos < len(raw) and raw[pos:].isspace(): yield pos,len(raw),'structural_glue'


def _with_exact_joins(raw, shape, proposals):
    """Preserve whole-token bounds; never disguise lexical singleton entries.

    Attach contiguous formatting and immediate delimiter joins to a grammar-owned
    phrase. Joins stop before the next lexical/operator token or comment. This
    makes closing punctuation chargeable with a statement without a char mode.
    """
    tokens = shape['tokens']; starts = {a:i for i,(a,b) in enumerate(tokens)}
    ends = {b:i for i,(a,b) in enumerate(tokens)}
    delimiters = {b')',b']',b'}',b';',b',',b':'}
    for a,b,kind in proposals:
        yield a,b,kind
        if kind == 'structural_glue' or len(raw[a:b].strip()) <= 1: continue
        before=a; after=b
        while before>0 and raw[before-1:before].isspace(): before-=1
        while after<len(raw) and raw[after:after+1].isspace(): after+=1
        for x,y in ((before,b),(a,after),(before,after)):
            if (x,y)!=(a,b): yield x,y,kind
        first=starts.get(a)
        if first is not None and first>0:
            x,y=tokens[first-1]
            if raw[x:y] in delimiters and (not raw[y:a] or raw[y:a].isspace()):
                yield x,b,kind+'_leading_join'
                yield x,after,kind+'_leading_join'
        index=ends.get(b)
        if index is None: continue
        end=b
        # At most four punctuation tokens, each charged as part of the literal.
        for x,y in tokens[index+1:index+5]:
            if raw[end:x] and not raw[end:x].isspace(): break
            if raw[x:y] not in delimiters: break
            end=y
            spaced=end
            while spaced<len(raw) and raw[spaced:spaced+1].isspace(): spaced+=1
            for start in (a,before):
                yield start,end,kind+'_joined'
                yield start,spaced,kind+'_joined'


def _global_banned_spans(raw, safe, banned):
    """Find whole banned units only at this source's lexical boundaries.

    A banned 'return total' must reject 'return total;' but not 'return totals'
    or text inside a string/comment token. Empty formatting is never a unit.
    """
    spans=set()
    for unit in banned:
        if not unit or len(unit)>len(raw): continue
        start=raw.find(unit)
        while start>=0:
            end=start+len(unit)
            if start in safe and end in safe: spans.add((start,end))
            start=raw.find(unit,start+1)
    return sorted(spans)


def enumerate_candidates(records, language):
    shapes = metadata(records, language)
    pool = {}
    banned = set()
    for key, r in records.items():
        raw = r['source'].encode()
        banned.add(raw.strip())
        banned.update(raw[a:b].strip() for a,b in shapes[key]['banned'])
    for key, r in sorted(records.items()):
        raw = r['source'].encode()
        seen = set()
        safe = _safe_boundaries(raw,shapes[key])
        banned_spans = _global_banned_spans(raw,safe,banned)
        proposals = list(_proposals(raw, shapes[key], language, shapes[key].get('coherent_proposals',())))
        for a,b,kind in _with_exact_joins(raw, shapes[key], proposals):
            text = raw[a:b]
            if not text or len(text) > 160: continue
            if a not in safe or b not in safe:
                raise ValueError('proposal cuts a lexical token or UTF-8 character: '+key)
            if any(a <= x and b >= y for x,y in banned_spans): continue
            if kind != 'structural_glue' and len(text.strip()) < 2: continue
            identity = (text,kind)
            if (a,b,kind) in seen: continue
            seen.add((a,b,kind))
            if len(seen) > 8192: raise ValueError('per-source candidate budget exceeded')
            c = pool.setdefault(identity, {'id':digest(language.encode()+b'\0'+kind.encode()+b'\0'+text),
                'language':language,'literal':text.decode(),'kind':kind,'state':'generated',
                'provenance':[], 'evidence':{'primitive':None,'source_qualification':'caller-bound receipts only',
                'unseen_solving':False}})
            if len(pool) > 250000: raise ValueError('candidate pool budget exceeded')
            c['provenance'].append({'source_id':key,'problem_id':r.get('problem_id'),'source_sha256':r['sha256'],
                'start_byte':a,'end_byte':b,'qualification':r.get('qualification')})
    for c in pool.values():
        owners = {p['source_sha256'] for p in c['provenance'] if p['qualification']}
        problems = {p['problem_id'] for p in c['provenance'] if p['qualification'] and p['problem_id']}
        c['receipt_bound_distinct_sources'] = len(owners)
        c['receipt_bound_distinct_problems'] = len(problems)
        if len(owners) >= 2 and len(problems) >= 2: c['state'] = 'promising'
    return sorted(pool.values(), key=lambda c:c['id'])


def promote(candidate):
    """Return copied candidate with local evidence; never execute mined source."""
    from verifier import verify_accumulator
    c = json.loads(json.dumps(candidate))
    if c['state'] != 'promising' or c['kind'] != 'accumulator_update': return c
    evidence = verify_accumulator(c['literal'], c['language'])
    c['evidence']['primitive'] = evidence
    if evidence and evidence['passed']: c['state'] = 'trusted'
    return c


def select_table(candidates, language, width, states=('promising','trusted'), policy='strict', records=None, _parsed=None):
    if width not in (6,7,8): raise ValueError('width must be 6, 7, or 8')
    if policy not in ('strict','charged_glue_diagnostic'): raise ValueError('invalid policy')
    # Deterministic shortlist, not an optimization or completeness claim.
    selected = [c for c in candidates if c['language'] == language and c['state'] in states
                and (len(c['literal'].strip()) > 1 or (policy == 'charged_glue_diagnostic' and c['kind'] == 'structural_glue'))]
    selected.sort(key=lambda c:(-len(c['literal'].encode())*len(c['provenance']),c['id']))
    unique = {}
    for c in selected: unique.setdefault(c['literal'],c)
    ranked = list(unique.values())
    if records is None:
        entries = ranked[:2**width]
        method = 'deterministic_frequency_shortlist_not_independent_optimization'
    else:
        parsed = metadata(records, language) if _parsed is None else _parsed
        entries = _reachability_seed(records, parsed, ranked, 2**width)
        method = 'width_specific_complementary_complete_path_greedy_not_global_optimum'
    return {'language':language,'width':width,'capacity':2**width,'entries':entries,
            'policy':policy,'selection_method':method,
            'stored_utf8_bytes':sum(len(c['literal'].encode()) for c in entries),
            'mapping_sha256':digest(json.dumps([c['literal'] for c in entries],ensure_ascii=False).encode())}


def _safe_boundaries(raw, shape):
    safe = set(range(len(raw)+1))
    for a,b in shape['tokens']: safe.difference_update(range(a+1,b))
    points = {0}; offset = 0
    for char in raw.decode():
        offset += len(char.encode()); points.add(offset)
    return safe & points


def _reachability_seed(records, parsed, ranked, capacity):
    """Minimum-selection paths provide complementary bundles, not free operands.

    Every width gets its own bounded greedy coverage search. Unreachable inputs
    stay in the final denominator. No source literal is synthesized by selection.
    """
    trie = {}
    for code,c in enumerate(ranked):
        node = trie
        for byte in c['literal'].encode(): node = node.setdefault(byte,{})
        node[None] = code
    bundles = []
    for key,r in sorted(records.items()):
        raw = r['source'].encode(); n=len(raw); safe=_safe_boundaries(raw,parsed[key])
        costs={0:0}; previous={}
        for i in range(n):
            if i not in costs: continue
            node=trie; j=i
            while j<n and raw[j] in node:
                node=node[raw[j]]; j+=1
                if None in node and j in safe and costs[i]+1 < costs.get(j,n+1):
                    costs[j]=costs[i]+1; previous[j]=(i,node[None])
        if n not in costs: continue
        codes=set(); j=n
        while j:
            i,code=previous[j]; codes.add(code); j=i
        if len(codes)<=capacity: bundles.append(frozenset(codes))
    chosen=set()
    while True:
        options=[]
        for bundle in bundles:
            delta=bundle-chosen
            if not delta or len(chosen|bundle)>capacity: continue
            trial=chosen|bundle
            gain=sum(b<=trial and not b<=chosen for b in bundles)
            options.append((-gain/len(delta),len(delta),tuple(sorted(bundle)),bundle))
        if not options: break
        chosen.update(min(options,key=lambda x:x[:3])[3])
    # Fill unused budget with grammar-owned candidates only. This cannot undo
    # reachability already secured by the complete-path bundles.
    for i in range(len(ranked)):
        if len(chosen)>=capacity: break
        chosen.add(i)
    return [ranked[i] for i in sorted(chosen)]


def segment(source, table, _shape=None):
    """Minimum selections or explicit uncovered intervals. No escape or remapping."""
    raw = source.encode(); n = len(raw)
    shape = _shape if _shape is not None else metadata({'input':{'source':source,'sha256':digest(raw)}},table['language'])['input']
    safe = _safe_boundaries(raw, shape)
    entries = [c['literal'].encode() for c in table['entries']]
    if table['width'] not in (6,7,8) or len(entries)>2**table['width'] or any(not x for x in entries):
        raise ValueError('invalid table')
    trie = {}
    for code, piece in enumerate(entries):
        node = trie
        for byte in piece: node = node.setdefault(byte, {})
        node[None] = code
    # Optimize covered bytes first, then entry count; skipped bytes stay visibly uncovered.
    best = [(n+1,n+1)]*(n+1); best[0]=(0,0); previous={}
    for i in range(n):
        if best[i][0] > n: continue
        choices = [(i+1,(best[i][0]+1,best[i][1]),None)]
        if i in safe:
            node = trie; j = i
            while j < n and raw[j] in node:
                node = node[raw[j]]; j += 1
                if None in node and j in safe:
                    choices.append((j,(best[i][0],best[i][1]+1),node[None]))
        for j,cost,code in choices:
            if cost<best[j]: best[j]=cost; previous[j]=(i,code)
    spans=[]; j=n
    while j:
        i,code=previous[j]; spans.append({'start_byte':i,'end_byte':j,'code':code}); j=i
    spans.reverse()
    uncovered=[]
    for s in spans:
        if s['code'] is None:
            if uncovered and uncovered[-1][1]==s['start_byte']: uncovered[-1][1]=s['end_byte']
            else: uncovered.append([s['start_byte'],s['end_byte']])
    complete=not uncovered
    singleton_selections = sum(s['code'] is not None and len(table['entries'][s['code']]['literal'].strip()) <= 1 for s in spans)
    return {'complete':complete,'uncovered_byte_ranges':uncovered,'uncovered_bytes':best[n][0],
            'selections':best[n][1], 'singleton_selections':singleton_selections,
            'singleton_selection_bits':singleton_selections*table['width'],
            'singleton_selection_fraction':singleton_selections/best[n][1] if best[n][1] else 0, 'selection_bits':best[n][1]*table['width'],
            'complete_program_bits':best[n][1]*table['width'] if complete else None,
            'dictionary_storage_bits':table['stored_utf8_bytes']*8,'spans':spans,
            'framing':'source length and dictionary identity required externally; not a wire codec'}


def evaluate_tables(records, language, candidates=None, states=('promising','trusted'), policy='strict'):
    """FIT-ONLY selection and measurement. Never pass reserved validation sources.

    Even when candidates are supplied, records guide selection. Use
    evaluate_fixed_table for a frozen transfer evaluation with no reselection.
    """
    validate_sources(records, language)
    candidates = enumerate_candidates(records, language) if candidates is None else candidates
    parsed = metadata(records, language)
    reports = {}
    for width in (6,7,8):
        table = select_table(candidates, language, width, states, policy, records, parsed)
        programs = {}
        for key,r in sorted(records.items()):
            result = segment(r['source'], table, parsed[key])
            programs[key] = {**result, 'source_sha256':r['sha256'],
                'reason':None if result['complete'] else 'exact table cannot cover every source byte; no fallback'}
        reports[width] = {'table':table,'programs':programs,
            'total_programs':len(records),
            'complete_programs':sum(p['complete'] for p in programs.values()),
            'source_bytes':sum(len(r['source'].encode()) for r in records.values()),
            'uncovered_bytes':sum(p['uncovered_bytes'] for p in programs.values()),
            'evidence_scope':'known-source representation only; not autonomous solving'}
    return reports


def validate_table(table):
    """Validate frozen mapping structure, not external receipt authenticity."""
    language=table['language']; width=table['width']; entries=table['entries']
    if language not in ('python','javascript') or type(width) is not int or width not in (6,7,8):
        raise ValueError('invalid table language/width')
    if table.get('capacity') != 2**width or len(entries)>2**width:
        raise ValueError('invalid table capacity')
    if table.get('policy') not in ('strict','charged_glue_diagnostic'):
        raise ValueError('invalid table policy')
    ids=set(); literals=set()
    for entry in entries:
        literal=entry['literal']; kind=entry['kind']
        if not isinstance(literal,str) or not literal or len(literal.encode())>160:
            raise ValueError('invalid literal size')
        identity=digest(language.encode()+b'\0'+kind.encode()+b'\0'+literal.encode())
        if entry['id']!=identity or entry['language']!=language or entry['id'] in ids or literal in literals:
            raise ValueError('invalid or duplicate entry identity')
        if entry['state'] not in ('generated','promising','trusted'):
            raise ValueError('invalid evidence state')
        if len(literal.strip())<=1 and (table['policy']=='strict' or kind!='structural_glue'):
            raise ValueError('singleton outside charged glue diagnostic')
        ids.add(entry['id']); literals.add(literal)
    if table['stored_utf8_bytes']!=sum(len(e['literal'].encode()) for e in entries):
        raise ValueError('dictionary storage mismatch')
    mapping=digest(json.dumps([e['literal'] for e in entries],ensure_ascii=False).encode())
    if table['mapping_sha256']!=mapping:
        raise ValueError('dictionary mapping hash mismatch')


def evaluate_fixed_table(records, table):
    """Read-only transfer evaluation; never mines candidates or reselects entries."""
    validate_table(table)
    parsed=metadata(records,table['language']) if records else {}
    programs={}
    for key,r in sorted(records.items()):
        result=segment(r['source'],table,parsed[key])
        programs[key]={**result,'source_sha256':r['sha256'],
            'reason':None if result['complete'] else 'frozen exact table cannot cover every source byte; no fallback'}
    return {'mapping_sha256':table['mapping_sha256'],'width':table['width'],
        'policy':table['policy'],'selection_performed':False,'programs':programs,
        'total_programs':len(records),'complete_programs':sum(p['complete'] for p in programs.values()),
        'source_bytes':sum(len(r['source'].encode()) for r in records.values()),
        'uncovered_bytes':sum(p['uncovered_bytes'] for p in programs.values()),
        'evidence_scope':'frozen known-source representation transfer only; no source qualification or unseen solving',
        'qualification_receipt_scope':'caller-bound metadata only; authenticity not verified here'}
