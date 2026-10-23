"""Standard-library, fixed-menu Python renderings; no loaders or execution.

AST identity excludes location attributes. Exact literal source spans are also
preserved, including complete formatted/template strings and their debug labels.
These structural checks do not replace strict behavioral qualification.
"""
import ast
import functools
import hashlib
import io
import os
import tokenize

if not __debug__ or 'PYTHONOPTIMIZE' in os.environ:
    raise RuntimeError('Normal Python assertion checks are required')

ALPHABET=frozenset(chr(i) for i in range(32,127))|{'\n'}
MAX_BYTES=65536
MAX_NODES=20000
MAX_TOKENS=40000
ALLOWED_IMPORTS=frozenset({'math','collections','heapq','bisect','itertools','functools',
                          'operator','statistics','string','typing','array','__future__'})
SAFE_TYPING=frozenset({'Any','List','Dict','Tuple','Set','FrozenSet','Optional','Union','Iterable',
    'Iterator','Sequence','Mapping','MutableMapping','Collection','Container','Callable',
    'Deque','DefaultDict','Counter','Literal','Final','ClassVar','NoReturn','Never','Self',
    'Type','TypeVar','Generic','Protocol','Hashable','Sized','Reversible','AbstractSet'})
REFLECTION=frozenset({
    'eval','exec','compile','locals','globals','vars','dir','getattr','setattr','delattr',
    '__import__','attrgetter','methodcaller','open','input','breakpoint','help',
    'format','format_map','Formatter','get_type_hints','ForwardRef','evaluate_forward_ref',
    '_eval_type','_evaluate',
    'inspect','traceback','linecache','dis','marshal','pickle','sys','types','gc',
    'ast','tokenize','code','builtins','importlib','import_module',
    '_getframe','currentframe','getsource','getsourcelines','findsource','getfile',
    'getsourcefile','getframeinfo','getouterframes','getinnerframes','stack','trace',
    'extract_stack','extract_tb','format_stack','format_tb','format_exc','print_stack',
    'print_tb','print_exc','StackSummary','TracebackException','getline','getlines',
    'gettrace','settrace','getprofile','setprofile','excepthook','breakpointhook',
    'f_locals','f_globals','f_code','f_lineno','f_lasti','f_back','tb_frame','tb_lineno',
    'tb_lasti','tb_next','gi_frame','cr_frame','ag_frame','gi_code','cr_code','ag_code',
    'co_code','co_consts','co_linetable','co_lnotab','co_lines','co_positions',
    'co_firstlineno','co_filename','co_stacksize','get_instructions','findlinestarts',
    'signature','getmembers','get_annotations','getclosurevars'})
FORMATTED=(ast.JoinedStr,)+((ast.TemplateStr,) if hasattr(ast,'TemplateStr') else ())
ASYNC=(ast.AsyncFunctionDef,ast.AsyncFor,ast.AsyncWith,ast.Await,ast.Yield,ast.YieldFrom)


def parse(text):
    tree=ast.parse(text,filename='candidate.py',type_comments=True)
    compile(tree,'candidate.py','exec')
    return tree


def fingerprint(tree):
    return ast.dump(tree,annotate_fields=True,include_attributes=False)


def unsafe_reason(text,tree):
    if not set(text)<=ALPHABET:return 'outside_literal_alphabet'
    if len(text.encode())>MAX_BYTES:return 'source_byte_limit'
    nodes=list(ast.walk(tree))
    if len(nodes)>MAX_NODES:return 'ast_node_limit'
    typing_aliases={a.asname or a.name for n in nodes if isinstance(n,ast.Import)
                    for a in n.names if a.name=='typing'}
    for n in nodes:
        if isinstance(n,(ast.Try,ast.TryStar)):
            return 'exception_handler_observability'
        if isinstance(n,ASYNC):return 'suspended_frame_observability'
        if isinstance(n,ast.TypeIgnore) or getattr(n,'type_comment',None):return 'type_comment'
        annotations=[getattr(n,key,None) for key in ('annotation','returns')]
        if any(isinstance(t,ast.Constant) and isinstance(t.value,str)
               for a in annotations if a is not None for t in ast.walk(a)):
            return 'string_annotation_observability'
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            if n.decorator_list or getattr(n,'type_params',[]):return 'decorator_or_type_parameters'
            if isinstance(n,ast.ClassDef) and n.keywords:return 'class_keyword_metaprogramming'
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            if isinstance(n,ast.ImportFrom) and n.module=='__future__' and any(a.name=='annotations' for a in n.names):
                return 'stringified_annotation_observability'
            modules=([n.module or ''] if isinstance(n,ast.ImportFrom) else [a.name for a in n.names])
            if getattr(n,'level',0) or any(m.split('.')[0] not in ALLOWED_IMPORTS for m in modules):
                return 'unapproved_import'
            if any(a.name=='*' or a.name.rsplit('.',1)[-1] in REFLECTION for a in n.names):
                return 'dynamic_or_reflection_import'
            if isinstance(n,ast.ImportFrom) and n.module=='typing' and any(a.name not in SAFE_TYPING for a in n.names):
                return 'unapproved_typing_helper'
        if isinstance(n,ast.Name) and (n.id in REFLECTION or n.id.startswith('__')):
            return 'reflection_name'
        if isinstance(n,ast.Attribute) and (n.attr in REFLECTION or n.attr.startswith('__')):
            return 'reflection_attribute'
        if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id in typing_aliases and n.attr not in SAFE_TYPING:
            return 'unapproved_typing_helper'
    return None


def offsets(text):
    # Source transformations are ASCII/LF-only. A multiline literal is copied
    # intact; its internal whitespace is never rebuilt by indentation handling.
    result=[0]
    for i,ch in enumerate(text):
        if ch=='\n':result.append(i+1)
    return result


def span(node,starts,text):
    # AST columns are UTF-8 byte offsets even though tokenize columns are code
    # points. unparse can temporarily emit Unicode from an ASCII escape.
    def at(line,column):
        start=starts[line-1]
        end=starts[line] if line<len(starts) else len(text)
        return start+len(text[start:end].encode()[:column].decode())
    return at(node.lineno,node.col_offset),at(node.end_lineno,node.end_col_offset)


def literal_nodes(tree):
    found=[]
    def visit(node):
        if isinstance(node,(ast.Constant,)+FORMATTED):
            found.append(node)
            return
        for child in ast.iter_child_nodes(node):visit(child)
    visit(tree)
    return found


def literal_profile(text,tree=None):
    tree=parse(text) if tree is None else tree
    starts=offsets(text)
    return [(type(n).__name__,text[slice(*span(n,starts,text))]) for n in literal_nodes(tree)]


def validate(original,candidate):
    if original==candidate:
        parse(original)
        return True
    if not set(candidate)<=ALPHABET:raise ValueError('candidate outside literal alphabet')
    before,after=parse(original),parse(candidate)
    if fingerprint(before)!=fingerprint(after):raise ValueError('AST identity changed')
    if literal_profile(original,before)!=literal_profile(candidate,after):
        raise ValueError('literal or formatted-string spelling changed')
    return True


def preserved_unparse(text,tree):
    raw=ast.unparse(tree)+'\n'
    target=parse(raw)
    # Pair nodes before restoring spelling. If unparse changes the AST at all,
    # this renderer is rejected; later token-only variants can still survive.
    if fingerprint(tree)!=fingerprint(target):raise ValueError('unparse AST mismatch')
    old,new=literal_nodes(tree),literal_nodes(target)
    if len(old)!=len(new):raise ValueError('unparse literal count mismatch')
    old_starts,new_starts=offsets(text),offsets(raw)
    replacements=[]
    for a,b in zip(old,new):
        if fingerprint(a)!=fingerprint(b):raise ValueError('unparse literal mismatch')
        value=text[slice(*span(a,old_starts,text))]
        # A formerly parenthesized multiline concatenation may lose its outer
        # grouping in unparse. Parentheses preserve the exact interior spelling.
        if isinstance(a,ast.Constant) and '\n' in value:value='('+value+')'
        replacements.append((*span(b,new_starts,raw),value))
    for start,end,value in sorted(replacements,reverse=True):raw=raw[:start]+value+raw[end:]
    validate(text,raw)
    return raw


IGNORED={tokenize.ENCODING,tokenize.ENDMARKER,tokenize.NEWLINE,tokenize.NL,
         tokenize.INDENT,tokenize.DEDENT,tokenize.COMMENT}


@functools.lru_cache(maxsize=4096)
def lexical_signature(fragment):
    result=[]
    try:
        for t in tokenize.generate_tokens(io.StringIO(fragment).readline):
            if t.type not in IGNORED:result.append((t.type,t.string))
    except (tokenize.TokenError,IndentationError,SyntaxError):
        # Unmatched operators are ordinary fragments. Already emitted tokens
        # still distinguish merged names/numbers/operators; final AST validates.
        pass
    return tuple(result)


def needs_space(left,right):
    a,b=lexical_signature(left),lexical_signature(right)
    # Python can preserve separate NUMBER/NAME tokens while warning about
    # spellings such as `0for` or `1and`. Do not introduce those warnings.
    if a and b and a[-1][0]==tokenize.NUMBER and b[0][0]==tokenize.NAME:return True
    return lexical_signature(left+right)!=lexical_signature(left+' '+right)


def compact(text,indent_width):
    if indent_width not in (1,2):raise ValueError('undeclared indentation width')
    tree=parse(text);starts=offsets(text)
    protected={span(n,starts,text)[0]:(span(n,starts,text)[1],text[slice(*span(n,starts,text))]) for n in literal_nodes(tree)}
    tokens=list(tokenize.generate_tokens(io.StringIO(text).readline))
    if len(tokens)>MAX_TOKENS:raise ValueError('token limit')
    pieces=[];depth=0;line_start=True;previous=None;skip_until=-1
    for token in tokens:
        at=starts[token.start[0]-1]+token.start[1] if token.start[0]<=len(starts) else len(text)
        if at<skip_until:continue
        if token.type==tokenize.INDENT:depth+=1;continue
        if token.type==tokenize.DEDENT:depth-=1;continue
        if token.type==tokenize.NEWLINE:
            pieces.append('\n');line_start=True;previous=None;continue
        if token.type in (tokenize.NL,tokenize.COMMENT,tokenize.ENCODING,tokenize.ENDMARKER):continue
        if token.type==tokenize.ERRORTOKEN and token.string.isspace():continue
        value=token.string
        if at in protected:
            skip_until,value=protected[at]
        if not value:continue
        if line_start:
            pieces.append(' '*(depth*indent_width));line_start=False
        elif previous is not None and needs_space(previous,value):pieces.append(' ')
        pieces.append(value);previous=value
    if depth!=0:raise ValueError('unbalanced indentation')
    result=''.join(pieces).rstrip('\n')+'\n'
    validate(text,result)
    return result


def menu(text):
    """At most six deterministic alternatives; original retained on every skip."""
    tree=parse(text)
    reason=unsafe_reason(text,tree)
    result={'candidates':{'original':text},'unsupported':reason,'rejected':{},'_private_rejections':{}}
    if reason:return result
    proposed={}
    try:proposed['unparse']=preserved_unparse(text,tree)
    except (ValueError,SyntaxError,RecursionError,tokenize.TokenError) as error:
        result['rejected']['unparse']=type(error).__name__
        result['_private_rejections']['unparse']=str(error)
    bases=[('original',text)]+([('unparse',proposed['unparse'])] if 'unparse' in proposed else [])
    for label,base in bases:
        for width in (1,2):
            name=f'compact_{label}_indent{width}'
            try:proposed[name]=compact(base,width)
            except (ValueError,SyntaxError,IndentationError,RecursionError,tokenize.TokenError) as error:
                result['rejected'][name]=type(error).__name__
                result['_private_rejections'][name]=str(error)
    seen={text}
    for name,value in proposed.items():
        validate(text,value)
        if value not in seen:result['candidates'][name]=value;seen.add(value)
    if len(result['candidates'])>6:raise AssertionError('renderer menu exceeds frozen bound')
    return result


def public_summary(result):
    """Only fixed labels, reason enums, counts and source hashes may be exported."""
    return {'unsupported_reason':result['unsupported'],'candidate_count':len(result['candidates']),
            'rejected_variant_count':len(result['rejected']),
            'rejection_types':dict(result['rejected']),
            'candidate_sha256':{name:hashlib.sha256(text.encode()).hexdigest()
                                for name,text in result['candidates'].items()}}
